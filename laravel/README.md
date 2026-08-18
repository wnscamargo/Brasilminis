# Brasil Minis — Laravel 12 (PHP 8.3 + MySQL 8)

E-commerce premium de miniaturas automotivas, migrado de React/FastAPI/MongoDB para uma stack compatível com **hospedagem compartilhada Linux (Locaweb)**: PHP 8.3, Laravel 12, Blade, Tailwind, Alpine.js, MySQL 8, Apache. Sem Node/FastAPI/Mongo/Docker/VPS em produção.

> ⚠️ Este repositório foi **gerado** no ambiente Emergent (que não roda PHP). Ele **não foi executado/testado** lá. Rode os passos abaixo localmente ou no CI para validar (Fase de homologação).

## Requisitos
- PHP 8.3 (ext: pdo_mysql, mbstring, bcmath, gd, zip)
- Composer
- MySQL 8
- Node 20 (apenas para compilar assets com Vite — local ou CI)

## Setup local
```bash
cp .env.example .env
composer install
php artisan key:generate

# ajuste DB_* no .env (MySQL local)
php artisan migrate --seed        # cria tabelas + admin + 28 produtos + cupons + banner
php artisan storage:link

npm install && npm run build      # ou: npm run dev
php artisan serve                 # http://localhost:8000
```

## Credenciais (seed DEMO — apenas fora de produção)
- **Admin demo**: `admin@brasilminis.com` / `Admin@2025` → `/admin`
- **Cliente demo**: `cliente@teste.com` / `senha123`
- **Cupons**: `BRASIL10`, `MINIS20`, `FRETEGRATIS`

> Em **produção** o `DemoSeeder` é bloqueado (não cria credenciais conhecidas). Rode apenas os essenciais e crie o admin com senha segura:
> ```bash
> php artisan migrate --force
> php artisan db:seed --class=Database\\Seeders\\EssentialSeeder --force
> php artisan bm:create-admin admin@seudominio.com.br --name="Seu Nome"
> # a senha forte é gerada e exibida uma única vez (ou use --password=...)
> ```

## Testes (Pest)
```bash
./vendor/bin/pest        # usa SQLite em memória (phpunit.xml)
```
Cobre: home, catálogo, cadastro, login admin, RBAC admin, carrinho, criação de pedido (baixa de estoque + frete grátis) e cupons.

## Estrutura
- `app/Http/Controllers` (storefront, `Account`, `Auth`, `Admin`)
- `app/Models`, `app/Services` (CartService, OrderService, PaymentService), `app/Http/Middleware/EnsureUserIsAdmin`
- `database/migrations` (23 tabelas), `database/seeders/BrasilMinisSeeder`
- `resources/views` (`layouts`, `partials`, `shop`, `account`, `auth`, `admin`)
- `routes/web.php`

## Pagamento
- **Simulado (mock)** no MVP — `App\Services\PaymentService` (driver `mock`).
- Pronto para **Mercado Pago**: implemente `mercadoPago()` no PaymentService, configure `MERCADOPAGO_*` no `.env`, mude `PAYMENT_DRIVER=mercadopago` e crie a rota de webhook para atualizar `payment_status`/`status` do pedido.

## Deploy Locaweb (hospedagem compartilhada)
Estrutura sugerida (Laravel FORA do public_html):
```
/home/storage/.../brasilminis1/brasilminis/app/laravel   <- este repositório (Laravel)
/home/storage/.../brasilminis1/public_html               <- pasta pública do domínio
```
1. Clone o repo (branch `laravel-migration`) em `.../brasilminis/app/laravel`.
2. Aponte o domínio para `public_html`. Copie o conteúdo de `app/laravel/public/` para `public_html/` **ou** use `deploy/public_html_index.php` (aponta para `../brasilminis/app/laravel`).
3. Configure `.env` (nunca versionado) com o MySQL da Locaweb:
   ```
   DB_CONNECTION=mysql
   DB_HOST=...  DB_PORT=3306  DB_DATABASE=...  DB_USERNAME=...  DB_PASSWORD=...
   APP_ENV=production  APP_DEBUG=false  APP_URL=https://seudominio.com.br
   SESSION_SECURE_COOKIE=true
   ```
4. Deploy automático via **GitHub Actions** (`.github/workflows/deploy.yml`) — configure os secrets:
   `LOCAWEB_HOST`, `LOCAWEB_USER`, `LOCAWEB_SSH_KEY`, `LOCAWEB_PORT`.
   Fluxo: git pull → `php83 composer install --no-dev` → `migrate --force` → `config/route/view:cache`.
5. Deploy manual alternativo: `bash deploy/deploy.sh`.

Notas Locaweb:
- Composer via `/usr/bin/php83 ~/bin/composer` (contorna `noexec`).
- Se `storage:link` (symlink) não for permitido, copie `storage/app/public` para `public/storage`.

## Independência do Emergent
Sem `emergentintegrations`, sem pacotes de visual-edit, sem runtime persistente. Roda em qualquer host Linux com PHP 8.3 + MySQL 8. As imagens de demonstração usam URLs públicas (Unsplash) e a logo está em `config/brasilminis.php` (troque por assets locais em `public/` quando desejar).

## Status de pedido
`PENDING, AWAITING_PAYMENT, PAID, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED` (com histórico em `order_status_history`).

## Mapa da migração
Ver `/app/docs/MIGRATION_PHASE1_INVENTORY.md` (equivalência ATUAL→NOVO e schema).
