from app.core.config import settings


def compute_shipping(amount_after_discount: float, method: str = "standard") -> float:
    """Frete simples. Preparado para integração futura (Correios / Melhor Envio).

    Regra atual: grátis acima do limite, senão valor padrão.
    """
    if amount_after_discount >= settings.FREE_SHIPPING_THRESHOLD:
        return 0.0
    return settings.STANDARD_SHIPPING
