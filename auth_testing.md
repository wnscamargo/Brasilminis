# Auth Testing Playbook — Brasil Minis

## MongoDB Verification
```
mongosh
use brasil_minis
db.users.find({role: "admin"}).pretty()
```
Verify bcrypt hash starts with `$2b$`. Unique index on users.email.

## API Testing
```
curl -c cookies.txt -X POST http://localhost:8001/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@brasilminis.com","password":"Admin@2025"}'
curl -b cookies.txt http://localhost:8001/api/auth/me
```
Login returns the user object and sets access_token + refresh_token cookies.
