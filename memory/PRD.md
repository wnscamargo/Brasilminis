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
