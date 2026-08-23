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

## Deploy Locaweb — BUILD no GitHub Actions, hospedagem só executa Laravel

> ⚠️ A Locaweb desabilita `php_strip_whitespace`, `proc_open`, `exec`, `shell_exec`, `system` e `symlink`.
> Por isso **NADA de build roda na Locaweb**: sem `composer install`, sem `composer dump-autoload`,
> sem `npm install/build`, sem `storage:link`. Todo o build acontece no **GitHub Actions** e apenas o
> **artefato pronto** (com `vendor/` e `public/build/`) é enviado por rsync/SSH.

### Fluxo
```
git push (branch laravel-migration)
   → GitHub Actions: PHP 8.3 → composer install --no-dev --optimize-autoloader
   → yarn build (Vite) → public/build
   → rsync do Laravel (com vendor/) para LOCAWEB_PATH  (fora do public_html)
   → rsync de public/ para LOCAWEB_PUBLIC_PATH + index.php do public_html
   → SSH: php83 artisan migrate --force + config/route/view:cache  (com fallback, sem quebrar)
```

### Estrutura real na Locaweb
```
/home/storage/d/6c/81/brasilminis1/brasilminis/laravel   <- Laravel (LOCAWEB_PATH), com vendor/ pronto
/home/storage/d/6c/81/brasilminis1/public_html           <- pasta pública (LOCAWEB_PUBLIC_PATH)
```

### GitHub Secrets (Settings → Secrets and variables → Actions)
`LOCAWEB_HOST`, `LOCAWEB_USER`, `LOCAWEB_PORT`, `LOCAWEB_SSH_KEY` (chave privada),
`LOCAWEB_PATH`, `LOCAWEB_PUBLIC_PATH`. Nenhum valor sensível fica no repositório.

### composer.lock (obrigatório e versionado)
Como o ambiente onde este código foi gerado não tem PHP/Composer, **gere o `composer.lock` localmente uma vez**
e faça commit (o workflow falha propositalmente se o lock estiver ausente):
```bash
cd laravel
composer install          # gera composer.lock a partir do composer.json
git add composer.lock && git commit -m "chore: composer.lock travado para deploy"
```
Em produção o deploy usa **exatamente** as versões travadas no lock.

### Uploads sem symlink
`storage:link` não é usado (symlink bloqueado). Existe o disco **`uploads`** (`config/filesystems.php`)
que grava direto numa pasta pública. Em produção configure no `.env`:
```
UPLOADS_ROOT=/home/storage/d/6c/81/brasilminis1/public_html/uploads
UPLOADS_URL=https://seudominio.com.br/uploads
```
E use `Storage::disk('uploads')` para arquivos públicos.

### Pós-deploy manual (opcional)
O CI já roda o pós-deploy. Se precisar rodar à mão via SSH (sem composer/npm):
```bash
LOCAWEB_PATH=/home/storage/.../brasilminis/laravel \
LOCAWEB_PUBLIC_PATH=/home/storage/.../public_html \
bash deploy/deploy.sh
```

## Independência do Emergent
Sem `emergentintegrations`, sem pacotes de visual-edit, sem runtime persistente. Roda em qualquer host Linux com PHP 8.3 + MySQL 8. As imagens de demonstração usam URLs públicas (Unsplash) e a logo está em `config/brasilminis.php` (troque por assets locais em `public/` quando desejar).

## Status de pedido
`PENDING, AWAITING_PAYMENT, PAID, PROCESSING, SHIPPED, DELIVERED, CANCELLED, REFUNDED` (com histórico em `order_status_history`).

## Mapa da migração
Ver `/app/docs/MIGRATION_PHASE1_INVENTORY.md` (equivalência ATUAL→NOVO e schema).
