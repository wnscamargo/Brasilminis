def build_mock_payment(method: str) -> dict:
    """Pagamento SIMULADO (mock). Arquitetura pronta para Mercado Pago no futuro."""
    return {
        "provider": "mock",
        "method": method,
        "pix_qr": "00020126BR.GOV.BCB.PIX-SIMULATED" if method == "pix" else None,
        "status": "approved",
    }


PAYMENT_STATUS_MOCK = "paid_simulated"
