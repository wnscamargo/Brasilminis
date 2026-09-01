# Brasil Minis — Deploy do zero em VPS Ubuntu 24.04 LTS

Stack: **Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL + Gunicorn/Uvicorn** (backend),
**React CRA (JS) build estático** (frontend), **Nginx + HTTPS Let's Encrypt**, **systemd**.
Sem Docker, PHP, Laravel, MongoDB, Supervisor, PM2 ou Kubernetes.

Estrutura final na VPS:
```
/var/www/brasilminis/
├── backend/        (app/, alembic/, .venv/, .env, server.py, requirements.txt)
├── frontend/       (build/ servido pelo Nginx; .env com REACT_APP_BACKEND_URL)
├── infra/          (nginx/, systemd/, scripts/, docs/)
└── backups/        (dumps do PostgreSQL)
```

---

## 1. Acessar a VPS
```bash
ssh root@SEU_IP
```

## 2. Atualizar o Ubuntu
```bash
apt update && apt -y upgrade
timedatectl set-timezone America/Sao_Paulo
```

## 3. Criar usuário dedicado da aplicação (não-root)
```bash
adduser --disabled-password --gecos "" brasilminis
usermod -aG www-data brasilminis
mkdir -p /var/www/brasilminis
chown -R brasilminis:brasilminis /var/www/brasilminis
```

## 4. Firewall UFW (só 22, 80, 443)
```bash
apt -y install ufw
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
ufw status
```
> PostgreSQL (5432) **não** é liberado — fica apenas local.

## 5. Instalar Nginx
```bash
apt -y install nginx
```

## 6. Instalar Python 3.12
```bash
apt -y install python3.12 python3.12-venv python3-pip
python3.12 --version
```

## 7. Instalar PostgreSQL
```bash
apt -y install postgresql postgresql-contrib
systemctl enable --now postgresql
```

## 8. Instalar Node (para build do frontend) + Yarn
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt -y install nodejs
npm i -g yarn    # opcional (o repo usa yarn.lock)
```

## 9. Instalar Git
```bash
apt -y install git
```

## 10. Clonar o projeto (branch python-vps)
```bash
sudo -u brasilminis -H bash
cd /var/www/brasilminis
git clone -b python-vps <URL_DO_REPO> .
```

## 11. Criar o virtualenv do backend
```bash
cd /var/www/brasilminis/backend
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 12. Configurar o `.env` do backend
```bash
cp .env.example .env
nano .env
# Gere segredos:
#   openssl rand -hex 32   -> JWT_SECRET
# Defina DATABASE_URL, ADMIN_*, CORS_ORIGINS, AUTO_CREATE_TABLES=false
```
E o `.env` do frontend (build usa o domínio oficial, mesma origem):
```bash
cd /var/www/brasilminis/frontend
echo "REACT_APP_BACKEND_URL=https://brasilminis.com" > .env
```

## 13. Configurar o PostgreSQL (banco + usuário dedicado, senha fora do Git)
```bash
sudo -u postgres psql <<'SQL'
CREATE ROLE brasilminis_app LOGIN PASSWORD 'TROQUE_POR_SENHA_FORTE';
CREATE DATABASE brasilminis OWNER brasilminis_app;
SQL
```
- Mantenha `listen_addresses = 'localhost'` em `/etc/postgresql/*/main/postgresql.conf` (conexão só local).
- Use a MESMA senha no `DATABASE_URL` do `.env`.

## 14. Aplicar as migrations (Alembic)
```bash
cd /var/www/brasilminis/backend
set -a; . ./.env; set +a
.venv/bin/alembic upgrade head
```
> `AUTO_CREATE_TABLES=false` em produção — as tabelas vêm SÓ do Alembic.

## 15. Build do frontend
```bash
cd /var/www/brasilminis/frontend
yarn install --frozen-lockfile && yarn build      # ou: npm install && npm run build
# gera /var/www/brasilminis/frontend/build
```

## 16. Instalar o serviço systemd
```bash
sudo cp /var/www/brasilminis/infra/systemd/brasilminis-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now brasilminis-backend
sudo systemctl status brasilminis-backend
```
Permitir ao usuário de deploy recarregar serviços (sudoers):
```bash
echo 'brasilminis ALL=(root) NOPASSWD: /bin/systemctl restart brasilminis-backend, /bin/systemctl reload nginx, /usr/sbin/nginx -t' \
  | sudo tee /etc/sudoers.d/brasilminis
```

## 17. Instalar a configuração do Nginx
```bash
sudo cp /var/www/brasilminis/infra/nginx/brasilminis.conf /etc/nginx/sites-available/brasilminis.conf
sudo ln -sf /etc/nginx/sites-available/brasilminis.conf /etc/nginx/sites-enabled/brasilminis.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

## 18. Apontar o domínio
- No DNS, crie registros A/AAAA de `brasilminis.com` e `www.brasilminis.com` para o IP da VPS.

## 19. Instalar o Certbot e emitir o certificado
```bash
apt -y install certbot python3-certbot-nginx
certbot --nginx -d brasilminis.com -d www.brasilminis.com
systemctl status certbot.timer   # renovação automática
```

## 20. Validar HTTPS
```bash
curl -I https://brasilminis.com
```

## 21–25. Homologação (checklist)
```bash
API=https://brasilminis.com
curl -s $API/api/health                      # 21. API health -> {"status":"ok"}
curl -I $API/                                 # 22. Home (200)
# 23. Login admin:
curl -s -c c.txt -X POST $API/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@brasilminis.com","password":"<sua_senha>"}'
curl -s -b c.txt $API/api/auth/me
# 24. Criar pedido (registre um cliente antes) e 25. validar baixa de estoque:
#   - pegue um produto: curl -s "$API/api/products?limit=1"
#   - POST $API/api/orders com {items:[{product_id, quantity}]}
#   - confira o stock antes/depois em /api/products/{slug}
#   - tente quantity > stock -> deve retornar 400 "Estoque insuficiente" sem baixar estoque
```

---

## Deploy contínuo
```bash
sudo -u brasilminis -H bash -lc 'cd /var/www/brasilminis && bash infra/scripts/deploy.sh'
```
Fluxo: git pull (ff-only) → pip install → alembic upgrade head → build isolado → restart backend → reload Nginx.
Se o build falhar, a versão funcional NÃO cai. Sem seed automático, sem reset de banco, `.env` e uploads preservados.

## Backup / Restore
```bash
# Backup (agende no cron):
DB_USER=brasilminis_app PGPASSWORD=... bash infra/scripts/backup-db.sh
# Restore (manual, destrutivo, pede confirmação):
sudo systemctl stop brasilminis-backend
DB_USER=brasilminis_app PGPASSWORD=... bash infra/scripts/restore-db.sh /var/www/brasilminis/backups/<arquivo>.sql.gz
sudo systemctl start brasilminis-backend
```

## Checklist final
- [ ] GET home / API `/api/health`
- [ ] login admin / registro cliente
- [ ] catálogo / busca / cupom
- [ ] criação de pedido + baixa de estoque + rejeição de estoque insuficiente
- [ ] RBAC (admin vs cliente vs anônimo)
- [ ] rate limiting (5 logins errados -> 429)
- [ ] Alembic aplicado (`alembic current`)
- [ ] `systemctl restart brasilminis-backend` OK
- [ ] reboot da VPS: serviços sobem sozinhos (Nginx, PostgreSQL, backend)
- [ ] HTTPS válido (cadeado)
- [ ] refresh do SPA em rotas React (ex.: /produtos) retorna 200 (fallback index.html)

## Segurança (resumo)
- `APP_ENV=production`, `DEBUG=false`, `AUTO_CREATE_TABLES=false`.
- CORS só para `https://brasilminis.com` e `https://www.brasilminis.com`.
- PostgreSQL apenas local (sem 5432 exposto). Firewall: 22/80/443.
- Backend em `127.0.0.1:8000` (não exposto direto); só o Nginx fala com a internet.
- Nginx sobrescreve `X-Forwarded-For` com o IP real (`$remote_addr`) — impede spoofing do rate limit.
- Usuário Linux dedicado `brasilminis` (backend não roda como root).
- Nenhum segredo no Git (apenas `.env.example`).
