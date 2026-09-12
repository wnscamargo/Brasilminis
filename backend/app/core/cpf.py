"""Validação e normalização de CPF (dado pessoal — nunca logar/expor em URL)."""


def normalize_cpf(value) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())


def is_valid_cpf(value) -> bool:
    cpf = normalize_cpf(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        total = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        check = ((total * 10) % 11) % 10
        if check != int(cpf[i]):
            return False
    return True
