# Brasil Minis — Playbook de Teste de Autenticação (FastAPI + SQLAlchemy + PostgreSQL)

Auth por JWT (bcrypt) com cookies httpOnly (`access_token`/`refresh_token`) + fallback Bearer.
Cookies são `Secure` + `SameSite=none` → testar via HTTPS (URL de preview), não http localhost.

## Credenciais
- Admin: `admin@brasilminis.com` / `Admin@2025`
- Cliente: criar via `/api/auth/register`

## Verificação no banco (PostgreSQL)
```
PGPASSWORD=brasilminis psql -h 127.0.0.1 -U brasilminis -d brasilminis \
  -c "SELECT email, role, left(password_hash,4) AS hash FROM users;"
```
Esperado: hash bcrypt começando com `$2b$`.

## Teste de API (HTTPS de preview)
```
API=https://vroom-preview.preview.emergentagent.com
curl -s -c c.txt -X POST "$API/api/auth/login" -H "Content-Type: application/json" \
  -d '{"email":"admin@brasilminis.com","password":"Admin@2025"}'
curl -s -b c.txt "$API/api/auth/me"          # retorna o usuário admin
curl -s -b c.txt "$API/api/admin/stats"      # 403 se não for admin
```

## Fluxos principais a validar
1. Login admin → `/me` → `/admin/stats` (RBAC).
2. Registro de cliente → login → `/api/auth/me`.
3. Criar pedido (`POST /api/orders`) baixa estoque de forma atômica (não permite estoque negativo).
4. Cupom (`POST /api/coupons/validate`) e desconto no pedido.
5. Brute force: 5 falhas de login → 429 por 15 min.
