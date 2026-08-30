# Brasil Minis — Análise de Retomada para Python/FastAPI + React (VPS)

> Documento de ANÁLISE (read-only). Nenhuma mudança destrutiva foi feita.
> Objetivo: abandonar Laravel/PHP como produção e consolidar Python/FastAPI + React em VPS Ubuntu 24.04.

## 1. Inventário do projeto atual

### Backend Python/FastAPI (`/app/backend`) — ~1000 LOC
- `server.py` (app FastAPI, CORS, startup seed/índices), `db.py` (**MongoDB via Motor**), `security.py` (bcrypt + JWT/pyjwt), `deps.py` (get_current_user/get_current_admin), `models.py` (schemas Pydantic), `seed.py`, `utils.py`.
- `routers/`: `auth.py` (154), `admin.py` (192), `orders.py` (117), `catalog.py` (112), `account.py` (68), `reviews.py` (42), `favorites.py` (32), `banners.py` (11).
- `.env`: `MONGO_URL, DB_NAME, CORS_ORIGINS, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD`.
- Testes: `backend/tests/backend_test.py`, `pytest.ini`.

### Frontend React (`/app/frontend`) — completo
- **React 19 + CRA (react-scripts 5) + CRACO** — NÃO é Vite. Arquivos **`.js`** — NÃO é TypeScript.
- Páginas: Home, Catalog, ProductDetail, Cart, Checkout, Brands, Contact, Favorites, Login, Register, PasswordRecovery, Account; Admin (Dashboard, Products, Orders, Customers, Categories, Brands, Banners).
- `context/` (Auth, Cart, Favorites), `lib/api.js` (axios + `REACT_APP_BACKEND_URL`), `lib/brand.js` (identidade), shadcn UI completo, Tailwind.
- Identidade visual Brasil Minis já pronta (a preservar).

### Laravel/PHP (`/app/laravel`) — tentativa de migração (a remover após aprovação)
- **113 arquivos .php**, **34 blades**, **8 migrations**, config, seeders, `deploy/`, `.env.example`.
- `/.github/workflows/deploy.yml` (pipeline Locaweb), `/app/docs/MIGRATION_PHASE1_INVENTORY.md`.

## 2. Comparação Python original × Laravel

| Aspecto | Python/FastAPI (original) | Laravel (tentativa) |
|---|---|---|
| Motivação | Stack principal desejada | Contornar hospedagem compartilhada (Locaweb) — **não mais necessária** |
| Banco | **MongoDB** (schemaless) | MySQL 8 + Eloquent + migrations |
| API | REST `/api/*` consumida pelo React | Blade server-side (SSR) |
| Front | React SPA (CRA) | Blade + Alpine |
| Estado | Funcional e testado (iteration_1) | Gerado como texto, **nunca executado** (sem runtime PHP) |
| Decisão | **MANTER como base** | **DESCARTAR** |

## 3. O que já existe e pode ser reaproveitado
- **Frontend React inteiro** (storefront + admin + identidade visual + contexts). Reaproveitamento ~100%.
- **Backend FastAPI**: rotas, auth JWT+bcrypt, RBAC admin, catálogo, favoritos, reviews, banners, pedidos com cupom/frete, seed. Lógica reaproveitável ~90% (muda a camada de persistência).
- Modelos de domínio (Pydantic) e regras de negócio (cupom, frete grátis ≥ R$300, snapshot de itens no pedido).
- Testes de backend existentes como base de regressão.

## 4. O que precisa ser corrigido / evoluir
1. **Persistência**: hoje é **MongoDB**. Alvo pedido = **PostgreSQL + SQLAlchemy + Alembic**. É a maior mudança (reescrita da camada de dados + script de migração de dados).
2. **Camada de serviços**: regras financeiras/estoque estão **inline nos routers** (`orders.py`). Mover para `services/` (routers só HTTP).
3. **Baixa de estoque NÃO atômica**: hoje lê e depois `$inc` separadamente (condição de corrida). Alvo: transação + `SELECT ... FOR UPDATE` no PostgreSQL, impedindo estoque negativo via constraint (`CHECK stock >= 0`).
4. **Estrutura de pastas**: achatada → modular (`app/core, db, models, schemas, routers, services, dependencies`).
5. **Campos de produto ausentes** na feature list: SKU, código de barras, peso, dimensões, histórico de movimentação de estoque, histórico de status de pedido. (preço promocional já existe via `compare_at_price`).
6. **Frete**: hoje valor fixo. Preparar contrato/serviço para Correios / Melhor Envio (sem integrar agora).
7. **Pagamento**: manter **MOCK** (já é), arquitetura pronta para Mercado Pago depois.
8. **Segurança**: CORS hoje default `*` — restringir por env; adicionar rate limiting em auth/admin; secrets só no `.env`.
9. **Frontend Vite/TS**: hoje é **CRA + JS**. Ver decisão na seção 9.

## 5. Arquitetura Python final proposta
```
brasilminis/
├── backend/
│   ├── app/
│   │   ├── main.py                 # cria FastAPI, monta routers, CORS
│   │   ├── core/                   # config (Pydantic Settings), security (JWT/bcrypt), rate limit
│   │   ├── db/                     # engine SQLAlchemy, Session, Base
│   │   ├── models/                 # ORM: User, Address, Category, Brand, Product, StockMovement,
│   │   │                           #      Cart, CartItem, Coupon, Order, OrderItem, OrderStatusHistory,
│   │   │                           #      Banner, Review, PasswordResetToken
│   │   ├── schemas/                # Pydantic entrada/saída
│   │   ├── routers/                # auth, catalog, orders, account, favorites, reviews, banners, admin
│   │   ├── services/               # cart_service, order_service (transação+lock), stock_service,
│   │   │                           #      coupon_service, shipping_service, payment_service (mock)
│   │   └── dependencies/           # get_db, get_current_user, get_current_admin
│   ├── alembic/                    # migrations versionadas
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example
├── frontend/                       # React (mantido) → build estático servido pelo Nginx
└── infra/
    ├── nginx/brasilminis.conf
    ├── systemd/brasilminis-backend.service
    └── deploy.sh
```
- **DB**: PostgreSQL, SQLAlchemy 2.x (ORM), Alembic (migrations), FKs + índices + `CHECK` (estoque ≥ 0) + transações.
- **Auth**: JWT (mantém), bcrypt, cookie httpOnly + Bearer (compatível com o front atual).
- **Camadas**: routers (HTTP) → services (negócio) → models (dados) → schemas (I/O).

## 6. Plano de limpeza do repositório (após aprovação)
1. Criar branch `python-vps` (ou reutilizar a base) a partir do estado atual — **sem force push**.
2. **Remover** `/app/laravel` inteiro.
3. **Remover** `/app/.github/workflows/deploy.yml` (pipeline Locaweb) e `/app/docs/MIGRATION_PHASE1_INVENTORY.md` (contexto Laravel).
4. Manter `/app/backend` e `/app/frontend`. Refatorar backend para a estrutura `app/` + Postgres/Alembic.
5. Atualizar `README.md`, `.gitignore`, `docs/` para a stack Python/VPS.
6. Nenhuma sobrescrita de histórico; commits via "Save to Github".

## 7. Plano de implantação na VPS (Ubuntu 24.04, sem Docker)
- Pacotes: `python3.12-venv`, `postgresql`, `nginx`, `certbot`.
- Backend: venv + `pip install -r requirements.txt`; `alembic upgrade head`; rodar via **Gunicorn+UvicornWorker** sob **systemd** (`brasilminis-backend.service`) em socket/porta local.
- Frontend: `npm ci && npm run build` → servir `build/` pelo Nginx.
- Nginx: servir SPA (fallback `index.html`), proxy `/api` → backend, servir `/uploads`, HTTPS via Let's Encrypt (certbot).
- Deploy simples: `git pull → pip install → alembic upgrade head → npm run build → systemctl restart brasilminis-backend → nginx -s reload`.

## 8. Riscos identificados
- **R1 — Migração de dados Mongo→Postgres**: schemas diferentes (documentos aninhados: `addresses`, `items`). Precisa script ETL + mapeamento de ids (UUID string atuais → manter como coluna).
- **R2 — Ambiente de preview Emergent usa MongoDB gerenciado**, não Postgres. Para testar aqui será preciso subir um PostgreSQL local no container (efêmero); produção real fica na VPS. Decisão necessária.
- **R3 — Reescrita da persistência** toca todos os routers → risco de regressão. Mitigar com testes (pytest) reaproveitados/ampliados.
- **R4 — Atomicidade de estoque**: garantir transação/lock para não vender além do estoque.
- **R5 — Vite/TS**: migrar CRA→Vite e JS→TS é opcional e adiciona risco sem ganho funcional imediato.
- **R6 — CORS/secrets**: garantir CORS restrito e segredos fora do Git.

## 9. Próximas fases recomendadas (após aprovação)
- **Fase 0**: limpeza do repo (remover Laravel/pipeline) + criar estrutura `app/`.
- **Fase 1**: infra de dados — engine SQLAlchemy + Base + Alembic + `.env` Postgres; modelos ORM.
- **Fase 2**: portar auth + catálogo (routers→services) e validar com pytest.
- **Fase 3**: pedidos/estoque com transação atômica + cupom + frete (serviço) + pagamento mock.
- **Fase 4**: admin (produtos/estoque/pedidos/clientes/categorias/marcas/cupons/banners).
- **Fase 5**: script de migração de dados Mongo→Postgres (opcional, se houver dados a preservar).
- **Fase 6**: arquivos de infra (nginx.conf, systemd.service, deploy.sh) + guia VPS.
- **Fase 7**: evoluções (SKU/barcode/peso/dimensões, histórico de estoque/status, Correios/Melhor Envio, Mercado Pago).

### Decisões que preciso confirmar antes de executar
1. PostgreSQL no preview: subir Postgres local no container para testes (produção fica na VPS)? [sim/não]
2. Frontend: manter **CRA + JS** (menor risco, build serve igual no Nginx) ou migrar para **Vite + TS**? 
3. Laravel: **remover** de vez o `/app/laravel` e o pipeline Locaweb, ou **arquivar** numa branch/tag antes?
4. Dados: existe base MongoDB de produção com dados reais a migrar, ou podemos recomeçar com seed?
