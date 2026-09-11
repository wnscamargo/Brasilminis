"""Consulta de CEP: BrasilAPI primeiro, ViaCEP como fallback."""
import httpx
from fastapi import HTTPException

TIMEOUT = httpx.Timeout(6.0, connect=4.0)


def _clean(cep: str) -> str:
    d = "".join(c for c in (cep or "") if c.isdigit())
    if len(d) != 8:
        raise HTTPException(status_code=400, detail="CEP inválido. Informe 8 dígitos.")
    return d


def lookup(cep: str) -> dict:
    d = _clean(cep)
    # 1) BrasilAPI
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.get(f"https://brasilapi.com.br/api/cep/v1/{d}")
        if r.status_code == 200:
            j = r.json()
            return {"cep": d, "street": j.get("street", ""), "district": j.get("neighborhood", ""),
                    "city": j.get("city", ""), "uf": j.get("state", "")}
    except httpx.HTTPError:
        pass
    # 2) ViaCEP (fallback)
    try:
        with httpx.Client(timeout=TIMEOUT) as c:
            r = c.get(f"https://viacep.com.br/ws/{d}/json/")
        if r.status_code == 200:
            j = r.json()
            if not j.get("erro"):
                return {"cep": d, "street": j.get("logradouro", ""), "district": j.get("bairro", ""),
                        "city": j.get("localidade", ""), "uf": j.get("uf", "")}
    except httpx.HTTPError:
        pass
    raise HTTPException(status_code=404, detail="CEP não encontrado. Verifique ou preencha manualmente.")
