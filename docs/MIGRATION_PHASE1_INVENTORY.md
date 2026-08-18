# Brasil Minis — Fase 1: Inventário e Plano de Migração (FastAPI/React/Mongo → Laravel 12/Blade/MySQL)

> Documento de análise. **Nenhuma reescrita foi iniciada.** O projeto React/FastAPI atual permanece intacto como referência até a homologação do Laravel.

---

## 0. Aviso de ambiente (importante)

Este preview roda em Kubernetes preparado para **React + FastAPI + MongoDB**. Ele **não executa PHP 8.3 / Laravel / MySQL**. Consequências práticas:

- Posso **gerar 100% do código Laravel** (estrutura, migrations, models, controllers, services, Blade, Livewire, seeders, testes Pest, GitHub Actions, `.htaccess`, scripts de deploy) como um projeto completo e versionável.
- **Não conseguirei rodar `php artisan` nem os testes Pest aqui.** A validação (migrate, serve, testes) será feita por você localmente ou via GitHub Actions.
- Portanto o Laravel será entregue como **novo diretório** (ex.: `/app/laravel/`) para você commitar no GitHub e publicar na Locaweb.

Decisão necessária (ver final do documento) antes de começar a Fase 2.

---

## 1. Mapa do sistema atual (ATUAL → NOVO)

### 1.1 Backend — Rotas FastAPI → Controllers Laravel

| ATUAL (FastAPI, prefixo `/api`) | Método | Descrição | NOVO (Laravel) |
|---|---|---|---|
| `/api/auth/register` | POST | Cadastro + cookies JWT | `AuthController@register` (web, sessão) |
| `/api/auth/login` | POST | Login + brute-force lockout | `AuthController@login` |
| `/api/auth/logout` | POST | Logout | `AuthController@logout` |
| `/api/auth/me` | GET | Usuário atual | `Auth::user()` / `AccountController@me` |
| `/api/auth/refresh` | POST | Renova access token | (N/A — sessão Laravel) |
| `/api/auth/forgot-password` | POST | Gera token reset | `PasswordResetController@sendLink` |
| `/api/auth/reset-password` | POST | Redefine senha | `PasswordResetController@reset` |
| `/api/categories` (+`?group=`) | GET | Lista categorias | `CategoryController@index` |
| `/api/categories/{slug}` | GET | Categoria por slug | `CategoryController@show` |
| `/api/brands`, `/api/brands/{slug}` | GET | Marcas | `BrandController` |
| `/api/products` (filtros: category, group, brand, badge, search, featured, on_sale, sort, page, limit) | GET | Catálogo paginado | `ProductController@index` (Eloquent + scopes) |
| `/api/products/{slug}` | GET | Detalhe do produto | `ProductController@show` |
| `/api/products/{slug}/related` | GET | Relacionados | `ProductController@related` |
| `/api/products/{id}/reviews` | GET/POST | Avaliações | `ReviewController@index/store` |
| `/api/favorites` | GET | Favoritos do usuário | `FavoriteController@index` |
| `/api/favorites/{product_id}` | POST/DELETE | Add/remove favorito | `FavoriteController@store/destroy` |
| `/api/coupons/validate` | POST | Valida cupom | `CouponController@validate` |
| `/api/orders` | POST/GET | Cria pedido / meus pedidos | `OrderController@store/index` |
| `/api/orders/{id}` | GET | Detalhe do pedido | `OrderController@show` |
| `/api/account/profile` | PUT | Atualiza perfil | `AccountController@updateProfile` |
| `/api/account/password` | PUT | Troca senha | `AccountController@updatePassword` |
| `/api/account/addresses` | GET/POST | Endereços | `AddressController@index/store` |
| `/api/account/addresses/{id}` | DELETE | Remove endereço | `AddressController@destroy` |
| `/api/banners` | GET | Banners ativos | `BannerController@index` |
| `/api/admin/stats` | GET | Dashboard | `Admin\DashboardController@index` |
| `/api/admin/products` | GET/POST | Lista/cria produto | `Admin\ProductController` |
| `/api/admin/products/{id}` | PUT/DELETE | Edita/remove | `Admin\ProductController@update/destroy` |
| `/api/admin/categories` | POST | Cria categoria | `Admin\CategoryController` |
| `/api/admin/categories/{id}` | PUT/DELETE | Edita/remove | idem |
| `/api/admin/brands`, `/{id}` | POST/PUT/DELETE | Marcas | `Admin\BrandController` |
| `/api/admin/orders` | GET | Todos pedidos | `Admin\OrderController@index` |
| `/api/admin/orders/{id}/status` | PUT | Muda status | `Admin\OrderController@updateStatus` |
| `/api/admin/customers` | GET | Clientes | `Admin\CustomerController@index` |
| `/api/admin/banners`, `/{id}` | GET/POST/PUT/DELETE | Banners | `Admin\BannerController` |

**Auth**: hoje JWT via cookies httpOnly (`access_token`/`refresh_token`), lockout 5 tentativas / 15 min, `seed_admin` no startup. → NOVO: **sessão nativa Laravel + Fortify/Breeze**, CSRF, `RateLimiter`, `throttle`, `AdminMiddleware` (Gate/Policy por `role`).

### 1.2 Modelos MongoDB → Tabelas MySQL

Coleções atuais: `users, products, categories, brands, orders, favorites, reviews, banners, coupons, login_attempts, password_reset_tokens`.

Campos-chave hoje:
- **product**: id(uuid), name, slug, description, price, compare_at_price, category(slug), group, brand(slug), images[], stock, badges[], specs{}, rating, reviews_count, featured, is_active, created_at.
- **order**: id, order_number(BMxxxxxx), user_id, user_name/email, items[{product_id,name,slug,image,price,quantity,line_total}], subtotal, discount, coupon, shipping, shipping_method, total, payment_method, payment_status, status, address{}, created_at.
- **coupon**: code, type(percent|fixed), value, min_order, active, description.
- **user**: name, email, password_hash, role(customer|admin), phone, newsletter, addresses[], created_at.
- **banner**: title, subtitle, image, cta_text, cta_link, position, active.

### 1.3 Frontend React → Blade/Livewire

| Rota React | Página | NOVO (Blade view + Livewire) |
|---|---|---|
| `/` | Home (hero, destaques, lançamentos, promoções, categorias, marcas, newsletter) | `home.blade.php` |
| `/produtos`, `/grupo/:group` | Catálogo (filtros, ordenação, busca, paginação) | `catalog.blade.php` + `Livewire\ProductCatalog` |
| `/produto/:slug` | Detalhe (galeria, specs, reviews, relacionados, favoritar, comprar) | `product/show.blade.php` + `Livewire\ProductViewer` |
| `/carrinho` | Carrinho | `cart.blade.php` + `Livewire\Cart` |
| `/checkout` | Checkout single-page (endereço, pagamento, cupom) | `checkout.blade.php` + `Livewire\Checkout` |
| `/favoritos` | Favoritos | `favorites.blade.php` + `Livewire\Favorites` |
| `/conta` | Minha conta (pedidos, endereços, dados, senha) | `account/*.blade.php` |
| `/login`, `/cadastro`, `/recuperar-senha`, `/reset-password` | Auth | Fortify/Breeze views customizadas |
| `/marcas`, `/contato` | Institucional | `brands.blade.php`, `contact.blade.php` |
| `/admin/*` | Painel (dashboard, produtos, categorias, marcas, pedidos, clientes, banners) | `admin/*.blade.php` + Livewire components |

Contextos React (`AuthContext`, `CartContext`, `FavoritesContext`) → Sessão Laravel + Livewire state. Carrinho: sessão para visitante, tabela `carts/cart_items` para logado.

### 1.4 Regras de negócio a preservar

- Frete grátis quando `(subtotal - desconto) >= R$300`, senão `R$29,90`.
- Cupom `percent` ou `fixed`, respeitando `min_order`; desconto nunca maior que o subtotal.
- Baixa de estoque ao confirmar pedido (migrar para **transação + `lockForUpdate`** para evitar oversell).
- Número de pedido `BM######`.
- Badges: NOVO, LANÇAMENTO, PROMOÇÃO, TREASURE HUNT, SUPER TH, PREMIUM, EDIÇÃO LIMITADA, PRÉ-VENDA, FRETE GRÁTIS.
- Grupos: miniaturas, colecionaveis, acessorios, vestuario, presentes.
- Pagamento **SIMULADO** (mock), arquitetura pronta p/ Mercado Pago (PIX/cartão/boleto/webhook).
- Recálculo de `rating`/`reviews_count` ao inserir avaliação.

---

## 2. Esquema MySQL 8 proposto (normalizado)

Tabelas (com `legacy_id` VARCHAR nullable p/ rastrear o id UUID do Mongo):

- **users** (id, name, email unq, email_verified_at, password, role enum[client,admin], phone, newsletter bool, remember_token, timestamps)
- **addresses** (id, user_id fk, label, recipient, street, number, complement, district, city, state, zip, is_default, timestamps)
- **categories** (id, name, slug unq, group enum, description, image, timestamps)
- **brands** (id, name, slug unq, logo, description, timestamps)  ← marcas de miniaturas (Hot Wheels…)
- **manufacturers** (id, name, slug unq)  ← fabricante (opcional; separa "marca do veículo" de "fabricante da miniatura")
- **products** (id, name, slug unq, sku unq null, barcode null, description, group enum, category_id fk, brand_id fk null, manufacturer_id fk null, price decimal(10,2), compare_at_price decimal null, stock int, featured bool, is_active bool, rating decimal(2,1), reviews_count int, meta_title, meta_description, legacy_id, timestamps) + índices (slug, sku, category_id, brand_id, is_active, featured)
- **product_images** (id, product_id fk, path, position)
- **product_attributes** (id, product_id fk, key, value)  ← escala, ano, cor, material, código fabricante, TH/STH/Chase, dimensões, compatibilidade, tecido, etc. (EAV leve; comum aos 3 grupos)
- **product_variants** (id, product_id fk, sku, size, color, fabric, price_override null, stock int)  ← vestuário/variações
- **badges** (id, code, label) + **product_badge** (pivot) — ou coluna JSON `badges` para MVP
- **favorites** (id, user_id fk, product_id fk, unique[user_id,product_id])
- **carts** (id, user_id fk null, session_id null, timestamps) + **cart_items** (id, cart_id fk, product_id fk, variant_id null, quantity, price)
- **coupons** (id, code unq, type enum[percent,fixed], value decimal, min_order decimal, active bool, starts_at null, ends_at null)
- **orders** (id, order_number unq, user_id fk, status enum, payment_method enum, payment_status enum, subtotal, discount, shipping, total, coupon_code null, shipping_method, address_json, legacy_id, timestamps)
- **order_items** (id, order_id fk, product_id fk null, variant_id null, name, image, price, quantity, line_total)
- **order_status_history** (id, order_id fk, from_status, to_status, note, changed_by fk, created_at)
- **banners** (id, title, subtitle, image, cta_text, cta_link, position, active, timestamps)
- **reviews** (id, product_id fk, user_id fk, rating tinyint, comment, approved bool, unique[product_id,user_id], timestamps)
- **settings** (key, value json)
- **notifications** (Laravel default) / **audit_logs** (id, user_id, action, model, model_id, changes json, ip, created_at)

Status de pedido (novo padrão solicitado): `PENDING, AWAITING_PAYMENT, PAID, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED` (mapear "confirmado" atual → `PAID`/`PROCESSING`).

---

## 3. Estrutura de diretórios Laravel

```
app/Http/Controllers/{Auth,Shop,Admin}    app/Http/Middleware  app/Http/Requests
app/Models  app/Services  app/Policies  app/Events  app/Jobs  app/Support
database/migrations  database/seeders  database/factories
resources/views/{layouts,partials,shop,account,admin,auth}  resources/css  resources/js
routes/web.php  routes/api.php  public/  storage/  tests/{Feature,Unit}
```

---

## 4. Plano de migração por fases (com aprovação em cada marco)

| Fase | Entrega | Validação |
|---|---|---|
| **1 – Inventário** (este doc) | Mapa ATUAL→NOVO, schema MySQL, plano | ✅ Aguardando sua aprovação |
| **2 – Fundação Laravel** | Projeto Laravel 12, auth (Fortify/Breeze), migrations, models, layout base + design system (Tailwind: cores/fontes Brasil Minis), Alpine/Livewire | Você roda `migrate` + login local |
| **3 – Catálogo** | Categorias, marcas, fabricantes, produtos, imagens, atributos, variantes, busca, filtros, seeders | Home + catálogo + produto no ar local |
| **4 – Cliente** | Conta, favoritos, endereços | Fluxos de conta |
| **5 – Carrinho & Checkout** | Carrinho (sessão+DB), checkout, cupom, pedidos, baixa de estoque com transação, pagamento simulado | Compra ponta a ponta |
| **6 – Admin** | Dashboard, produtos, categorias, marcas, fabricantes, estoque, pedidos+histórico, clientes, banners, cupons, reviews, settings | CRUD admin |
| **7 – Produção Locaweb** | `.env` MySQL, GitHub Actions (deploy SSH), `index.php` apontando para `../brasilminis`, `.htaccess`, `storage:link` + fallback, SSL, sitemap/robots, script de migração de dados Mongo→MySQL (`legacy_id`) | Deploy real |

Regra crítica respeitada: **o projeto React/FastAPI não será removido** até o Laravel estar funcional, testado e aprovado.

---

## 5. Deploy Locaweb (resumo técnico já previsto)

- Laravel fora da pasta pública (`~/brasilminis`), expondo só `~/brasilminis/public` em `public_html` (ajuste do `index.php` para `../brasilminis/...`).
- PHP explícito `/usr/bin/php83`; Composer via `/usr/bin/php83 ~/bin/composer` (contorna `noexec`).
- GitHub Actions: `git pull` → `composer install --no-dev --optimize-autoloader` → `migrate --force` (não destrutivo) → `config/route/view:cache`.
- Assets compilados com Vite no CI (Node só no build), publicados em `public/build`.
- `.env` nunca versionado; MySQL da Locaweb.

---

## 6. Itens que serão REMOVIDOS (independência do Emergent)

- `emergentintegrations`, pacotes de visual-edit, URLs/variáveis específicas do Emergent, qualquer runtime persistente. Logo oficial e assets visuais são preservados (armazenados em `public/`/`storage`).

---

## 7. Pontos que preciso confirmar antes da Fase 2

1. Gerar o Laravel como **novo diretório neste projeto** (`/app/laravel/`) para você commitar? (Aqui não roda PHP; validação será sua/CI.)
2. Autenticação: **Laravel Breeze (Blade)** — ok? (mais simples p/ Blade+Livewire).
3. Migração de dados: os 28 produtos atuais são **seed de demonstração** — recriar via Seeder no Laravel (recomendado) ou exportar do Mongo com `legacy_id`?
4. Produto: adoto o modelo **base comum + `product_attributes` (EAV) + `product_variants`** (conforme seu texto), confirmando?
5. Status de pedido: adoto o **novo conjunto EN (PENDING…REFUNDED)** em vez do atual "confirmado" em PT?
