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


def exercise_hash(normalized_text: str, *, schema_version: str) -> str:
    payload = f"{schema_version}||{normalized_text}".encode("utf-8")
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

    def _safe_get_dynamodb_table(self):
        try:
            import boto3  # type: ignore

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

    def _light_validate_response(self, obj: dict) -> None:
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

        key = exercise_hash(normalized_text, schema_version=self._config.schema_version)
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

        request_id = f"req_{hashlib.sha1((normalized_text + _now_iso()).encode()).hexdigest()[:12]}"
        exercise_id = f"ex_{hashlib.sha1(normalized_text.encode()).hexdigest()[:12]}"

        base_obj: Dict[str, Any] = {
            "schema_version": self._config.schema_version,
            "request": {
                "id": request_id,
                "created_at": _now_iso(),
                "locale": "en-GB",
                "student_context": {
                    "uid": uid,
                    "year_group": year_group,
                    "tier": tier,
                    "desired_help_level": desired_help_level,
                    "what_ive_tried": "",
                },
                "input": {"modality": "typed_text", "typed_text": {"text": normalized_text}},
            },
            "exercise": {
                "exercise_id": exercise_id,
                "origin": {"type": origin_type, "label": origin_label, "created_at": _now_iso()},
                "prompt": {
                    "normalized_text": normalized_text,
                    "raw_text": raw_text,
                    "attachments": [],
                },
                "extraction": {"status": "ok", "confidence": 1, "ambiguities": []},
            },
            "analysis": {
                "subject": "maths",
                "topics": [],
                "difficulty": {"gcse_tier_hint": "unknown", "confidence": 0.5},
                "prerequisites": [],
                "common_mistakes": [],
            },
            "help": {
                "recommended_start": "nudge",
                "tiers": {
                    "nudge": {"title": "", "content": [{"type": "plain", "text": ""}]},
                    "hint": {"title": "", "content": [{"type": "plain", "text": ""}]},
                    "steps": {"title": "", "content": [{"type": "plain", "text": "", "expectedAnswer": ""}]},
                    "worked": {"title": "", "content": [{"type": "plain", "text": ""}]},
                    "teachback": {"title": "", "content": [{"type": "plain", "text": ""}]},
                },
                "formulas_used": [],
                "check_your_answer": {"instruction": "", "worked_check": ""},
                "practice": [],
            },
        }

        system = (
            "You are a GCSE tutor assistant. Return ONLY valid JSON that conforms to the requested structure. "
            "Use UK tone (en-GB) and age-appropriate wording for Year 9 unless otherwise specified. "
            "Do not include markdown fences. Do not include commentary."
        )
        prompt = (
            "Fill in and complete the JSON object below. Keep the same keys. Replace placeholder empty strings/arrays with real content. "
            "Populate analysis.topics, analysis.prerequisites, analysis.common_mistakes appropriately. "
            "Populate help.tiers with progressive help: nudge (1-2 lines), hint (bullets), steps (numbered bullets), worked (math lines), teachback (why it works). "
            "Use help.formulas_used only if relevant. Include a check_your_answer with substitution check. Add 2-3 practice questions with final answers only. "
            "Return strictly valid JSON.\n\n"
            + json.dumps(base_obj, ensure_ascii=False)
        )

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
                    max_tokens=2500,
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
                    max_tokens=2500,
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
            self._light_validate_response(obj)
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
            "gcse_help_generator.generate_ok key=%s total_ms=%d",
            key_short,
            int((time.perf_counter() - start) * 1000),
        )
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
