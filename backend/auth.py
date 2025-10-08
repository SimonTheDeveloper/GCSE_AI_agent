import os
import time
from functools import lru_cache
from typing import Any, Dict, Optional
from types import SimpleNamespace

from fastapi import HTTPException, Request

import requests
from jose import jwk, jwt


class CognitoVerifier:
    def __init__(self, region: str, user_pool_id: str, audience: Optional[str] = None):
        self.region = region
        self.user_pool_id = user_pool_id
        self.audience = audience
        self.issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

    @lru_cache(maxsize=1)
    def _get_jwks(self) -> Dict[str, Any]:
        url = f"{self.issuer}/.well-known/jwks.json"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def verify(self, token: str) -> Dict[str, Any]:
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        alg = headers.get("alg", "RS256")
        if not kid:
            raise ValueError("Missing key id (kid)")

        jwks = self._get_jwks()
        key_dict = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_dict:
            # Keys may have rotated; clear cache and retry once
            self._get_jwks.cache_clear()  # type: ignore[attr-defined]
            jwks = self._get_jwks()
            key_dict = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            if not key_dict:
                raise ValueError("Public key not found for token")

        # Build a key usable by python-jose
        public_key = jwk.construct(key_dict)
        try:
            # Prefer decoding with PEM if supported by backend
            pem = public_key.to_pem().decode("utf-8")
            claims = jwt.decode(
                token,
                pem,
                algorithms=[alg],
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_aud": bool(self.audience)},
            )
        except AttributeError:
            # Fallback: let jose handle JWK dict directly
            claims = jwt.decode(
                token,
                key_dict,
                algorithms=[alg],
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_aud": bool(self.audience)},
            )

        # Extra token_use sanity check (accept both id and access tokens)
        tuse = claims.get("token_use")
        if tuse not in ("id", "access"):
            raise ValueError("Unsupported token type")
        return claims


def get_default_verifier() -> Optional[CognitoVerifier]:
    region = os.getenv("AWS_REGION")
    pool = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_APP_CLIENT_ID")
    if region and pool and client_id:
        return CognitoVerifier(region, pool, client_id)
    return None

# Optional access control (duplicate of main.py logic so this dependency can be used directly)
_ALLOWED_EMAILS = {x.strip().lower() for x in os.getenv("ALLOWED_EMAILS", "").split(",") if x.strip()}
_ALLOWED_DOMAINS = {x.strip().lower().lstrip("@") for x in os.getenv("ALLOWED_DOMAINS", "").split(",") if x.strip()}
_REQUIRED_GROUP = os.getenv("REQUIRED_GROUP", "").strip()

def _user_is_allowed(claims: Dict[str, Any]) -> bool:
    if _REQUIRED_GROUP:
        groups = claims.get("cognito:groups") or []
        if isinstance(groups, str):
            groups = [groups]
        if _REQUIRED_GROUP not in groups:
            return False
    if _ALLOWED_EMAILS:
        email = (claims.get("email") or "").lower().strip()
        username = (claims.get("username") or claims.get("cognito:username") or "").lower().strip()
        if email and email in _ALLOWED_EMAILS:
            return True
        if username and username in _ALLOWED_EMAILS:
            return True
        return False
    if _ALLOWED_DOMAINS:
        email = (claims.get("email") or "").lower().strip()
        if not email or "@" not in email:
            return False
        domain = email.split("@", 1)[1]
        return domain in _ALLOWED_DOMAINS
    return True

def get_current_principal(request: Request):
    verifier = get_default_verifier()
    if not verifier:
        raise HTTPException(status_code=503, detail="Cognito not configured")
    auth = request.headers.get("Authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        claims = verifier.verify(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    if not _user_is_allowed(claims):
        raise HTTPException(status_code=403, detail="User not allowed. Please contact the administrator.")
    sub = claims.get("sub") or claims.get("username") or claims.get("cognito:username")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token: missing subject")
    return SimpleNamespace(sub=sub, claims=claims)
