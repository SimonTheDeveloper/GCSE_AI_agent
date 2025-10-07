import os
import time
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from jose import jwk, jwt
from jose.utils import base64url_decode


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
        alg = headers.get("alg")
        if not kid or not alg:
            raise ValueError("Invalid token header")

        jwks = self._get_jwks()
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            # Clear cache and retry once in case keys rotated
            self._get_jwks.cache_clear()  # type: ignore[attr-defined]
            jwks = self._get_jwks()
            key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            if not key:
                raise ValueError("Public key not found for token")

        public_key = jwk.construct(key)
        message, encoded_sig = str(jwt.get_unverified_claims(token)).encode("utf-8"), jwt.get_unverified_signature(token)
        decoded_sig = base64url_decode(encoded_sig.encode("utf-8"))
        if not public_key.verify(message, decoded_sig):
            raise ValueError("Signature verification failed")

        claims = jwt.get_unverified_claims(token)
        # Validate iss, exp, aud
        if claims.get("iss") != self.issuer:
            raise ValueError("Invalid issuer")
        if time.time() > float(claims.get("exp", 0)):
            raise ValueError("Token expired")
        if self.audience and claims.get("client_id") != self.audience and claims.get("aud") != self.audience:
            raise ValueError("Invalid audience")
        return claims


def get_default_verifier() -> Optional[CognitoVerifier]:
    region = os.getenv("AWS_REGION")
    pool = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_APP_CLIENT_ID")
    if region and pool and client_id:
        return CognitoVerifier(region, pool, client_id)
    return None
