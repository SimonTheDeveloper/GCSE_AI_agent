from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

from json import JSONDecodeError

import time
import boto3  # type: ignore

from gcse_help_template import create_gcse_help_base_structure
from gcse_help_prompts import (
    get_system_prompt,
    get_user_prompt_template,
    render_user_prompt,
    seed_ingestion_prompt_if_missing,
)



logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_exercise_text(text: str) -> str:
    """Normalize text for hashing + caching.

    Keep it conservative: normalize whitespace, strip, standardize unicode minus.
    """
    t = (text or "").replace("−", "-")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def exercise_hash(normalized_text: str, *, schema_version: str, prompt_version: int) -> str:
    payload = f"{schema_version}||{prompt_version}||{normalized_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class GCSEHelpError(RuntimeError):
    pass


@dataclass(frozen=True)
class GCSEHelpGeneratorConfig:
    model: str = "gpt-4.1-mini"
    schema_version: str = "1.0.0"
    cache_backend: str = "dynamodb"  # dynamodb | json
    cache_path: Path = Path("./gcse_cache.json")
    cache_ttl_seconds: int | None = None
    dynamodb_table_name: str = os.environ.get("DYNAMODB_TABLE_NAME", "gcse_app")
    dynamodb_region: str = os.environ.get("AWS_REGION") or "eu-west-1"
    dynamodb_endpoint_url: str | None = os.environ.get("DYNAMODB_ENDPOINT_URL")


_CACHE_PK = "CACHE#GCSE_HELP"
_CACHE_SK_PREFIX = "EX#"


class GCSEHelpGenerator:
    """Generate structured GCSE help JSON (nudge/hint/steps/worked/teachback).

    - Uses optional on-disk cache keyed by normalized exercise text.
    - Uses OpenAI SDK if `OPENAI_API_KEY` is set.

    This intentionally returns plain dicts suitable for JSON responses.
    """

    def __init__(self, config: GCSEHelpGeneratorConfig | None = None):
        self._config = config or GCSEHelpGeneratorConfig(
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            schema_version=os.environ.get("GCSE_HELP_SCHEMA_VERSION", "1.0.0"),
            cache_backend=os.environ.get("GCSE_HELP_CACHE_BACKEND", "dynamodb"),
            cache_path=Path(os.environ.get("GCSE_HELP_CACHE_PATH", "./gcse_cache.json")),
            cache_ttl_seconds=(
                int(os.environ["GCSE_HELP_CACHE_TTL_SECONDS"]) if os.environ.get("GCSE_HELP_CACHE_TTL_SECONDS") else None
            ),
            dynamodb_table_name=os.environ.get("DYNAMODB_TABLE_NAME", "gcse_app"),
            dynamodb_region=os.environ.get("AWS_REGION") or "eu-west-1",
            dynamodb_endpoint_url=os.environ.get("DYNAMODB_ENDPOINT_URL"),
        )

        # Only used for JSON fallback cache.
        self._cache: Dict[str, Any] = {}
        if self._config.cache_backend == "json":
            self._cache = self._load_cache(self._config.cache_path)

        self._dynamo_table = None
        if self._config.cache_backend == "dynamodb":
            self._dynamo_table = self._safe_get_dynamodb_table()

        # In-memory prompt cache: (version, system_prompt, user_prompt_template)
        self._prompt_cache: tuple[int, str, str] | None = None
        self._load_prompts()

        logger.info(
            "gcse_help_generator.init cache_backend=%s model=%s schema_version=%s dynamo_table=%s dynamo_ready=%s",
            self._config.cache_backend,
            self._config.model,
            self._config.schema_version,
            self._config.dynamodb_table_name,
            bool(self._dynamo_table) if self._config.cache_backend == "dynamodb" else False,
        )

    @property
    def config(self) -> GCSEHelpGeneratorConfig:
        return self._config

    def _load_prompts(self) -> None:
        """Load the active ingestion prompt from DynamoDB into memory.

        Falls back to the module-level constants if DB is unavailable or not seeded.
        Also seeds the prompt into DB on first run.
        """
        try:
            seeded = seed_ingestion_prompt_if_missing()
            if seeded:
                logger.info("gcse_help_generator.prompt_seeded")
        except Exception:
            logger.exception("gcse_help_generator.prompt_seed_failed — using module defaults")

        try:
            import db as _db
            active = _db.get_prompt_active("ingestion")
            if active:
                version = int(active["version"])
                record = _db.get_prompt_version("ingestion", version)
                if record:
                    self._prompt_cache = (
                        version,
                        record["systemPrompt"],
                        record["userPromptTemplate"],
                    )
                    logger.info("gcse_help_generator.prompt_loaded version=%d", version)
                    return
        except Exception:
            logger.exception("gcse_help_generator.prompt_load_failed — using module defaults")

        # Fallback to module constants (version 0 = not from DB)
        self._prompt_cache = (0, get_system_prompt(), get_user_prompt_template())
        logger.warning("gcse_help_generator.prompt_using_fallback")

    def reload_prompt(self) -> int:
        """Invalidate the in-memory prompt cache and reload from DB. Returns new version."""
        self._prompt_cache = None
        self._load_prompts()
        return self._prompt_cache[0] if self._prompt_cache else 0

    def _get_prompts(self) -> tuple[int, str, str]:
        """Return (version, system_prompt, user_prompt_template)."""
        if self._prompt_cache is None:
            self._load_prompts()
        return self._prompt_cache  # type: ignore[return-value]

    def _safe_get_dynamodb_table(self):
        try:
          
            dynamodb = boto3.resource(
                "dynamodb",
                region_name=self._config.dynamodb_region,
                endpoint_url=self._config.dynamodb_endpoint_url,
            )
            return dynamodb.Table(self._config.dynamodb_table_name)
        except Exception:
            logger.exception(
                "gcse_help_generator.dynamo_unavailable table=%s region=%s endpoint_url=%s",
                self._config.dynamodb_table_name,
                self._config.dynamodb_region,
                self._config.dynamodb_endpoint_url,
            )
            return None

    def _load_cache(self, path: Path) -> Dict[str, Any]:
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    logger.info("gcse_help_generator.json_cache_loaded path=%s entries=%s", str(path), len(data))
                    return data
                logger.warning("gcse_help_generator.json_cache_invalid path=%s", str(path))
                return {}
        except Exception:
            logger.exception("gcse_help_generator.json_cache_load_failed path=%s", str(path))
            return {}
        return {}

    def _save_cache(self) -> None:
        try:
            self._config.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._config.cache_path.write_text(
                json.dumps(self._cache, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info(
                "gcse_help_generator.json_cache_saved path=%s entries=%s",
                str(self._config.cache_path),
                len(self._cache),
            )
        except Exception:
            # Cache is an optimization; generation should still succeed.
            logger.exception("gcse_help_generator.json_cache_save_failed path=%s", str(self._config.cache_path))
            pass

    def _dynamo_key(self, cache_key: str) -> Dict[str, str]:
        return {"PK": _CACHE_PK, "SK": f"{_CACHE_SK_PREFIX}{cache_key}"}

    def _dynamo_get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if not self._dynamo_table:
            return None
        try:
            resp = self._dynamo_table.get_item(Key=self._dynamo_key(cache_key))
            item = resp.get("Item")
            if not item:
                return None

            expires_at = item.get("expiresAt")
            if expires_at is not None:
                try:
                    if int(expires_at) <= int(time.time()):
                        return None
                except Exception:
                    # If TTL is malformed, ignore TTL.
                    pass

            result = item.get("result")
            return result if isinstance(result, dict) else None
        except Exception:
            logger.exception("gcse_help_generator.dynamo_get_failed")
            return None

    def _dynamo_put(self, cache_key: str, *, normalized_text: str, result: Dict[str, Any]) -> None:
        if not self._dynamo_table:
            return
        try:
            # Convert all floats to Decimals for DynamoDB compatibility
            result_for_dynamo = convert_floats_to_decimal(result)
            
            item: Dict[str, Any] = {
                **self._dynamo_key(cache_key),
                "Type": "CacheEntry",
                "cacheKey": cache_key,
                "schemaVersion": self._config.schema_version,
                "normalizedText": normalized_text,
                "createdAt": _now_iso(),
                "result": result_for_dynamo,
            }
            if self._config.cache_ttl_seconds:
                item["expiresAt"] = int(time.time()) + int(self._config.cache_ttl_seconds)

            self._dynamo_table.put_item(Item=item)
            logger.info(
                "gcse_help_generator.dynamo_put_ok ttl_seconds=%s",
                self._config.cache_ttl_seconds,
            )
        except Exception:
            # Cache is an optimization; generation should still succeed.
            logger.exception("gcse_help_generator.dynamo_put_failed")
            return

    def _safe_import_openai(self):
        try:
            import openai  # type: ignore

            return openai  # type: ignore[return-value]
        except Exception:
            return None

    def _light_validate_response(self, obj: dict, schema_version: str = "1.0.0") -> None:
        if schema_version == "2.0.0":
            self._validate_v2_response(obj)
        else:
            self._validate_v1_response(obj)

    def _validate_v1_response(self, obj: dict) -> None:
        required_top = ["schema_version", "request", "exercise", "analysis", "help"]
        for k in required_top:
            if k not in obj:
                raise GCSEHelpError(f"Missing top-level field: {k}")

        tiers = obj.get("help", {}).get("tiers", {})
        for tier in ["nudge", "hint", "steps", "worked", "teachback"]:
            if tier not in tiers:
                raise GCSEHelpError(f"Missing help.tiers.{tier}")
            content = (tiers[tier] or {}).get("content", [])
            if not isinstance(content, list) or len(content) == 0:
                raise GCSEHelpError(f"help.tiers.{tier}.content must be a non-empty list")

        nt = obj.get("exercise", {}).get("prompt", {}).get("normalized_text")
        if not nt or not isinstance(nt, str):
            raise GCSEHelpError("exercise.prompt.normalized_text missing or invalid")

    def _validate_v2_response(self, obj: dict) -> None:
        for field in ["normalised_form", "steps", "full_solution", "explain_it_back"]:
            if field not in obj:
                raise GCSEHelpError(f"v2 response missing field: {field}")

        steps = obj.get("steps", [])
        if not isinstance(steps, list) or len(steps) == 0:
            raise GCSEHelpError("v2 steps must be a non-empty list")

        for step in steps:
            n = step.get("step_number", "?")
            for f in ["step_number", "nudge", "hint", "worked_step", "expected_answer", "common_errors"]:
                if f not in step:
                    raise GCSEHelpError(f"v2 step {n} missing field: {f}")
            errors = step.get("common_errors", [])
            if not isinstance(errors, list) or len(errors) < 2:
                raise GCSEHelpError(f"v2 step {n} must have at least 2 common_errors")
            for err in errors:
                for ef in ["category", "pattern", "wrong_answer_example", "redirect_question"]:
                    if ef not in err:
                        raise GCSEHelpError(f"v2 step {n} common_error missing field: {ef}")
                valid_categories = {"conceptual", "procedural", "arithmetic", "format"}
                if err.get("category") not in valid_categories:
                    raise GCSEHelpError(f"v2 step {n} common_error has invalid category: {err.get('category')}")

        eib = obj.get("explain_it_back", {})
        for f in ["question", "sentence_starters", "rubric"]:
            if f not in eib:
                raise GCSEHelpError(f"v2 explain_it_back missing field: {f}")
        if not isinstance(eib.get("rubric", []), list) or len(eib.get("rubric", [])) == 0:
            raise GCSEHelpError("v2 explain_it_back.rubric must be a non-empty list")

    def _extract_first_json_object(self, s: str) -> str:
        """Extract the first complete JSON object from a string.

        Useful when LLM output includes fences/prose around the JSON.
        """
        start = s.find("{")
        if start == -1:
            raise GCSEHelpError("Model output did not contain a JSON object")

        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(s)):
            ch = s[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue

            if ch == '"':
                in_str = True
                continue

            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start : i + 1]

        raise GCSEHelpError("Model output contained incomplete JSON")

    def generate(
        self,
        *,
        raw_text: str,
        uid: Optional[str] = None,
        origin_type: str = "student_homework",
        origin_label: str = "Student homework",
        year_group: Optional[int] = 9,
        tier: str = "unknown",
        desired_help_level: str = "auto",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        normalized_text = normalize_exercise_text(raw_text)
        if not normalized_text:
            raise GCSEHelpError("No exercise text provided")

        prompt_version, system, user_template = self._get_prompts()
        # v2 prompt (version >= 2) produces a different output shape — use a separate cache namespace
        effective_schema_version = "2.0.0" if prompt_version >= 2 else self._config.schema_version
        key = exercise_hash(
            normalized_text,
            schema_version=effective_schema_version,
            prompt_version=prompt_version,
        )
        text_len = len(normalized_text)
        key_short = key[:12]
        logger.info(
            "gcse_help_generator.generate_start cache=%s backend=%s key=%s text_len=%s year_group=%s tier=%s desired=%s",
            bool(use_cache),
            self._config.cache_backend,
            key_short,
            text_len,
            year_group,
            tier,
            desired_help_level,
        )
        if use_cache:
            if self._config.cache_backend == "dynamodb":
                cache_start = time.perf_counter()
                cached = self._dynamo_get(key)
                if cached is not None:
                    logger.info(
                        "gcse_help_generator.cache_hit backend=dynamodb key=%s ms=%d",
                        key_short,
                        int((time.perf_counter() - cache_start) * 1000),
                    )
                    return cached
                logger.info(
                    "gcse_help_generator.cache_miss backend=dynamodb key=%s ms=%d",
                    key_short,
                    int((time.perf_counter() - cache_start) * 1000),
                )
            elif self._config.cache_backend == "json":
                if key in self._cache:
                    cached = self._cache[key]
                    if isinstance(cached, dict):
                        logger.info("gcse_help_generator.cache_hit backend=json key=%s", key_short)
                        return cached
                logger.info("gcse_help_generator.cache_miss backend=json key=%s", key_short)

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise GCSEHelpError("OPENAI_API_KEY is not set")

        openai = self._safe_import_openai()
        if openai is None:
            raise GCSEHelpError("OpenAI SDK not installed in backend environment")

        if prompt_version >= 2:
            # v2: send plain problem text — the system prompt carries all schema context
            prompt = render_user_prompt(user_template, normalized_text)
        else:
            base_structure = create_gcse_help_base_structure(
                normalized_text=normalized_text,
                raw_text=raw_text,
                schema_version=self._config.schema_version,
                uid=uid,
                year_group=year_group,
                tier=tier,
                desired_help_level=desired_help_level,
                origin_type=origin_type,
                origin_label=origin_label,
            )
            prompt = render_user_prompt(user_template, json.dumps(base_structure, ensure_ascii=False))

        # v2 responses are richer (~2k–4k tokens); v1 fits in 2500
        max_tokens = 4000 if prompt_version >= 2 else 2500

        # Support both new (OpenAI()) and legacy SDKs.
        text: str
        llm_start = time.perf_counter()
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=api_key)  # type: ignore[attr-defined]
            try:
                resp = client.chat.completions.create(
                    model=self._config.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    # Ask the API to enforce JSON output.
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    # Avoid truncation that can produce incomplete JSON.
                    max_tokens=max_tokens,
                )
                text = (resp.choices[0].message.content or "").strip()
            except Exception:
                logger.exception(
                    "gcse_help_generator.llm_call_failed sdk=new key=%s model=%s",
                    key_short,
                    self._config.model,
                )
                raise
        else:
            openai.api_key = api_key  # type: ignore[attr-defined]
            try:
                resp = openai.ChatCompletion.create(  # type: ignore[attr-defined]
                    model=self._config.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                text = (resp["choices"][0]["message"]["content"] or "").strip()
            except Exception:
                logger.exception(
                    "gcse_help_generator.llm_call_failed sdk=legacy key=%s model=%s",
                    key_short,
                    self._config.model,
                )
                raise

        logger.info(
            "gcse_help_generator.llm_call_ok key=%s model=%s chars=%s ms=%d",
            key_short,
            self._config.model,
            len(text),
            int((time.perf_counter() - llm_start) * 1000),
        )

        try:
            obj: Dict[str, Any] = json.loads(text)
        except JSONDecodeError:
            logger.warning("gcse_help_generator.json_parse_failed key=%s attempting_repair=true", key_short)
            # One repair attempt (strict: must return JSON, but we defensively
            # extract the first JSON object if wrapped in code fences/text).
            repaired_text: str
            if hasattr(openai, "OpenAI"):
                client = openai.OpenAI(api_key=api_key)  # type: ignore[attr-defined]
                repair = client.chat.completions.create(
                    model=self._config.model,
                    messages=[
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": "Fix and return ONLY valid JSON for the following (no commentary, no markdown):\n" + text,
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0,
                    max_tokens=2500,
                )
                repaired_text = (repair.choices[0].message.content or "").strip()
            else:
                repair = openai.ChatCompletion.create(  # type: ignore[attr-defined]
                    model=self._config.model,
                    messages=[
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": "Fix and return ONLY valid JSON for the following (no commentary, no markdown):\n" + text,
                        },
                    ],
                    temperature=0,
                    max_tokens=2500,
                )
                repaired_text = (repair["choices"][0]["message"]["content"] or "").strip()

            try:
                obj = json.loads(repaired_text)
            except JSONDecodeError:
                extracted = self._extract_first_json_object(repaired_text)
                obj = json.loads(extracted)

        logger.info(
            "gcse_help_generator.json_parse_ok key=%s ms=%d",
            key_short,
            int((time.perf_counter() - llm_start) * 1000),
        )

        try:
            self._light_validate_response(obj, schema_version=effective_schema_version)
        except Exception:
            logger.exception("gcse_help_generator.validation_failed key=%s", key_short)
            raise

        if use_cache:
            if self._config.cache_backend == "dynamodb":
                self._dynamo_put(key, normalized_text=normalized_text, result=obj)
            elif self._config.cache_backend == "json":
                self._cache[key] = obj
                self._save_cache()
        logger.info(
            "gcse_help_generator.generate_ok key=%s schema=%s total_ms=%d",
            key_short,
            effective_schema_version,
            int((time.perf_counter() - start) * 1000),
        )
        # Attach schema version so callers can dispatch without inspecting the shape
        obj["_schema_version"] = effective_schema_version
        return obj

def convert_floats_to_decimal(obj: Any) -> Any:
    """Recursively convert all float values to Decimal for DynamoDB compatibility."""
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj
