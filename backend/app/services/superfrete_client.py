"""Client HTTP isolado da SuperFrete. Nenhum router chama httpx diretamente.

Endpoints públicos oficiais (confirmados na doc):
- POST /api/v0/calculator      -> cotação
- GET  /api/v0/user            -> valida token (teste de conexão)
- GET  /api/v0/order/info/{id} -> status/rastreio do pedido
- GET  /api/v1/shipping-labels/{id} -> dados/impressão da etiqueta
Operações de compra/cancelamento NÃO têm contrato público completo -> fluxo híbrido (painel).
"""
import httpx

BASE_URLS = {
    "sandbox": "https://sandbox.superfrete.com",
    "production": "https://api.superfrete.com",
}
PANEL_URLS = {
    "sandbox": "https://sandbox.superfrete.com/#/orders",
    "production": "https://web.superfrete.com/#/orders",
}
DEFAULT_USER_AGENT = "Brasil Minis/1.0 (contato@brasilminis.com.br)"
TIMEOUT = httpx.Timeout(10.0, connect=3.0)


class SuperfreteUnavailable(Exception):
    pass


class SuperfreteError(Exception):
    def __init__(self, status: int, body: str, retry_after: int | None = None):
        self.status = status
        self.body = (body or "")[:500]
        self.retry_after = retry_after
        super().__init__(f"SuperFrete {status}")


class SuperfreteAuthError(SuperfreteError):
    """Erro de autenticação (401/403): token inválido/expirado."""
    def __init__(self, status: int = 401, body: str = "Token inválido ou expirado."):
        super().__init__(status, body)


def base_url(environment: str) -> str:
    return BASE_URLS.get(environment or "sandbox", BASE_URLS["sandbox"])


def panel_url(environment: str) -> str:
    return PANEL_URLS.get(environment or "sandbox", PANEL_URLS["sandbox"])


def _headers(token: str, user_agent: str | None) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": user_agent or DEFAULT_USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def request(environment: str, token: str, method: str, path: str, user_agent: str | None = None, **kwargs):
    if not token:
        raise SuperfreteUnavailable("Token SuperFrete não configurado.")
    url = base_url(environment).rstrip("/") + path
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.request(method, url, headers=_headers(token, user_agent), **kwargs)
    except httpx.TimeoutException:
        raise SuperfreteUnavailable("Tempo esgotado ao contatar a SuperFrete.")
    except httpx.HTTPError:
        raise SuperfreteUnavailable("SuperFrete indisponível.")
    if r.status_code in (401, 403):
        raise SuperfreteAuthError(r.status_code, "Token inválido ou expirado.")
    if r.status_code == 429:
        ra = r.headers.get("Retry-After")
        try:
            ra_int = int(ra) if ra is not None else None
        except (TypeError, ValueError):
            ra_int = None
        raise SuperfreteError(429, "Limite de requisições atingido.", retry_after=ra_int)
    if r.status_code >= 400:
        raise SuperfreteError(r.status_code, r.text)
    try:
        return r.json()
    except Exception:
        return {}
