import random
import requests


def authenticated_session():
    """
    Session para testes HTTP locais.

    A aplicação usa cookies Secure corretamente em produção.
    Como requests não reenvia cookies Secure sobre HTTP local,
    preserve_auth_cookie() replica somente os cookies de autenticação
    no header Cookie da sessão de teste.
    """
    return requests.Session()


def preserve_auth_cookie(session, response):
    """
    Preserva access_token e refresh_token recebidos pela resposta.

    Necessário apenas para testes HTTP executados em
    http://127.0.0.1, pois cookies Secure não são reenviados
    automaticamente pelo requests nesse transporte.
    """
    tokens = {}

    for cookie in response.cookies:
        if cookie.name in ("access_token", "refresh_token"):
            tokens[cookie.name] = cookie.value

    # Fallback para respostas nas quais requests não exponha
    # todos os cookies individualmente.
    raw = response.headers.get("set-cookie", "")

    for name in ("access_token", "refresh_token"):
        if name not in tokens and f"{name}=" in raw:
            tokens[name] = raw.split(
                f"{name}=", 1
            )[1].split(";", 1)[0]

    if tokens:
        # Mantém tokens anteriores caso uma resposta, como refresh,
        # atualize apenas um deles.
        existing = {}

        current = session.headers.get("Cookie", "")
        for part in current.split(";"):
            part = part.strip()
            if "=" in part:
                key, value = part.split("=", 1)
                if key in ("access_token", "refresh_token"):
                    existing[key] = value

        existing.update(tokens)

        cookie_header = "; ".join(
            f"{name}={existing[name]}"
            for name in ("access_token", "refresh_token")
            if name in existing
        )

        session.headers.update({"Cookie": cookie_header})

    return session


def valid_cpf():
    """
    Gera CPF matematicamente válido para fixtures.
    Não utiliza CPF real conhecido.
    """
    digits = [random.randint(0, 9) for _ in range(9)]

    if len(set(digits)) == 1:
        digits[8] = (digits[8] + 1) % 10

    for length in (9, 10):
        total = sum(
            digits[i] * (length + 1 - i)
            for i in range(length)
        )
        digit = (total * 10) % 11
        if digit == 10:
            digit = 0
        digits.append(digit)

    return "".join(map(str, digits))
