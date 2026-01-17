# Plataforma Birdstone (Aura Quant) - V1.1 Diamond

**Status:** Battle Ready (Beta Fechado)
**Arquitetura:** Híbrida (Dados MT5 / Execução FIX)
**Versão:** 1.1 Diamond (Pós-Sprint Estabilidade)

---

## 1. Visão Geral

A Birdstone é um ecossistema de inteligência financeira que democratiza o acesso a estratégias quantitativas de nível institucional. Nossa arquitetura híbrida combina o melhor de dois mundos:
*   **O Laboratório (Dados):** Utilizamos o **MetaTrader 5 (Desktop)** como fonte robusta de dados históricos para pesquisa e treinamento de IA.
*   **O Front de Batalha (Execução):** Utilizamos a **API FIX (cTrader)** para execução de ordens em baixa latência, garantindo estabilidade e independência de terminais gráficos.

---

## 2. Stack Tecnológica

*   **Backend:** Django 4.2 (Python 3.10+)
*   **Frontend:** React 18 (Vite) + Material UI / Shadcn
*   **Banco de Dados:** PostgreSQL (Produção) / SQLite (Dev)
*   **Mensageria & Async:** Redis + Celery
*   **Conectividade:**
    *   **Dados:** Biblioteca `MetaTrader5` (Windows Only para o worker de dados).
    *   **Execução:** Protocolo FIX 4.4 (via SSL/TCP puro).

---

## 3. Funcionalidades Principais (O Arsenal V1.1)

### 🧠 O Motor Quantitativo (Quant Engine)
*   **Coleta de Dados "Download Ativo":** Script que força o MT5 a baixar histórico profundo, eliminando buracos nos dados.
*   **Estratégias Modulares:** Framework `StrategyContract` (ex: `Hunter X`) que desacopla a lógica de trading da infraestrutura.
*   **Backtest "Veritas Prime":** Pipeline de validação com **Walk-Forward Analysis** (prevenção de overfitting) e simulação financeira híbrida (Risco % vs Lote Mínimo).

### ⚔️ O Motor de Execução (Execution Engine)
*   **Conector FIX Nativo:** Driver Python proprietário para cTrader, gerenciando sessões de Trade e Quote.
*   **Gestão de Risco Dinâmica:** Cálculo de lote baseado no saldo atual da conta (`current_balance`), espelhando a lógica do backtest.
*   **Decision Engine:** Lógica unificada (`analyze_and_get_signal`) que integra indicadores e filtros de IA (XGBoost).

### 🛡️ O Guardião (Segurança)
*   **Kill Switch Ativo:** Monitora o saldo da conta a cada ciclo. Se cair abaixo de zero ou do limite de drawdown configurado, fecha todas as ordens abertas e desliga o robô.
*   **Persistência de Estado (Redis):** O sistema salva as ordens abertas no Redis, garantindo que o Guardião "lembre" das posições mesmo após reinicialização do worker.
*   **Feedback Visual:** Alerta vermelho no frontend quando o sistema está em parada de emergência.

### 🤖 Aura Portfolio AI
*   **Consultoria via LLM:** Módulo que recebe o perfil do investidor e utiliza GPT-4 para gerar uma alocação de portfólio personalizada e profissional.

---

## 4. Protocolo de Inicialização (Ambiente de Desenvolvimento)

Para levantar o ambiente completo, execute os comandos na ordem abaixo em terminais separados:

1.  **Terminal 1 (Infra - Redis):**
    ```bash
    redis-server
    ```

2.  **Terminal 2 (Infra - Dados MT5):**
    *   Abra o terminal MetaTrader 5 (apenas se for rodar backtests ou coleta de dados).

3.  **Terminal 3 (App - Django API):**
    ```bash
    python manage.py runserver 0.0.0.0:8000
    ```

4.  **Terminal 4 (App - Celery Worker Trading):**
    ```bash
    celery -A core worker -Q realtime_trading -l info
    ```
    *(Responsável pela execução FIX e Kill Switch)*

5.  **Terminal 5 (App - Celery Worker Backtest):**
    ```bash
    celery -A core worker -Q backtesting_heavy -l info
    ```
    *(Responsável pelo processamento de dados e IA)*

6.  **Terminal 6 (App - Frontend):**
    ```bash
    cd frontend
    npm run dev
    ```
    *(Acessar em http://localhost:8080 ou a porta indicada pelo Vite)*

---

## 5. Roadmap e Próximos Passos

Consulte o documento `CONSOLIDADO_BIRDSTONE_AURA.md` para detalhes sobre a estratégia futura.

*   **Médio Prazo (V2.0):** Arquitetura AsyncIO e Birdstone Forge.

---
*Documentação atualizada em 28/07/2025 por Jules.*
