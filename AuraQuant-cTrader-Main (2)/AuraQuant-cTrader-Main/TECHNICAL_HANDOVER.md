# Dossiê Técnico: Plataforma de Campeonato de Trading

**Versão do Documento:** 1.0
**Data:** 06 de Janeiro de 2026
**Status do Projeto:** Feature-Complete / Pronto para Produção

---

## 1. Visão Geral do Sistema

A **Plataforma de Campeonato de Trading** é uma aplicação web Full-Stack projetada para gerenciar competições de trading em tempo real. Ela permite que usuários registrem-se, vinculem suas contas **MetaTrader 5 (MT5)** e tenham suas operações monitoradas automaticamente.

O sistema processa o histórico de negociações, calcula métricas de performance (ROI, Drawdown, Win Rate) e exibe um **Ranking em Tempo Real** via WebSockets, eliminando a necessidade de atualização manual da página.

---

## 2. Arquitetura de Solução

O sistema opera em uma arquitetura de **Monolito Modular Desacoplado**, onde o Backend e o Frontend são projetos distintos que se comunicam via API REST e WebSockets.

### 2.1. Diagrama de Comunicação

```mermaid
[Navegador do Cliente]
       |
       | (HTTP / WebSocket)
       v
[Proxy Reverso (Nginx / Vite em Dev)]
       |
   -----------------------------------
   |                                 |
   v                                 v
[Frontend (React)]             [Backend (Django/Daphne)]
                                     |
                                     | (Leitura/Escrita)
                                     v
                            [Banco de Dados (PostgreSQL)]
                                     ^
                                     |
                            [Redis (Broker/Cache)]
                                     ^
                                     |
                            [Celery Worker] <--- [Coletor MT5 (Windows)]

2.2. Stack Tecnológico
Frontend:

Framework: React 18 (Vite).

Linguagem: TypeScript.

Gerenciador de Pacotes: Bun (Essencial: o projeto não usa npm/yarn).

UI Kit: Tailwind CSS + Shadcn/UI.

Estado: Context API (Auth) + TanStack Query (Server State).

Backend:

Framework: Django 4.2 + Django REST Framework (DRF).

Linguagem: Python 3.10+.

Servidor ASGI: Daphne (para suportar HTTP e WebSockets simultaneamente).

Async/Tasks: Celery + Django Celery Beat.

Infraestrutura de Dados:

Banco Principal: PostgreSQL (Produção) / SQLite (Dev).

Message Broker & Cache: Redis.

3. Estrutura do Projeto
Plaintext

/
├── core/                 # Configurações globais do Django (settings, asgi, wsgi)
├── trading_platform/     # App principal: Lógica de negócio, Models, Services e Tasks
│   ├── models.py         # Trader, MT5Account, Operation
│   ├── services.py       # Lógica pesada (Sincronização MT5, Cálculo de Ranking)
│   ├── consumers.py      # Lógica de WebSockets (Django Channels)
│   └── tasks.py          # Tarefas assíncronas do Celery
├── Frontend/             # Código fonte do React
│   ├── src/
│   │   ├── api/          # Clientes Axios (client.ts)
│   │   ├── contexts/     # AuthContext (Gerenciamento central de Token/Headers)
│   │   ├── hooks/        # Hooks customizados (useRankingWebSocket)
│   │   └── pages/        # Componentes de página
│   ├── package.json      # Dependências (gerenciado pelo Bun)
│   └── vite.config.ts    # Configuração do Proxy reverso
├── requirements.txt      # Dependências Python
├── run_waitress.bat      # Script de inicialização Windows (Waitress)
└── manage.py             # CLI do Django
4. Fluxos Críticos e Lógica de Negócio
4.1. Autenticação e Segurança (Token + CSRF)
O sistema utiliza uma abordagem centralizada para segurança da API:

Gerenciamento via Contexto: Diferente de interceptors globais implícitos, o AuthContext é a fonte da verdade. Ele injeta o Token de Autenticação e gerencia o estado do usuário.

Axios Limpo: O arquivo Frontend/src/api/client.ts exporta uma instância limpa do Axios com baseURL: '/api'. Isso facilita o teste e evita dependências circulares, delegando a injeção de headers para os componentes/hooks que consomem o contexto ou serviços específicos.

Proxy: O vite.config.ts redireciona chamadas /api para o Django (127.0.0.1:8000), evitando problemas de CORS em desenvolvimento (o cookie é setado no mesmo domínio).

4.2. Sincronização de Dados MT5
Esta é a lógica central (executada via Celery Tasks em trading_platform):

O sistema conecta-se à conta MT5 usando credenciais criptografadas (via cryptography.fernet).

Baixa o histórico de "Deals" (transações).

Agregação: O MT5 trata compras e vendas como eventos separados. O sistema agrupa esses eventos por position_id para consolidar uma Operation (Trade completo).

Persiste no banco e dispara o recálculo de métricas do Trader.

4.3. Atualização em Tempo Real (WebSockets)
O ranking é reativo e "Event-Driven":

Gatilho: Ao finalizar o processamento de trades, o Celery publica uma mensagem no Redis.

Distribuição: O Django Channels (configurado em core/asgi.py) consome essa mensagem.

Entrega: O Consumer envia o payload JSON atualizado via WebSocket para o Frontend.

Frontend: O hook useRankingWebSocket recebe os dados e atualiza a UI sem refresh.

5. Guia de Configuração e Desenvolvimento Local
ATENÇÃO: O ambiente de desenvolvimento recomenda Windows com WSL (devido à biblioteca MetaTrader5 ser exclusiva para Windows) ou uma arquitetura híbrida.

Pré-requisitos
Python 3.10+

Bun (Instalar via PowerShell: irm bun.sh/install.ps1 | iex)

Redis rodando (WSL ou Docker).

Passo a Passo para Rodar
São necessários terminais simultâneos:

Terminal 1 (Backend - Daphne/Waitress):

Certifique-se de corrigir o core/settings.py (remover chave } extra no final se houver).

PowerShell

.\venv\Scripts\activate
# Opção A: Daphne (Suporte a WebSocket)
python -m daphne -p 8000 core.asgi:application
# Opção B: Waitress (Apenas HTTP, usar run_waitress.bat ajustando o caminho do Python)
Terminal 2 (Frontend - Bun):

PowerShell

cd Frontend
bun run dev --port 8080
O vite.config.ts está configurado para rodar na porta 8080 e fazer proxy para a 8000.

Terminal 3 (Celery Worker):

PowerShell

.\venv\Scripts\activate
celery -A core worker --loglevel=info --pool=solo
Nota: --pool=solo é obrigatório no Windows.

6. Guia de Deploy e Produção
A arquitetura de produção sugerida é Híbrida:

6.1. Servidor Principal (Linux/Docker)
Hospeda a aplicação web (Django), banco (PostgreSQL) e cache (Redis).

Servidor Web: Recomenda-se Gunicorn (HTTP) + Daphne (WS) atrás de Nginx.

Estáticos: Configurados via WhiteNoise no settings.py.

6.2. Coletor de Dados (Windows VPS)
CRÍTICO: A biblioteca MetaTrader5 Python só funciona em Windows.

O Worker do Celery responsável pela tarefa fetch_trades deve rodar nesta VPS Windows.

Este Worker deve apontar para o Redis e Banco de Dados do servidor Linux remoto.

7. Solução de Problemas Comuns (Troubleshooting)
Erro SyntaxError ao iniciar o Django:

Causa: Erro de digitação no final de core/settings.py (chave extra).

Solução: Remova o último caractere } do arquivo settings.py.

Erro de Conexão WebSocket:

Causa: O backend não foi iniciado com daphne ou o Nginx/Proxy não está configurado para upgrades de conexão (WS).

Solução: Verifique se core.asgi:application está sendo servido.

Dependências do Frontend falhando:

Causa: Uso misto de npm e bun.

Solução: O projeto foi configurado para Bun. Apague node_modules e bun.lockb se necessário e rode bun install.
