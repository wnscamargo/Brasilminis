# Brasil Minis — PRD

## Original Problem Statement
E-commerce premium "Brasil Minis" para miniaturas colecionáveis, acessórios e vestuário automotivo. Identidade visual premium (Porsche/BMW M/Gran Turismo/Apple/LEGO/Nike). Dark theme, Orbitron + Exo 2, paleta Azul VW #1E3A8A / Verde #009B3A / Amarelo #FFC107. Desenvolvido do zero, sem CMS.

## User Choices
- Stack: React + FastAPI + MongoDB (arquitetura limpa, preparada para migração).
- Logo: provisória gerada no estilo da marca.
- Pagamento: checkout simulado (mock), preparado para Mercado Pago futuro (PIX/cartão/boleto/webhooks).
- Auth: e-mail + senha (JWT via httpOnly cookies).
- MVP completo: Home, catálogo, categorias, pesquisa, produto, carrinho, checkout, cadastro/login, minha conta, favoritos, painel admin (produtos, categorias, marcas, estoque, dashboard, banner), responsivo.

## Architecture
- Backend modular: `db.py`, `security.py`, `deps.py`, `models.py`, `utils.py`, `seed.py`, `server.py`, `routers/{auth,catalog,reviews,favorites,orders,account,banners,admin}.py`. Todas rotas sob `/api`.
- Frontend: React Router, contexts (Auth/Cart/Favorites), design system em `lib/brand.js` + `index.css`, componentes reutilizáveis (ProductCard, TrustIcons, Header/Footer/Layout, Guards), páginas storefront + `pages/admin/*`.
- MongoDB collections: users, products, categories, brands, orders, favorites, reviews, banners, coupons, login_attempts, password_reset_tokens.

## Implemented (2026-06)
- Full storefront: hero banner, categorias por grupo, destaques/lançamentos/promoções, marcas, newsletter, trust icons, footer.
- Catálogo com filtros (categoria, marca, promoções), ordenação, busca, paginação.
- Página de produto: galeria/thumbs, zoom hover, badges, especificações, avaliações (CRUD), relacionados, favoritar, comprar.
- Carrinho (localStorage) com frete grátis progressivo; Checkout single-page (endereço, PIX/cartão/boleto, cupom) com pagamento SIMULADO e confirmação.
- Auth JWT (cookies httpOnly), registro/login/logout/me/refresh/forgot/reset, brute-force lockout, admin seeding.
- Minha Conta: pedidos, endereços, dados, senha. Favoritos persistidos por usuário.
- Painel Admin (admin-only/RBAC): dashboard com gráfico de faturamento, CRUD de produtos com controle de estoque + badges, categorias, marcas, pedidos (status), clientes, banners.
- Seed: 28 produtos, categorias, 10 marcas, banner, cupons (BRASIL10/MINIS20/FRETEGRATIS).
- Testing: 32/32 backend pass; todos os fluxos críticos de frontend verificados.

## Backlog / Next (P1/P2)
- Integração real Mercado Pago (PIX/cartão/boleto + webhooks + atualização de status).
- Integração Melhor Envio (cálculo de frete por CEP).
- Módulos complementares: relatórios/financeiro/SEO avançado, gestão de usuários admin.
- Dedup de reviews, guarda de concorrência no estoque, página dedicada de pedido (/pedido/:id).
- Wishlist para convidados, cupons por admin, uploads de imagem (object storage).

## Credentials
Ver `/app/memory/test_credentials.md`. Admin: admin@brasilminis.com / Admin@2025.

## Notes
- MOCKED: pagamento no POST /api/orders (payment_status=paid_simulated, PIX QR fictício).

---

## Migração para Laravel 12 (Locaweb) — em `/app/laravel/`
- **Fase 1 (Inventário)**: `/app/docs/MIGRATION_PHASE1_INVENTORY.md` — mapa ATUAL→NOVO + schema MySQL. Aprovada.
- **Decisões aprovadas**: código em `/app/laravel/` (commit no GitHub); auth Laravel Breeze/sessão; dados via Seeder (28 produtos); produto = base + `product_attributes` (EAV) + `product_variants`; status EN (PENDING…REFUNDED).
- **Fases 2–6 GERADAS** (código versionável, NÃO executado no preview pois não há PHP):
  - Fundação: composer/bootstrap/public/configs, `.env.example`, `EnsureUserIsAdmin`, AppServiceProvider.
  - Banco: 8 arquivos de migration → 23 tabelas (users, addresses, categories, brands, manufacturers, products+images/attributes/variants, favorites, carts/cart_items, coupons, orders/order_items/order_status_history, banners, reviews, settings, audit_logs).
  - Models Eloquent (18) com relações/scopes/casts; Services (Cart, Order c/ transação+lockForUpdate, Payment mock→MercadoPago).
  - Controllers (storefront, Account, Auth, Admin) + `routes/web.php` (rotas PT).
  - Views Blade (34): layout/partials, home, catálogo, produto, carrinho, checkout(+sucesso), favoritos, marcas, contato, auth (4), conta (6), admin (9). Tailwind com identidade Brasil Minis (cores/fontes/texturas).
  - Seeder (admin + cliente demo + 28 produtos + cupons + banner).
  - Deploy: GitHub Actions (SSH Locaweb), `deploy/deploy.sh`, `deploy/public_html_index.php`, `.htaccess`.
  - Testes Pest (ShopTest, OrderTest) + phpunit (SQLite em memória).
- **Fase 7 (Produção)**: instruções no `/app/laravel/README.md` (MySQL Locaweb, secrets do Actions, SSL). Pendente execução/homologação pelo usuário.
- **Regra crítica respeitada**: app React/FastAPI original permanece intacto como referência.
- **Validação pendente (ambiente sem PHP)**: rodar `composer install && php artisan migrate --seed && ./vendor/bin/pest` localmente/CI.

---
## Preparação p/ GitHub (branch laravel-migration) — data desta sessão
- Seeder endurecido: `EssentialSeeder` (categorias/marcas, seguro em prod), `DemoSeeder` (produtos/cupons/banner/usuários demo) **bloqueado em produção**; `DatabaseSeeder` só roda Demo fora de produção.
- Comando seguro `php artisan bm:create-admin` para admin de produção (senha gerada/1x, sem senha versionada).
- `.env.example` com DB_* vazios (placeholders); `.gitignore` protege `.env`, `.env.*` (exceto `.env.example`), `vendor/`, `node_modules/`, `public/storage`, `storage/*.key`.
- Deploy Locaweb ajustado ao caminho real `.../brasilminis/app/laravel` (deploy.sh, public_html_index.php, GitHub Actions com secrets SSH_HOST/USER/PORT/PRIVATE_KEY/DEPLOY_PATH, php83).
- Varredura de segredos: nenhum segredo real no código (apenas `env()` placeholders e APP_KEY de teste no phpunit.xml).
- PUSH pendente: feito pelo usuário via "Save to Github" na branch `laravel-migration` (sem merge na main).

---
## Pipeline Build+Deploy Locaweb (GitHub Actions) — Junho/2026
Motivo: Locaweb desabilita php_strip_whitespace/proc_open/exec/shell_exec/system/symlink → Composer não gera vendor/autoload.php na hospedagem. Build passa a ser 100% no GitHub Actions; Locaweb só executa Laravel.
Arquivos modificados/criados (branch laravel-migration):
- **CRIADO** `/.github/workflows/deploy.yml` (raiz do repo): PHP 8.3 → composer install --no-dev --optimize-autoloader → yarn build (Vite) → rsync do Laravel (com vendor/) p/ LOCAWEB_PATH → rsync public/ p/ LOCAWEB_PUBLIC_PATH + index.php próprio → SSH php83 artisan migrate/config/route/view:cache (com fallback, sem quebrar). Secrets: LOCAWEB_HOST/USER/PORT/SSH_KEY/PATH/PUBLIC_PATH.
- **REMOVIDO** `/laravel/.github/workflows/deploy.yml` (GitHub só lê workflows na raiz; a versão antiga rodava composer/git pull na Locaweb — inválido).
- **REESCRITO** `/laravel/deploy/deploy.sh`: pós-deploy manual só com Artisan (php83), sem composer/npm, tolerante a funções bloqueadas, exige vendor/ já presente.
- **ATUALIZADO** `/laravel/deploy/public_html_index.php`: base = ../brasilminis/laravel (caminho real, sem segmento app/), fallback absoluto comentado.
- **ATUALIZADO** `/laravel/config/filesystems.php`: novo disco `uploads` (sem symlink) via UPLOADS_ROOT/UPLOADS_URL.
- **ATUALIZADO** `/laravel/.env.example`: UPLOADS_ROOT/UPLOADS_URL + comentários.
- **CRIADO** `/laravel/public/uploads/.gitignore`: versiona a pasta, ignora uploads de runtime.
- **ATUALIZADO** `/laravel/README.md`: novo fluxo, secrets, composer.lock obrigatório, uploads sem symlink.
Regras respeitadas: sem novas features, sem mudança de layout, Mercado Pago NÃO ativado, sem merge na main.
Pendências do usuário: (1) gerar `composer.lock` localmente e commitar; (2) configurar os 6 Secrets; (3) Save to Github na branch laravel-migration.
Validação: YAML e bash validados no ambiente. PHP/rsync/SSH não executáveis aqui (sem runtime) → homologação real na Locaweb pelo usuário.

---
## Retomada Python/FastAPI + React (VPS) — Junho/2026
Decisão do usuário: abandonar Laravel/PHP; consolidar Python/FastAPI + React em VPS Ubuntu 24.04. Persistência migrada de MongoDB → **PostgreSQL + SQLAlchemy + Alembic**. Frontend mantido (CRA + JS). Pagamento MOCK. Recomeço com seed.

### Concluído e TESTADO (41/41 pytest + smoke HTTPS + screenshot)
- Backend reescrito na estrutura modular `backend/app/`: `core/` (config, security JWT+bcrypt), `db/` (engine/session/base), `models/` (ORM PostgreSQL, JSONB, CHECK stock>=0), `schemas/` (Pydantic), `dependencies/` (get_db, get_current_user, get_current_admin), `routers/` (auth, catalog, orders, account, favorites, reviews, banners, admin), `services/` (order c/ baixa ATÔMICA via with_for_update, coupon, shipping, payment mock), `seed.py`.
- Contrato REST idêntico → frontend React não alterado e funcionando.
- `backend/server.py` mantido como entrypoint do supervisor (importa `app.main:app`).
- Alembic configurado + migração inicial `ea44b6ac0765` (12 tabelas) aplicada. `AUTO_CREATE_TABLES=true` só em preview.
- PostgreSQL 15 local no container (auto-start via supervisor) + DATABASE_URL no `.env`.
- Removidos os arquivos Mongo antigos (`db.py, deps.py, security.py, models.py, seed.py, utils.py, routers/, tests/` antigos) — preservados no histórico git.
- Fix de segurança (achado pelo testing agent): brute force agora usa `X-Forwarded-For` (ingress K8s) e só trava ao atingir 5 tentativas → 429 (verificado).

### Pendente (próximas fases)
- Fase 0 (git): usuário arquiva Laravel numa branch/tag (`archive/laravel`) e então autoriza a remoção de `/app/laravel` + workflow Locaweb `.github/workflows/deploy.yml` + `docs/MIGRATION_PHASE1_INVENTORY.md` na branch `python-vps`.
- Fase 6 (infra VPS): `infra/nginx/brasilminis.conf`, `infra/systemd/brasilminis-backend.service` (Gunicorn+UvicornWorker), `infra/deploy.sh`, guia Let's Encrypt.
- Fase 7 (evoluções): SKU, código de barras, peso/dimensões, histórico de estoque/status, Correios/Melhor Envio, Mercado Pago real.

### Arquivos de referência (novos)
- `backend/app/**`, `backend/alembic/**`, `backend/alembic.ini`, `backend/server.py`
- `docs/RETOMADA_PYTHON_ANALISE.md` (análise completa das 9 entregas)
- `memory/test_credentials.md`, `auth_testing.md`

---
## Infra de produção VPS (Ubuntu 24.04) — Junho/2026
Gerada (não-destrutiva). Laravel AINDA presente — remoção condicionada à confirmação do usuário de que criou a branch/tag `archive/laravel`.
Arquivos criados:
- `infra/nginx/brasilminis.conf` — SPA em / + proxy /api -> 127.0.0.1:8000; gzip; cache de assets; SPA fallback; HTTPS; **anti-spoofing**: sobrescreve X-Forwarded-For com $remote_addr (não anexa) + X-Real-IP + X-Forwarded-Proto.
- `infra/systemd/brasilminis-backend.service` — Gunicorn+UvicornWorker (`server:app`), user `brasilminis` (não-root), autostart/restart, EnvironmentFile, hardening.
- `infra/scripts/deploy.sh` — set -euo pipefail; git pull ff-only (sem reset/force); pip; `alembic upgrade head`; build isolado (BUILD_PATH=build_new, promoção atômica; build falho não derruba versão); restart backend; nginx -t + reload. Sem seed automático, sem reset de banco, preserva .env/uploads.
- `infra/scripts/backup-db.sh` — pg_dump | gzip timestampado + retenção (RETENTION_DAYS). `infra/scripts/restore-db.sh` — manual, destrutivo, exige digitar RESTAURAR.
- `infra/docs/VPS_DEPLOY.md` — passo a passo 1..25 (usuário, UFW 22/80/443, Nginx, Python 3.12, PostgreSQL local, Node, Git, venv, .env, DB, Alembic, build, systemd, Certbot, homologação).
- `backend/.env.example` — placeholders de produção (APP_ENV=production, DEBUG=false, AUTO_CREATE_TABLES=false, CORS só domínios oficiais). Nenhum segredo real.
Regra: Mercado Pago/Correios/Melhor Envio/histórico de status NÃO implementados nesta fase (estabilizar VPS primeiro). Histórico de status: APROVADO para depois.
Pendências git (usuário): (1) confirmar archive/laravel; (2) autorizar remoção de laravel/ + workflow Locaweb + docs/MIGRATION_PHASE1_INVENTORY.md na branch python-vps.

---
## Limpeza branch python-vps + health check + smoke-test deploy — Junho/2026
- REMOVIDOS (branch python-vps; archive/laravel preservada pelo usuário): `/app/laravel` (todo), `.github/workflows/deploy.yml` (Locaweb), `docs/MIGRATION_PHASE1_INVENTORY.md`. Nenhum arquivo Python/FastAPI/React afetado (backend/app = 26 .py intactos). Sem force push / sem reescrever histórico.
- `/api/health` evoluído (app/main.py): retorna {status, database, migration} — 200 saudável / 503 se banco indisponível. Checa SELECT 1 + compara revisão Alembic atual vs head. Não expõe segredos/stack/infra. Verificado 200 e 503.
- Startup do backend agora é resiliente: aguarda o banco (retry) e sobe em modo degradado (health 503) em vez de crashar; seed/create_all protegidos.
- `infra/scripts/deploy.sh`: smoke-test pós-deploy — após restart, faz polling em /api/health; só conclui se status ok; em falha faz rollback SEGURO só do FRONTEND (restaura build anterior, guarda build_failed), loga motivo e o SHA anterior p/ rollback manual de código; NÃO faz rollback de migration nem restore de banco.
- Preview infra: PostgreSQL é efêmero entre reinícios de pod. Adicionados `backend/scripts/ensure_db.sh` (recria role/DB idempotente) + supervisor `pg-bootstrap` para o backend reconectar após restart. (Só preview; VPS persiste.)
- Testes: 41/41 pytest PASS (test_health atualizado p/ novo contrato). Fluxos HTTPS revalidados: health, login admin, RBAC (401 anon / 403 cliente / 200 admin), pedido com cupom+frete e baixa atômica (50→47), estoque insuficiente => 400 sem baixar. Banco de preview resetado ao seed limpo (28 produtos).

---
## Nova identidade visual (logo + favicon) — Junho/2026
- Logo oficial (imagem enviada: VW azul + bandeira do Brasil + "BRASIL MINIS DIECAST") aplicada. Fundo preto tornado TRANSPARENTE via flood-fill pelas bordas (preserva pretos internos; sem redesenhar/cortar conteúdo), margens vazias aparadas. Salvo em `frontend/public/brasil-minis-logo.png` (936×1196, transparente).
- Substituída em: Header (`h-12 md:h-16`, object-contain, link para /, alt "Brasil Minis - Miniaturas e Diecast"), Footer, Login e AdminLayout (object-cover → object-contain p/ não cortar). `lib/brand.js` LOGO_HEADER/LOGO_EMBLEM → "/brasil-minis-logo.png".
- Favicons gerados (Pillow): favicon.ico (16/32/48), favicon-32x32.png, apple-touch-icon.png (180), logo192/512.png. `public/index.html` com <link> icon/apple-touch/manifest + theme-color #111111; `public/manifest.json` criado. Todos servindo HTTP 200.
- Sem mudanças em funcionalidades/catálogo/carrinho/checkout/auth/admin. `/api/health` segue 200.
- Ajuste de infra preview: `AUTO_CREATE_TABLES=false`; `ensure_db.sh` agora aplica `alembic upgrade head` (fallback `stamp head`) para o health reportar migration=current após reinício de pod; startup do backend espera as tabelas antes do seed.

---
## Modo "Site em Construção" gerenciável pelo admin — Junho/2026
Configuração persistente no PostgreSQL (linha única site_settings), gate anti-flash no frontend, página premium, controle total pelo admin. Sem migração de tecnologia.
Backend (novos/alterados): `app/models/__init__.py` (+SiteSettings), `app/schemas/__init__.py` (+SiteSettingsInput c/ validação de URL), `app/services/site_service.py` (novo), `app/routers/site.py` (novo), `app/main.py` (inclui router site), `app/seed.py` (garante linha site_settings). Migration Alembic: `21a5e90c8117_site_settings.py`.
Endpoints: GET /api/site-status (público, leve), GET/PUT /api/admin/site-settings (role admin; PUT valida URLs, grava updated_at/updated_by).
Frontend (novos/alterados): `components/MaintenanceGate.js` (novo — fetch /site-status no boot, BootSplash, libera /login,/cadastro,/recuperar-senha,/reset-password,/em-construcao e prefixos /conta,/admin; bloqueia rotas públicas p/ não-admin; fail-open em erro), `pages/UnderConstruction.js` (novo — premium, countdown, WhatsApp/Instagram target=_blank rel=noopener), `pages/admin/AdminSite.js` (novo — toggle c/ confirmação, campos, salvar, "Visualizar página" /em-construcao?preview=1), `App.js` (MaintenanceGate envolve Routes; rota /em-construcao; child admin "site"), `pages/admin/AdminLayout.js` (item de menu "Site em Construção").
Testes: `tests/backend_test.py` +TestSiteMaintenance (5 casos). Suíte: 46/46 pytest PASS. Frontend E2E (testing_agent): 100% (10/10 cenários), 0 issues.
Comportamento validado: OFF→storefront normal; ON→visitante anônimo vê construção em /, /produtos, /produto/:slug; /login e /admin não bloqueados; countdown; preview; sem redirect loop; revert imediato; health nunca bloqueado; customer não acessa config (403). Efeito imediato (sem restart/rebuild). Estado final: manutenção DESATIVADA.
Deploy VPS: o `deploy.sh` já roda `alembic upgrade head` (aplica a nova migration) + rebuild do frontend. Nenhum passo extra.

---
## Identidade Visual GLOBAL gerenciada pelo admin — Junho/2026
Config global (logo + tamanho) reutilizando site_settings; usada pelo site e reutilizada pela manutenção. Sem migração de tecnologia. Upload persistente fora de frontend/build.
Backend (novos/alterados): `app/models/__init__.py` (+colunas logo_url, logo_width, branding JSONB em SiteSettings), `app/core/config.py` (+UPLOADS_DIR), `app/schemas/__init__.py` (+SiteConfigInput: logo_width 60–500, branding), `app/services/site_service.py` (+public_config/admin_config/update_config/save_logo(Pillow: MIME+dimensões+tamanho, nome próprio uuid, sem path traversal)/delete_logo), `app/routers/site.py` (+GET /api/site-config, GET/PUT /api/admin/site-config, POST/DELETE /api/admin/site-config/logo), `app/main.py` (StaticFiles mount /api/uploads). Migration Alembic: `455b5d4bbb3e_site_branding.py`.
Frontend (novos/alterados): `context/SiteConfigContext.js` (SiteConfigProvider + useSiteConfig + resolveLogo; carrega /api/site-config 1x; fallback resiliente), `components/BrandLogo.js` (variantes header/footer/auth/admin/hero; maxWidth=min(logo_width, vw) + maxHeight cap; proporção preservada, sem overflow), `pages/admin/AdminBranding.js` (preview, upload, slider 60–500 c/ preview em tempo real, salvar, restaurar padrão, visualizar no site), `App.js` (SiteConfigProvider + rota admin 'identidade'), `AdminLayout.js` (menu 'Identidade Visual'), Header/Footer/Login/AdminLayout/UnderConstruction agora usam BrandLogo/logo global.
Persistência: UPLOADS_DIR (preview: /app/backend/uploads; VPS: /var/www/brasilminis/uploads via .env.example). Servido em /api/uploads (via backend → funciona atrás do Nginx /api). Deploy (git pull) e reboot NÃO apagam a logo.
Fallback: sem logo_url => usa a logo padrão institucional (/brasil-minis-logo.png).
Testes: backend TestSiteBranding (4 casos) — suíte 50/50 pytest PASS. Frontend E2E (testing_agent): 100% (9/9), 0 issues. Estado final: logo padrão (fallback) + manutenção desativada.
Deploy VPS: criar UPLOADS_DIR persistente e setar no .env; deploy.sh já roda `alembic upgrade head` (aplica 455b5d4bbb3e). Opcional: servir /api/uploads direto pelo Nginx com cache (não obrigatório).
Extensível: coluna branding (JSONB) pronta p/ favicon, logos dark/light, cores, OG, store_name.

---
## Evolução: Categorias hierárquicas + Custo/CMV + Imagens de produto — Junho/2026
Evolução estrutural (stack mantida: FastAPI + SQLAlchemy + PostgreSQL + Alembic + React). Migration Alembic `c1f2a3b4d5e6` (não-destrutiva). Nada de tecnologia migrada, banco não resetado.

### Backend
- **Modelos** (`app/models/__init__.py`): `Category` +parent_id (FK self), is_active, sort_order, created_at, updated_at (hierarquia 2 níveis; group = slug da principal p/ compat). `Product` price/compare_at_price/cost_price → `Numeric(12,2)`, +main_category_id, +subcategory_id, rating→Numeric. Novas tabelas `ProductImage` (source_type url|upload, url, sort_order, is_primary) e `ProductCostHistory` (old_cost/new_cost/changed_by/changed_at). `Order`/`Coupon` monetários → Numeric. CHECK cost_price>=0.
- **Serviços**: `category_service` (árvore, criar/editar/mover/ativar, impede ciclo e >2 níveis), `product_image_service` (Pillow valida MIME real+dimensões+tamanho 8MB, nome UUID sem path traversal, sync do cache `product.images`, add URL/upload/primary/reorder/delete), `order_service` (CMV em Decimal: congela unit_cost_snapshot/unit_price_snapshot/line_revenue/line_cogs/line_gross_profit/has_cost por item), `analytics_service` (períodos hoje/7d/30d/este mês/mês anterior/custom; faturamento, descontos, frete, receita líq., CMV, lucro bruto, margem %, ticket médio, nº pedidos, produtos vendidos; rankings top produtos por faturamento/lucro, top categorias/subcategorias, menor margem, mais vendidos; série faturamento×CMV×lucro; sinaliza itens/produtos sem custo — NUNCA inventa CMV).
- **utils.to_dict**: converte Decimal→float na fronteira JSON. **Público** (`catalog.py`) exclui `cost_price` (PUBLIC_EXCLUDE) em /products, /products/{slug}, /related; `GET /api/categories?tree=true` retorna árvore ativa.
- **Endpoints admin** (`admin.py`): produtos c/ custo+categoria (deriva main/sub/category/group) + histórico de custo em toda alteração; `GET /products/{id}/cost-history`; imagens `GET/POST /products/{id}/images`, `POST .../images/upload`, `PUT .../images/reorder`, `PUT .../images/{img}/primary`, `DELETE .../images/{img}`; categorias `GET /categories/tree`, `POST/PUT/DELETE /categories`, `PUT /categories/reorder`; `GET /admin/analytics?period=&start=&end=`.
- **Uploads**: `UPLOADS_DIR/products` (preview: /app/backend/uploads; VPS: /var/www/brasilminis/uploads) servidos em `/api/uploads/products`. Deploy/reboot preservam. `main.py` cria o subdir no boot.
- **Fix de regressão** (achado pelo testing agent): `coupon_service.resolve_coupon` fazia `float * Decimal` (coupon.value virou Numeric) → 500 em cupom percentual. Corrigido com `float(coupon.value)`.

### Frontend
- `pages/admin/AdminCategories.js` — árvore (principal → subcategorias), criar principal/sub, editar, ativar/desativar, mover subcategoria, contadores de produto.
- `pages/admin/AdminProducts.js` — modal c/ Custo + Categoria principal/Subcategoria (sub filtrada), preview de Lucro/Margem; tabela c/ colunas Custo e Margem ("sem custo" quando NULL); seção Imagens (miniaturas, add URL, enviar arquivo, tornar principal, mover, excluir) disponível ao editar.
- `pages/admin/Dashboard.js` — filtros de período, 8 KPIs, aviso de custo ausente, resultado produtos×frete×descontos, gráfico Faturamento×CMV×Lucro, 6 rankings.

### Testes
- `backend/tests/test_new_features.py` (30 casos) + `backend_test.py` (50 regressão) = 100% PASS. Frontend E2E (testing_agent) 100%. Cobre categorias/ciclos, custo Decimal, custo oculto no público, histórico de custo, snapshot de CMV (custo antigo não recalcula), produto sem custo, dashboard por período, rankings, uploads JPG/PNG/WEBP, MIME/tamanho/path traversal rejeitados, URL+upload coexistem, principal/reorder/delete, regressão checkout/estoque/pedidos/identidade/manutenção/health.
- Preview limpo pós-teste: 28 produtos (26 c/ custo ~55%, 2 sem custo: Gift Card e Mystery Box), 29 categorias (5 principais + 24 sub), 0 pedidos.

### Deploy VPS
- `deploy.sh` já roda `alembic upgrade head` (aplica c1f2a3b4d5e6). Garantir `UPLOADS_DIR=/var/www/brasilminis/uploads` no `.env` e subdir `products` (criado automaticamente pelo backend). Sem create_all, sem reset de banco, sem apagar uploads.

### Backlog remanescente (P1/P2)
- Opcional: trocar `<input type=date>` do período personalizado por shadcn Calendar. Correios/Melhor Envio, Mercado Pago real, histórico de status de pedido (aguardando validação do usuário na VPS).

---
## Melhor Envio — FASE SANDBOX (não ativar produção) — Junho/2026
Integração oficial (OAuth 2.0 + fluxo de envio) construída SOMENTE para Sandbox, com placeholders. Migration Alembic `d2e3f4a5b6c7` (não-destrutiva). Branch alvo: `melhor-envio-sandbox` (salvar via GitHub; NÃO tocar `python-vps`).

### Backend
- **Config** (`core/config.py`): vars `MELHOR_ENVIO_ENV|CLIENT_ID|CLIENT_SECRET|REDIRECT_URI|USER_AGENT_EMAIL|TOKEN_ENCRYPTION_KEY`, `FRONTEND_URL`; `MELHOR_ENVIO_BASE_URL` resolve sandbox/prod dinamicamente; `MELHOR_ENVIO_USER_AGENT` = "Brasil Minis (email)"; `MELHOR_ENVIO_CONFIGURED`.
- **Cripto** (`core/crypto.py`): Fernet; tokens criptografados em repouso.
- **Cliente HTTP** (`services/melhor_envio_client.py`): httpx com timeouts, User-Agent, refresh proativo (margem 60s) + 1 retry único em 401, 5xx/rede → `MelhorEnvioUnavailable` (não derruba a loja), logs sanitizados (sem token/PII/code). OAuth: `exchange_code`, `_refresh`, `api_request`.
- **Serviços**: `auth_service` (auth-url + state CSRF persistido em `melhor_envio_tokens.pending_state`, status, test, disconnect, sender CRUD, exchange_code wrapper); `quote_service` (peso/dimensões/preço SEMPRE do PostgreSQL, valida dados logísticos, CEP; normaliza opções; cotação com validade de 15 min em `shipping_quotes`); `shipment_service` (prepare→cart→checkout→generate→print, idempotente por estado e por `cart_order_id`, ALLOWED_ACTIONS por estado); `tracking_service` (rastreio + timeline, mapeia status externo p/ interno sem perder o original; `apply_external_status` p/ webhook).
- **Modelos/Tabelas novas**: `melhor_envio_tokens`, `melhor_envio_sender`, `melhor_envio_shipments` (1:1 pedido; lifecycle), `shipping_quotes`, `melhor_envio_webhook_events`. Produto +`weight_kg/width_cm/height_cm/length_cm/sku/barcode`. Pedido + snapshot de frete congelado (`shipping_provider/service_id/service_name/company_id/company_name/price_customer/price_quoted/delivery_min/max/destination_postal_code/quote_snapshot`) + `recipient_snapshot`.
- **Pedido** (`order_service`): se cotação selecionada, congela snapshot; frete grátis preservado (cliente paga 0, mas custo real cotado é registrado); cria `MelhorEnvioShipment` (pending). Sem cotação → regra de frete padrão (compat).
- **Rotas** (`routers/melhor_envio.py`): admin `GET /api/admin/melhor-envio/{status,auth-url}`, `POST .../{test,disconnect}`, `GET/PUT .../sender`; callback público `GET /api/admin/melhor-envio/callback` (valida state, redireciona ao front); `POST /api/shipping/quote` (cliente/visitante); ações admin por pedido `.../shipment/{prepare,cart,checkout,generate}` + `GET .../shipment[/print]` + `POST .../shipment/tracking`; webhook `POST /api/webhooks/melhor-envio` (HMAC-SHA256 hex/base64 + dedup por hash). `/api/health` inclui `melhor_envio` como OPCIONAL (nunca vira 503).

### Frontend
- Nova página `pages/admin/AdminMelhorEnvio.js` (badge SANDBOX, status, Conectar/Testar/Reconectar/Desconectar, form de remetente). Rota `/admin/melhor-envio` + item no menu.
- `Checkout.js`: card "Frete" com "Calcular frete" (POST /shipping/quote), lista de opções (transportadora/serviço/prazo/preço), seleção, total; campos CPF/CNPJ e telefone do destinatário; envia `quote_id/shipping_service_id/recipient_document/recipient_phone`; erros amigáveis (indisponível/CEP) sem quebrar a loja.
- `AdminOrders.js`: painel de logística por pedido (transportadora, valor cliente vs custo real, prazo, CEP, status interno/externo, tracking, shipment id) + ações por estado + timeline.
- `AdminProducts.js`: seção "Dados logísticos" (peso/largura/altura/comprimento/SKU/barcode) + alerta "Dados de frete incompletos".

### Testes
- `tests/test_melhor_envio.py` (13 mockados via respx, sem internet): auth-url/state, exchange (token criptografado), refresh em token expirado, 401→1 retry, API fora→unavailable, cotação (normalização/CEP inválido/sem dimensões/API fora/expiração), idempotência de carrinho, fluxo completo cart→checkout→generate→print→tracking, print antes de generate bloqueado. **13/13 PASS**.
- Regressão HTTP: `backend_test.py` + `test_new_features.py` **79+/80 PASS** (1 falha foi timeout de rede flaky; passou no rerun). Frontend (testing_agent) **100%**, sem bugs.
- Segurança: cost_price e tokens/segredos NUNCA no frontend; RBAC admin nos endpoints; state CSRF; HMAC no webhook.

### Deploy (pendente com o usuário)
- Cadastrar app Sandbox e a redirect URI exata; preencher `MELHOR_ENVIO_*` no `.env`; rodar `alembic upgrade head`. Produção NÃO ativada. Salvar em branch `melhor-envio-sandbox`.

---
## Mercado Pago (TESTE) + CEP automático — Junho/2026
Migration `e4f5a6b7c8d9` (não-destrutiva). Branch alvo: `mercado-pago-gateway`. Produção BLOQUEADA (backend recusa `environment=production`).

### Backend (completo e testado)
- **CEP** (`services/cep_service.py`, `GET /api/cep/{cep}`): BrasilAPI + fallback ViaCEP → {street, district, city, uf}; erros amigáveis.
- **Mercado Pago** (`services/mercado_pago_service.py`, Orders API `/v1/orders`): settings CRUD (Access Token cifrado Fernet com `MERCADO_PAGO_TOKEN_ENCRYPTION_KEY` do .env — nunca no painel/logs/frontend; só máscara `••••••`), test_connection, disconnect; PIX (QR/qr_base64/copia-e-cola/expiração, valor SEMPRE do backend), Cartão (token do Brick + parcelas + método + emissor; sem PAN/CVV no backend), `X-Idempotency-Key` (clique duplo não duplica), status mapping preservando `status`/`status_detail` originais, snapshot no pedido (payment_provider/external_id/mp_id/status/status_detail/status_raw/amount/created_at/approved_at/idempotency_key), auditoria (`payment_audit_logs`), webhook `POST /api/webhooks/mercado-pago` (HMAC x-signature + dedup `mp_webhook_events`, confirma via GET da Order — nunca confia só no webhook).
- `/api/health` inclui `mercado_pago` (opcional, nunca vira 503). Chave Fernet MP em `backend/.env`.
- **Tabelas novas**: `mp_settings`, `mp_webhook_events`, `payment_audit_logs`. Pedido +9 colunas de pagamento.

### Frontend
- Admin → **Mercado Pago** (`AdminMercadoPago.js`): badge TEST, status, Public Key/Access Token (mascarado)/Webhook Secret, Salvar/Testar/Desconectar, aviso de criptografia. Rota + nav.
- **CEP automático** (`lib/cep.js`): máscara 00000-000 + debounce 500ms; aplicado no Checkout (endereço do cliente) e no Remetente (Admin Melhor Envio) — preenche rua/bairro/cidade/UF, mantém número/complemento, silencioso se falhar.
- Checkout: campos CPF/CNPJ e telefone do destinatário (para Melhor Envio) já presentes.

### Testes
- `tests/test_mercado_pago.py` (8 mockados via respx): cifra do token/não vaza, produção bloqueada, PIX usa valor do backend, PIX idempotente, cartão aprovado, webhook HMAC válido/inválido, webhook dedup + aprovação, status mapping. **8/8 PASS**. Regressão (melhor_envio 13 + TestOrders + TestCatalog) verde. Corrigido bug real: `save_settings` não persistia a linha nova.

### PENDENTE (frontend checkout de pagamento)
- Backend PIX/cartão prontos e testados, mas a UI de pagamento DENTRO do checkout (exibir QR PIX / Card Payment Brick) ainda NÃO foi integrada — o checkout atual segue com pagamento simulado. Próximo passo: renderizar QR/Brick após criar o pedido quando o MP estiver configurado.

### Infra (variáveis)
- `MERCADO_PAGO_TOKEN_ENCRYPTION_KEY` (Fernet, só backend/.env), `MERCADO_PAGO_API_BASE=https://api.mercadopago.com`. Credenciais (Public Key/Access Token/Webhook Secret) via painel Admin. Não fazer deploy; salvar em `mercado-pago-gateway`.


---

## Central de Integrações + Checkout Real (Jun/2026) — branch `integrations-production-ready`

### Entregue
- **Central de Integrações** `/admin/integracoes` (`AdminIntegracoes.js`): cards unificados MP + Melhor Envio com badge de ambiente, status, seletor de ambiente (com `window.confirm`), campos de credenciais (secret/token em `type=password`, mascarados), Salvar/Testar/Conectar/Desconectar, botão "Ativar produção" (gating) e dica visual. Item de menu "Integrações" no `AdminLayout`.
- **Credenciais no banco (cifradas)**: Melhor Envio agora guarda `client_id`, `client_secret_enc` (Fernet), `redirect_uri` na tabela `melhor_envio_tokens` (migration `f5a6b7c8d9e0`). `.env` só tem chaves Fernet/infra. Endpoints `GET/PUT /api/admin/melhor-envio/credentials`. `get_config(db)` com fallback legado ao `.env`.
- **Troca de ambiente com isolamento**: ME (sandbox↔production) e MP (test↔production) desassociam tokens/sessão anteriores. MP limpa public_key/access_token e desativa.
- **Produção protegida (MP)**: `save_settings` nunca ativa produção; `POST /api/admin/mercado-pago/activate {confirm}` exige status=connected (teste prévio) + confirmação explícita. `_access_token` não bloqueia mais produção.
- **Scopes OAuth Melhor Envio** corrigidos: removidos `shipping-cancel` e `shipping-tracking`. Restam os 6 válidos.
- **Checkout REAL** (`Checkout.js` + `components/checkout/MercadoPagoPayment.js`): quando MP ativo, `create_order` cria pedido `aguardando_pagamento` e a UI mostra passo de pagamento — PIX (QR base64 + copia-e-cola + polling de status) ou Cartão via **Card Payment Brick** (`@mercadopago/sdk-react`). Boleto oculto quando MP ativo. Sem MP ativo, mantém fluxo SIMULADO.
- `GET /api/mercado-pago/public-key` agora retorna `enabled`. `GET /api/admin/integrations` (visão unificada).
- Doc: `/app/backend/INTEGRATIONS.md` (variáveis .env + passos de produção).

### Testes
- `tests/test_mercado_pago.py` + `tests/test_melhor_envio.py`: **26/26 PASS** (cifragem, gating de produção, troca de ambiente, dedup/HMAC webhook, scopes). Regressão `test_new_features.py` + `backend_test.py`: **80 PASS**. Testing agent (iteration_7): backend 10/10 + frontend 100%, sem bugs.
- **Limitação**: preview sem credenciais reais do MP (DB efêmero) → PIX/cartão/webhook validados via mocks (respx), não contra a API real.

### Deploy
- NÃO deployado. Usar "Save to Github" para a branch `integrations-production-ready`. Migration head: `f5a6b7c8d9e0`.

---

## Categorias públicas 100% controladas pelo Admin (Jun/2026) — branch `fix-public-category-tree`

### Entregue
- **Menu superior dinâmico** (`Header.js`): categorias principais vêm de `/api/categories?tree=true` (parent_id null, is_active, sort_order). Dropdown de subcategorias no hover (desktop) e acordeão touch (mobile). Institucionais fixos e separados: Início, Lançamentos, Promoções, Marcas, Contato. Criar/renomear/desativar/reordenar categoria no Admin reflete automaticamente no site.
- **Contexto reutilizável** (`context/CategoriesContext.js`): fetch ÚNICO da árvore, compartilhado por Header/Catálogo/mobile. Helper `findCategoryTrail` (principal>sub).
- **Backend `_category_filter`** (`catalog.py`): `?category=<principal>` → produtos com `main_category_id` dela OU `subcategory_id` das subcategorias (+ fallback legado `Product.category`/`group`); `?category=<sub>` → só `subcategory_id` dela. Validado: hotwheels→2, mainline→1, elite-64→0.
- **Catálogo** (`Catalog.js`): sidebar em accordion SEM `max-h-64 overflow-y-auto`; principal clicável + seta expandir + subcategorias; auto-expande o pai da subcategoria ativa. Botão "Todas" limpa só `category` preservando marca/promoção/ordenação. Breadcrumb + título dinâmicos (PRINCIPAL > SUB). URL `/produtos?category=<slug>` persiste no refresh e por link direto.

### Testes (iteration_8) — 100%, sem bugs
- Backend 5/5 filtros + árvore ordenada/is_active. Frontend desktop (dropdown, breadcrumb, accordion, "Todas" preserva filtros, refresh) + mobile (acordeão) + regressão (cart/checkout/produto/admin). Corrigido testid duplicado `catalog-title`.
- Dados de teste criados no preview: Hot Wheels (subs mainline/premium-hw/elite-64/fast-furious), Matchbox, Majorette; produtos TESTE (hotwheels/mainline) e HW DIRETO (hotwheels).

### Não deployado
- Trabalho no preview; salvar via "Save to Github" na branch `fix-public-category-tree`.


---

## Conteúdo institucional + Redes sociais + CEP no cadastro (Jun/2026) — branch `site-content-and-customer-address`

### Entregue
- **CEP automático no cadastro** (`Register.js`): seção de endereço opcional com autofill (logradouro/bairro/cidade/UF) via `GET /api/cep/{cep}`; número obrigatório quando há endereço, complemento opcional (nenhum autopreenchido); loading discreto e erro amigável; não bloqueia o cadastro se o CEP falhar (endereço salvo via `POST /account/addresses` após registrar, com aviso se falhar). Mesmo helper `useCepAutofill` (agora com `onStart/onError`) reutilizado no formulário de endereços da conta (`Account.js`), checkout e remetente ME.
- **Páginas institucionais configuráveis** (Sobre, Contato, Trocas e Devoluções, Frete e Entrega): `site_settings.institutional_content` (JSONB). Cada página: título, subtítulo, conteúdo Markdown sanitizado (bleach — remove script/iframe/js), ativo/inativo, SEO title/description. Contato tem campos estruturados (email, telefone, whatsapp, horário, endereço, mapa). Rotas públicas `/sobre`, `/trocas-devolucoes`, `/frete-entrega`, `/contato` consomem do banco via `useSiteContent` + `MarkdownContent` (react-markdown, sem HTML bruto). Nada hardcoded no React (defaults moram no service).
- **Redes sociais configuráveis** (`social_links` JSONB): Instagram, Facebook, TikTok, YouTube, WhatsApp, Telegram, X/Twitter, Pinterest — cada uma com URL + ativo. Público (`GET /api/site-content` e `/api/site-config`) expõe só as ativas com URL. Footer e Contato renderizam via `SocialLinks` (target=_blank rel=noopener). WhatsApp aceita URL completa ou número (gera `wa.me/<digitos>`).
- **Admin** (`AdminContent.js`, rota `/admin/conteudo`, menu "Conteúdo do Site"): abas por página + aba Redes Sociais, toggle ativo, botão "Visualizar página", "Salvar alterações". RBAC: só admin altera (`get_current_admin`); público só leitura.
- **Endpoints**: `GET /api/site-content` (público), `GET/PUT /api/admin/site-content`, `GET/PUT /api/admin/social-links`. `site-config` agora inclui `social_links`.
- **Migration** `a1b2c3d4e5f6` (não-destrutiva): adiciona `institutional_content` e `social_links` (JSONB) em `site_settings`.

### Testes (iteration_9) — 100%, sem bugs
- Backend 11/11 (`tests/test_site_content.py`): shape público, RBAC 401, sanitização XSS, URL javascript/sem-scheme → 400, página inativa some do público, rede vazia normalizada, CEP válido/inválido. Frontend: institucionais + contato (só campos preenchidos) + CEP no cadastro (número/complemento preservados, erro amigável) + Admin→público sem redeploy + redes sociais no footer/contato. Aplicadas melhorias: testids ASCII no Contato, aviso ao falhar endereço no cadastro, WhatsApp por número.

### Não deployado
- Preview apenas; salvar via "Save to Github" na branch `site-content-and-customer-address`. Migration head: `a1b2c3d4e5f6`. Nova dep backend: `bleach`; frontend: `react-markdown`.


---

## Checkout endereço + Cupons de desconto + Exclusão protegida + Brasil Minis® (Jun/2026) — branch `checkout-order-admin-improvements`

### Entregue
- **Checkout endereço**: carrega endereço cadastrado (default > mais recente) via `/account/addresses`; toggle "Entregar em outro endereço" com form editável + CEP autofill; checkbox "Salvar este endereço na minha conta" (só persiste se marcado — nunca sobrescreve o cadastro). Snapshot final congelado em `order.recipient_snapshot` (Melhor Envio usa o endereço final). 
- **Cupons de desconto** (`Coupon` estendido + `CouponRedemption`): % ou fixo, valor mínimo, desconto máximo, início/expiração, limite total e por cliente, ativo/inativo, primeira compra, frete grátis, escopo all/categorias/produtos, flag cumulativo. Admin CRUD em `/admin/cupons` (código manual ou gerado). Checkout aplica via `POST /api/coupons/preview` (cálculo 100% no servidor), mostra/remove, recalcula total. Pedido congela `coupon_snapshot` e registra uso (`used_count`+redemption) atômico.
- **Exclusão protegida de pedidos**: soft delete (`deleted_at/deleted_by/delete_reason/stock_returned`); `DELETE /api/admin/orders/{id}` exige `reason` + `confirm=="EXCLUIR"`; bloqueia (409) se MP `approved` ou envio ME comprometido (in_cart/purchased/generated/posted/delivered); devolve estoque exatamente 1x (idempotente); auditoria `AdminAuditLog` (REQUESTED/BLOCKED/DELETED). Admin: filtro Ativos/Excluídos/Todos + modal de confirmação. Cliente não vê pedidos excluídos.
- **Brasil Minis®**: ® discreto (sup) no Header (logo), Footer (marca + copyright) e títulos; logo original preservada.
- **Migration** `b2c3d4e5f6a7` (não-destrutiva). Seed FRETEGRATIS corrigido para `free_shipping=True`.

### Testes (iteration_10): backend 20/21 (1 skipped) + frontend 100%
- `tests/test_coupons_and_delete.py`: preview auth/cálculo, snapshot+used_count, limites (inativo/expirado/usage/per-user/1ª compra), escopo, frete grátis, CRUD RBAC, exclusão (confirm/reason/soft/estoque 1x/idempotência/scope/MP-block 409/RBAC 403). Frontend: endereço, cupom aplicar/remover, modal exclusão gating, ® Header/Footer. Corrigidos: seed FRETEGRATIS + warning React key (AdminOrders).
- Preservados (regressão OK): páginas institucionais, redes sociais, catálogo/categorias, MP, Melhor Envio, Admin.

### Não deployado — branch `checkout-order-admin-improvements`. Head: `b2c3d4e5f6a7`.


---

## CPF no cadastro de cliente (Jun/2026) — mesmo pacote `checkout-order-admin-improvements`

### Entregue
- **CPF obrigatório no cadastro** (`RegisterInput.cpf`), com máscara `000.000.000-00` no frontend, armazenado **normalizado** (11 dígitos) em `users.cpf` (único, nullable). Validação **matemática** dos dígitos verificadores (`app/core/cpf.py`), rejeita repetidos e formato só por tamanho.
- **Unicidade** (DB unique + checagem no endpoint) com mensagens amigáveis; **PII-safe** (nunca loga/expõe o CPF nas mensagens).
- **Legados sem CPF continuam funcionando** (cpf NULL); podem adicionar depois em `/conta` (dica "complete seu cadastro"). `PUT /api/account/profile` aceita cpf com validação/unicidade.
- **Admin**: coluna CPF em `/admin/clientes` + `PUT /api/admin/customers/{id}` para visualizar/editar (RBAC).
- **Checkout**: campo CPF/CNPJ do destinatário **pré-preenchido** com o CPF do cadastro; editar/alternar endereço **não** altera o CPF da conta.
- **Migration** não-destrutiva `c3d4e5f6a7b8` (coluna cpf + índice único).
- Auth JWT/bcrypt **preservada** (nenhuma mudança em hashing/tokens; playbook do integration_expert seguido).

### Testes (iteration_11): backend 16/16 + frontend 100%, sem bugs
- `tests/test_cpf.py`: register (válido/inválido/ausente/duplicado com máscara), normalização, PII, profile (legado adiciona depois), admin edit + RBAC, legado sem CPF funcionando. Frontend: máscara no cadastro, `/conta`, `/admin/clientes` (modal), prefill no checkout.
- Sem regressão no pacote anterior (checkout/cupons/exclusão/®).

### Não deployado — branch `checkout-order-admin-improvements`. Head: `c3d4e5f6a7b8`.


---

## CONSOLIDAÇÃO FINAL + AUDITORIA (12/Jun/2026) — branch alvo `production-improvements-sep2026`

### Objetivo
Consolidar em UMA branch final todos os pacotes A–F (institucional/CEP/redes, checkout+endereço, cupons de desconto, exclusão protegida, CPF, Brasil Minis®), baseada na `python-vps` mais recente, SEM regressão e SEM deploy.

### Achado principal
Nenhuma alteração de CÓDIGO DE APLICAÇÃO foi necessária: todos os recursos A–F já estavam implementados e o comportamento é idêntico ao já testado (iteration_11). Esta sessão fez apenas: (1) atualização dos testes backend antigos para o novo contrato de CPF obrigatório + fixtures determinísticas de estoque; (2) limpeza de `.gitignore` (artefatos de teste e uploads runtime fora do VCS).

### Resultado da auditoria (PREVIEW, sem deploy)
- **Alembic**: 1 único head `c3d4e5f6a7b8`; cadeia linear válida base→head (10 migrations). As três exigidas (`a1b2c3d4e5f6` → `b2c3d4e5f6a7` → `c3d4e5f6a7b8`) estão no topo, sem múltiplos heads.
- **/api/health**: `status ok`, `database ok`, `migration current`.
- **Backend pytest**: 163 passed, 1 skipped, 0 failed (rodado via HTTPS do preview).
- **Frontend**: `yarn build` sem erros; home renderiza com Brasil Minis® e menu dinâmico de categorias.
- **Segurança**: nenhum secret/token commitado; `.env` não rastreado; credenciais operacionais (MP/ME) em DB (Fernet).
- **Artefatos**: `test_reports/*.json` e `pytest/*.xml` removidos do rastreio; `backend/uploads/` ignorado (conteúdo runtime).
- **Preservados (verificados em código + smoke)**: árvore dinâmica de categorias/subcategorias, CategoriesContext, dropdown/acordeão, Central de Integrações, Mercado Pago (payments.py), Melhor Envio (melhor_envio.py), checkout real, estoque, catálogo, auth JWT/bcrypt, Admin.

### Observações (dados de preview, NÃO afetam código/produção)
- Menu público mostra categorias "TEST MAIN..." e produtos "TEST ..." criados pelas suítes de teste no DB compartilhado do preview. Não existem no código nem na produção (python-vps tem seu próprio DB).
- `frontend/yarn.lock` não é rastreado (estado pré-existente do main); build funciona normalmente.

### Git — como salvar na branch final (NÃO feito automaticamente)
O pod não tem remoto; criar/baserar branch em `python-vps` é feito via "Save to Github":
1. No GitHub: criar `production-improvements-sep2026` a partir de `python-vps` (última versão).
2. No Emergent: botão Save → Save to Github → selecionar a branch → push.
3. No GitHub: abrir PR `production-improvements-sep2026` → `python-vps`, revisar diff, mergear.

### NENHUM DEPLOY realizado. NENHUM dado real de produção alterado.

---

## Exclusão protegida de CLIENTES + Zeragem do Dashboard (13/Jun/2026)

### Entregue (backend + frontend + testes)
- **Exclusão protegida de clientes (soft delete)**: Admin → Clientes com escopos Ativos/Excluídos/Todos. Modal exige motivo + digitar `EXCLUIR`; botão só habilita após confirmação correta. RBAC admin (cliente comum → 403). Idempotente (excluir 2x não duplica). Auditoria `CUSTOMER_DELETE_REQUESTED`/`CUSTOMER_DELETED` (CPF nunca exposto — só `cpf_tail`). Cliente excluído **não loga** (login 403; sessão existente 401). Pedidos/pagamentos/envios/cupons **preservados** (nada apagado fisicamente).
- **Anonimização LGPD (opcional)**: checkbox no modal — apaga nome/e-mail/CPF/telefone/endereços e **libera e-mail/CPF para novo cadastro**; histórico operacional mantido via snapshots do pedido.
- **Restauração**: aba Excluídos → "Restaurar" (admin only), auditoria `CUSTOMER_RESTORED`, valida conflito de e-mail/CPF com cliente ativo (409 amigável, sem alterar dados).
- **Zeragem do Dashboard (baseline)**: Admin → Dashboard → "Controle dos indicadores" → "Zerar Dashboard". Modal exige motivo + digitar `ZERAR DASHBOARD`. **Não apaga nada** — grava marco em `dashboard_resets`. KPIs dos períodos padrão passam a contar só após o marco (cards iniciam em zero); período **Personalizado** ainda acessa histórico. Auditoria `DASHBOARD_RESET_REQUESTED`/`DASHBOARD_RESET_COMPLETED` (baseline anterior + novo). **Histórico de zeragens** listado (não apagável pela UI).

### Arquivos
- Backend: `services/customer_admin_service.py` (novo), `services/dashboard_service.py` (novo), `routers/admin.py`, `routers/auth.py`, `dependencies/__init__.py`, `services/analytics_service.py`, `models/__init__.py` (User soft-delete + `DashboardReset`), `schemas/__init__.py`.
- Frontend: `pages/admin/AdminCustomers.js`, `pages/admin/Dashboard.js`.
- Migration: `d4e5f6a7b8c9_customer_soft_delete_dashboard.py` (não-destrutiva) — down_revision `c3d4e5f6a7b8`.

### Endpoints
- `GET /api/admin/customers?scope=active|deleted|all`
- `DELETE /api/admin/customers/{id}` body `{reason, confirm:"EXCLUIR", anonymize?}`
- `POST /api/admin/customers/{id}/restore`
- `GET /api/admin/dashboard/baseline` · `POST /api/admin/dashboard/reset` body `{reason, confirm:"ZERAR DASHBOARD"}`
- `/api/admin/stats` e `/api/admin/analytics` respeitam o baseline (custom = histórico).

### Testes: backend 18/18 (novo) e suíte completa 182/182; frontend E2E 100% (iteration_12). Alembic head único `d4e5f6a7b8c9`. NENHUM deploy.

---

## Catálogo/Categorias/Badges/Galeria (13/Jun/2026)

### Entregue
- **Home dinâmica**: cards de Categorias vêm de `GET /api/home-categories` (árvore do Admin). Sem hardcode. Numeração automática 01,02.. pela ordem; contagem de produtos ATIVOS por nó. Nós aparecem só com `is_active=true` E `show_on_home=true`. Card → `/produtos?category=<slug>`.
- **Categoria**: campos novos `icon`, `show_on_home`, `featured` (categoria e subcategoria) no modal do Admin. `build_tree` agora conta apenas produtos ATIVOS (subcategoria = seus produtos; raiz = próprios + filhos, sem duplicar).
- **Badges administráveis**: tabela `badges` (texto, bg_color, text_color, icon, priority, sort_order, active). Admin → Badges (CRUD + preview). Exclusão bloqueada se em uso (desativar disponível). Associação ao produto mantida em `Product.badges` (JSONB). Produto: seleção múltipla a partir do catálogo. Storefront estiliza via `BadgesContext`/`GET /api/badges` (fallback padrão).
- **Ver produtos (Admin)**: `GET /api/admin/catalog/products?category&search&active&stock&sort&page&limit` + modal na árvore de categorias (busca/filtro/ordenação/paginação).
- **Galeria avançada**: `components/Lightbox.js` — zoom (+/-/roda/duplo clique/0 reset), arrastar quando ampliado, ← → trocar, Esc fechar, miniaturas, contador (oculto com 1 imagem), swipe mobile, foco no diálogo + restauração, aria-labels, lazy loading. 1 imagem: sem setas/contador, zoom disponível.

### Migration
- `e5f6a7b8c9d0` (aditiva): categories.icon/show_on_home/featured + tabela badges. Head único. Não-destrutiva.

### Endpoints
- Público: `GET /api/home-categories`, `GET /api/badges`.
- Admin: `GET/POST /api/admin/badges`, `PUT/DELETE /api/admin/badges/{id}`, `GET /api/admin/catalog/products`.

### Arquivos
- Backend: models, schemas, `services/badge_service.py` (novo), `services/category_service.py`, `routers/catalog.py`, `routers/admin.py`, migration.
- Frontend: `context/BadgesContext.js` (novo), `components/Lightbox.js` (novo), `pages/admin/AdminBadges.js` (novo), `Home.js`, `components/ProductCard.js`, `pages/ProductDetail.js`, `pages/admin/AdminCategories.js`, `pages/admin/AdminProducts.js`, `App.js`, `pages/admin/AdminLayout.js`.

### Testes: backend `test_catalog_badges_home.py` 9/9 + suíte completa 191/191; frontend E2E ~95% (iteration_13), 2 itens de código corrigidos (Lightbox). Build OK. NENHUM deploy.
