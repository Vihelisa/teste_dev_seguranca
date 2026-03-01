# ============================================================================
# GUIA DE INSTALAÇÃO — DOCKER LOCAL
# Aura Quant Platform V1.0
# ============================================================================

## 📋 PRÉ-REQUISITOS

1. **Docker Desktop** instalado
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Após instalar, reinicie o computador

2. **MT5** (para backtesting)
   - Já instalado e configurado ✅

---

## 🚀 PASSO A PASSO — PRIMEIRA VEZ

### 1. Copiar arquivos Docker para o projeto

Copie estes 3 arquivos para a **raiz** do seu projeto (onde está o `manage.py`):

```
Dockerfile
docker-compose.yml
.env.docker.example
```

### 2. Configurar variáveis de ambiente

```bash
# Copie o arquivo de exemplo
copy .env.docker.example .env

# Edite o .env e adicione sua ENCRYPTION_KEY
# Se não tiver, gere uma nova:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Cole a chave gerada no .env na linha:
ENCRYPTION_KEY=sua-chave-aqui=
```

### 3. Criar arquivo requirements.txt (se não existir)

Na raiz do projeto, crie `requirements.txt` com:

```
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-decouple==2.1
psycopg2-binary==2.9.9
django-redis==5.4.0
celery==5.3.6
django-celery-beat==2.5.0
redis==5.0.1
cryptography==42.0.2
xgboost==2.0.3
pandas==2.2.0
numpy==1.26.3
scikit-learn==1.4.0
joblib==1.3.2
MetaTrader5==5.0.4510
simplefix==1.0.16
python-decouple==3.8
kombu==5.3.5
pandas-ta==0.3.14b0
optuna==3.5.0
channels==4.0.0
channels-redis==4.1.0
whitenoise==6.6.0
```

### 4. Iniciar os containers

```bash
# Abra o terminal na raiz do projeto e rode:
docker-compose up --build

# OU em modo background (detached):
docker-compose up -d --build
```

### 5. Aguardar inicialização (primeira vez demora ~3-5 min)

Você verá logs de:
- PostgreSQL iniciando
- Redis iniciando
- Django rodando migrações
- Celery Worker iniciando
- Frontend compilando

### 6. Acessar a aplicação

Quando ver a mensagem:
```
django    | Starting development server at http://0.0.0.0:8000/
frontend  | ➜  Local:   http://localhost:5173/
```

Acesse:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/api/
- **Admin Django:** http://localhost:8000/admin/
  - User: `admin`
  - Pass: `admin123`

---

## 🔧 COMANDOS ÚTEIS

### Ver logs em tempo real
```bash
# Todos os serviços
docker-compose logs -f

# Apenas Django
docker-compose logs -f django

# Apenas Celery
docker-compose logs -f celery_worker
```

### Parar os containers
```bash
docker-compose down
```

### Reiniciar um serviço específico
```bash
docker-compose restart django
docker-compose restart celery_worker
```

### Executar comandos Django dentro do container
```bash
# Criar superusuário
docker-compose exec django python manage.py createsuperuser

# Rodar migrações
docker-compose exec django python manage.py migrate

# Shell Django
docker-compose exec django python manage.py shell

# Coletar static files
docker-compose exec django python manage.py collectstatic
```

### Acessar o shell do container
```bash
docker-compose exec django sh
```

### Limpar tudo e recomeçar
```bash
# Para e remove containers + volumes (CUIDADO: apaga BD!)
docker-compose down -v

# Rebuild completo
docker-compose up --build
```

---

## 📊 VALIDAR SE ESTÁ FUNCIONANDO

### 1. Verificar se todos os serviços estão "healthy"
```bash
docker-compose ps
```

Deve mostrar:
```
aura_postgres       Up (healthy)
aura_redis          Up (healthy)
aura_django         Up (healthy)
aura_celery_worker  Up
aura_celery_beat    Up
aura_frontend       Up
```

### 2. Testar o backend
```bash
curl http://localhost:8000/api/health/
```

### 3. Testar autenticação
Abra http://localhost:5173 e tente fazer login

### 4. Rodar backtest (DENTRO do container Django)
```bash
docker-compose exec django python validate_ml_pipeline.py
```

---

## ⚠️ TROUBLESHOOTING

### Erro: "port is already allocated"
```bash
# Algum serviço está usando a porta 5432, 6379, 8000 ou 5173
# Pare os serviços locais:
# - PostgreSQL local
# - Redis local
# - Django runserver
# - npm run dev
```

### Erro: "ENCRYPTION_KEY" not found
```bash
# Adicione a chave no .env
# Gere uma nova:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Erro: MT5 não conecta no backtest
```bash
# MT5 precisa estar rodando no HOST (seu Windows)
# Docker não consegue acessar MT5 diretamente
# Solução: rode o backtest FORA do Docker
python validate_ml_pipeline.py
```

### Container Django fica reiniciando
```bash
# Veja os logs
docker-compose logs django

# Geralmente é erro de migração ou .env incorreto
```

---

## 🧪 TESTANDO O SISTEMA COMPLETO

### 1. Criar conta de usuário
- Acesse: http://localhost:5173
- Registre uma nova conta

### 2. Criar conta de trading
- Login → Accounts → Add Account
- Preencha com dados de teste (pode ser fake)

### 3. Ativar uma estratégia
- Marketplace → Liquidity Hunter → Activate
- Escolha a conta criada
- Define lote: 0.01

### 4. Verificar se Celery está processando
```bash
docker-compose logs -f celery_worker
```

Deve ver logs de monitoramento iniciando

---

## 📝 PRÓXIMOS PASSOS APÓS VALIDAR LOCAL

1. ✅ Sistema funciona localmente
2. ✅ Todas as features testadas
3. ✅ Nenhum bug crítico encontrado
4. → **Partir para AWS!**

---

## 🆘 AJUDA

Se algo não funcionar:
1. Veja os logs: `docker-compose logs -f`
2. Verifique o .env
3. Confirme que Docker Desktop está rodando
4. Reinicie tudo: `docker-compose down && docker-compose up --build`

---

**Documentação gerada em:** 01/03/2026
