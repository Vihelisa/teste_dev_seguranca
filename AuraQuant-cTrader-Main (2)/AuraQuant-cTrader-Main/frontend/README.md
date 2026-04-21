# AuraQuant — Trading Automatizado com IA Avançada

Plataforma de trading algorítmico que permite iniciar, parar e monitorar robôs de negociação integrados ao cTrader e MetaTrader 5.

## Stack

- **Frontend**: React 18 + TypeScript + Vite
- **UI**: shadcn/ui + Tailwind CSS
- **Backend**: Django + Django REST Framework
- **Banco de dados**: PostgreSQL
- **Filas**: Redis + Celery
- **Brokers**: cTrader (FIX), MetaTrader 5

## Desenvolvimento local

Requisitos: Node.js 18+, Python 3.11+, Docker (opcional)

```sh
# Clonar o repositório
git clone <URL_DO_REPO>
cd AuraQuant-cTrader-Main

# Backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

O frontend roda em `http://localhost:8080` e faz proxy das chamadas `/api` para o backend Django na porta `8000`.

## Build de produção

```sh
cd frontend
npm run build
```

Os arquivos gerados ficam em `frontend_dist/` e são servidos pelo Django via `whitenoise`.

## Estrutura do frontend

```
src/
├── api/          # Cliente Axios e endpoints
├── components/   # Componentes reutilizáveis (shadcn/ui + customizados)
├── contexts/     # AuthContext
├── hooks/        # Hooks customizados
├── pages/        # Páginas da aplicação
├── types/        # Interfaces TypeScript
└── App.tsx       # Roteamento principal
```
