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
