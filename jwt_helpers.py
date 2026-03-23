import requests
from jwt.algorithms import RSAAlgorithm


_discovery_cache = {}
_jwks_cache = {}


def get_openid_configuration(issuer: str) -> dict:
    issuer = issuer.rstrip("/")
    url = f"{issuer}/.well-known/openid-configuration"

    if url not in _discovery_cache:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        _discovery_cache[url] = response.json()

    return _discovery_cache[url]


def get_signing_key_from_jwks(jwks_uri: str, kid: str):
    if jwks_uri not in _jwks_cache:
        response = requests.get(jwks_uri, timeout=10)
        response.raise_for_status()
        _jwks_cache[jwks_uri] = response.json()

    jwks = _jwks_cache[jwks_uri]

    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return RSAAlgorithm.from_jwk(jwk)

    raise ValueError(f"No matching JWK found for kid={kid}")
