# Central de Integrações — Guia (Brasil Minis)

Todas as credenciais **operacionais** são gerenciadas pelo painel Admin em
`/admin/integracoes` e salvas **cifradas no banco** (Fernet). O `.env` guarda
apenas chaves de criptografia/infra — **nunca** tokens ou secrets operacionais.

## Variáveis obrigatórias no `backend/.env`
```
# Criptografia (Fernet) — geradas uma vez, NUNCA versionar
MERCADO_PAGO_TOKEN_ENCRYPTION_KEY=<fernet-key>
MELHOR_ENVIO_TOKEN_ENCRYPTION_KEY=<fernet-key>

# Infra
MERCADO_PAGO_API_BASE=https://api.mercadopago.com
MELHOR_ENVIO_USER_AGENT_EMAIL=contato@seudominio.com
FRONTEND_URL=https://seudominio.com    # usado no redirect pós-callback do OAuth

# Legado (mantidos VAZIOS — o painel tem prioridade)
MELHOR_ENVIO_CLIENT_ID=
MELHOR_ENVIO_CLIENT_SECRET=
MELHOR_ENVIO_REDIRECT_URI=
```
Gerar uma chave Fernet: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

## Mercado Pago
1. Painel → Integrações → card Mercado Pago.
2. Ambiente **Teste**: cole `Public Key (TEST-...)` e `Access Token (TEST-...)`, salve → fica ativo no checkout.
3. Webhook: configure a URL `https://SEU_DOMINIO/api/webhooks/mercado-pago` no painel do MP e cole o *webhook secret* (opcional, valida a assinatura HMAC).
4. **Produção** (bloqueada contra ativação acidental):
   - Troque o ambiente para **Produção** (limpa credenciais de teste).
   - Cole `Public Key (APP_USR-...)` e `Access Token (APP_USR-...)` de produção e salve.
   - Clique **Testar** (precisa status = *Conectado*).
   - Clique **Ativar produção** e confirme. Só então a loja cobra pagamentos reais.

## Melhor Envio
1. Crie um app em https://app.melhorenvio.com.br (produção) ou https://app-sandbox.melhorenvio.com.br (sandbox).
2. Painel → Integrações → card Melhor Envio: informe `Client ID`, `Client Secret`, `Redirect URI`.
   - A **Redirect URI** deve bater byte a byte com o app: `https://SEU_DOMINIO/api/admin/melhor-envio/callback`.
3. Salve → clique **Conectar** (OAuth) → autorize a conta.
4. Scopes solicitados: `shipping-calculate cart-write cart-read shipping-checkout shipping-generate shipping-print`.
5. Trocar de ambiente (Sandbox↔Produção) **desassocia** o token/sessão anteriores.

## Fluxo de checkout (real)
Carrinho → CEP/endereço → cotação de frete (Melhor Envio) → total → PIX/Cartão
(Mercado Pago) → webhook → atualização idempotente do pedido. Quando o MP não está
ativo, o checkout usa pagamento **SIMULADO** (para desenvolvimento/demo).

## Deploy
Não fazer deploy automático. Trabalho na branch `integrations-production-ready`
(use o botão **Save to Github** do chat). Rodar migrations no destino:
`cd backend && alembic upgrade head` (head atual: `f5a6b7c8d9e0`).
