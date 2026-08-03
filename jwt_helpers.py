import requests
from urllib.parse import urlparse


_discovery_cache = {}
_jwks_cache = {}


def _assert_same_origin(url: str, issuer: str, label: str) -> None:
    """Prevent SSRF: ensure the fetched URL belongs to the expected issuer origin."""
    issuer_host = urlparse(issuer.rstrip("/")).netloc
    url_host = urlparse(url).netloc
    if not url_host or url_host != issuer_host:
        raise ValueError(
            f"{label} host '{url_host}' does not match issuer host '{issuer_host}'"
        )


def get_openid_configuration(issuer: str) -> dict:
    issuer = issuer.rstrip("/")
    url = f"{issuer}/.well-known/openid-configuration"

    if url not in _discovery_cache:
        response = requests.get(url, timeout=10, allow_redirects=False)
        response.raise_for_status()
        _discovery_cache[url] = response.json()

    return _discovery_cache[url]


def get_signing_key_from_jwks(jwks_uri: str, kid: str, issuer: str):
    # Import lazily so missing crypto extras do not crash app startup.
    try:
        from jwt.algorithms import RSAAlgorithm
    except ImportError as exc:
        raise RuntimeError(
            "PyJWT crypto backend is missing. Install with: pip install 'PyJWT[crypto]'"
        ) from exc

    # Ensure jwks_uri stays on the issuer's own origin (SSRF prevention)
    _assert_same_origin(jwks_uri, issuer, "jwks_uri")

    if jwks_uri not in _jwks_cache:
        response = requests.get(jwks_uri, timeout=10, allow_redirects=False)
        response.raise_for_status()
        _jwks_cache[jwks_uri] = response.json()

    jwks = _jwks_cache[jwks_uri]

    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return RSAAlgorithm.from_jwk(jwk)

    raise ValueError(f"No matching JWK found for kid={kid}")
