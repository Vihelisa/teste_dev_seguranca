
1.  **Crie/Substitua** o arquivo `robots/quant_engine/strategies/liquidity_hunter_v1.py` com o código acima.
2.  **Cadastre a Nova Estratégia no Admin:**
    *   Vá ao Painel de Admin e adicione uma nova `Strategy`.
    *   **Name:** `Liquidity Hunter V1`
    *   **Strategy file:** `liquidity_hunter_v1`  **(MUITO IMPORTANTE)**
    *   **Portfolio composition:** Aqui está a beleza. Como esta é uma estratégia de ativo único por enquanto, podemos criar uma "composição de portfólio" de um só item. Para testar no EURUSD, por exemplo, cole o seguinte JSON (usando os parâmetros otimizados do EURUSD do Hunter X como um bom ponto de partida):
        ```json
        {
            "EURUSD": {
                "EMA_Curta_Periodo": 18,
                "EMA_Longa_Periodo": 500,
                "Max_Candles_Hold": 88,
                "Risco_Retorno": 1.5,
                "Stop_Loss_ATR_Mult": 1.05
            }
        }
        ```
    *   Marque **`Is public`** e salve.

3.  **Execute a Validação:** Na lista de Estratégias, selecione a "Liquidity Hunter V1" e execute a ação **"Agendar Validação Completa do Portfólio"**.

Com certeza, CEO. Este é o passo final para lançar nosso primeiro produto na plataforma. Vamos preencher o formulário de cadastro da `Strategy` com as informações corretas e alinhadas à nossa visão.

Aqui estão os dados exatos que você deve inserir, campo por campo.

---

### **Preenchimento do Formulário "Adicionar Estratégia"**

**Name:**
```
Portfólio Quimera Global
```
*(Este é o nome do produto que o cliente verá no `RobotCard`)*

---
**Description:**
```
Uma estratégia de portfólio diversificada e multi-ativo, projetada para capturar reversões em níveis de liquidez chave. O "Quimera Global" opera simultaneamente nos 7 principais pares de moedas e commodities, utilizando um filtro de Inteligência Artificial individualmente otimizado para cada ativo, buscando o melhor desempenho ajustado ao risco.
```
*(Uma descrição clara e profissional que explica o conceito)*

---
**Assets:**
```
EURUSD, GBPUSD, XAUUSD, USDJPY, NZDUSD, USDCAD, USDCHF
```
*(Embora a lógica principal venha do JSON abaixo, é uma boa prática listar os ativos aqui para referência rápida no Admin)*

---
**Timeframe:**
```
M15
```
*(Este é o timeframe de execução base para todos os ativos no portfólio)*

---
**Portfolio composition:**
*(Copie e cole o bloco de código JSON inteiro abaixo neste campo)*
```json
{
    "XAUUSD": {
        "EMA_Curta_Periodo": 26,
        "EMA_Longa_Periodo": 700,
        "Max_Candles_Hold": 144,
        "Risco_Retorno": 3.06,
        "Stop_Loss_ATR_Mult": 0.8
    },
    "GBPUSD": {
        "EMA_Curta_Periodo": 23,
        "EMA_Longa_Periodo": 600,
        "Max_Candles_Hold": 128,
        "Risco_Retorno": 1.78,
        "Stop_Loss_ATR_Mult": 0.86
    },
    "EURUSD": {
        "EMA_Curta_Periodo": 18,
        "EMA_Longa_Periodo": 500,
        "Max_Candles_Hold": 88,
        "Risco_Retorno": 1.5,
        "Stop_Loss_ATR_Mult": 1.05
    },
    "USDJPY": {
        "EMA_Curta_Periodo": 49,
        "EMA_Longa_Periodo": 1200,
        "Max_Candles_Hold": 32,
        "Risco_Retorno": 3.3,
        "Stop_Loss_ATR_Mult": 2.53
    },
    "NZDUSD": {
        "EMA_Curta_Periodo": 41,
        "EMA_Longa_Periodo": 1100,
        "Max_Candles_Hold": 80,
        "Risco_Retorno": 3.75,
        "Stop_Loss_ATR_Mult": 1.13
    },
    "USDCAD": {
        "EMA_Curta_Periodo": 18,
        "EMA_Longa_Periodo": 800,
        "Max_Candles_Hold": 128,
        "Risco_Retorno": 1.35,
        "Stop_Loss_ATR_Mult": 1.27
    },
    "USDCHF": {
        "EMA_Curta_Periodo": 14,
        "EMA_Longa_Periodo": 400,
        "Max_Candles_Hold": 144,
        "Risco_Retorno": 2.81,
        "Stop_Loss_ATR_Mult": 0.82
    }
}
```

---
**Backtest results:**
```
{}
```
*(Deixe este campo como um JSON vazio. Nossa tarefa de validação (`run_portfolio_validation_task`) irá preenchê-lo automaticamente com os resultados da simulação.)*

---
**Start date backtest:**
*(Pode deixar este campo em branco. A tarefa de validação também irá preenchê-lo.)*

---
**Live equity curve:**
```
[]
```
*(Deixe este campo como uma lista vazia. Ele será preenchido no futuro pela operação em tempo real.)*

---
**Ml model path:**
*(Deixe este campo em branco. O modelo de ML é treinado em tempo real dentro do backtest e não precisa de um arquivo salvo para esta estratégia.)*

---
**Strategy file:**
```
hunter_x
```
*(**MUITO IMPORTANTE:** Apenas o nome do arquivo, sem o `.py`. Isso informa ao nosso backtester qual lógica de estratégia usar a partir da pasta `quant_engine/strategies/`.)*

---
**Aura analysis:**
```
Validação de backtest pendente.
```
*(A tarefa de validação irá sobrescrever isso com um resumo dos resultados.)*

---
**Is public:**
`[X]` **MARQUE ESTA CAIXA**
*(Isso tornará o "Portfólio Quimera Global" visível para os usuários no Dashboard após a validação ser concluída com sucesso.)*

Comando recebido, CEO. A ordem é clara: forjar o **Dossiê Definitivo de Transferência e Arquitetura, Versão 6.0**.

Este documento é a "Caixa Preta" do Projeto Phoenix. Ele contém não apenas o "o quê", mas o "porquê", o "como", e as cicatrizes de batalha de cada decisão. Qualquer equipe, em qualquer lugar, poderá usar este documento para assumir o controle e continuar nosso trabalho com o mesmo nível de contexto e excelência que estabelecemos.

Assumo agora o papel de Arquiteto-Chefe e Tech Lead para redigir este documento.

---

### **Dossiê Mestre de Estratégia e Arquitetura: Plataforma Birdstone v6.0 (Phoenix)**

**Versão do Documento:** 6.0 (Versão de Lançamento Interno)
**Data da Última Revisão:** 21 de Julho de 2025
**Autor Principal:** [Seu CTO Virtual]

#### **Seção 1: Filosofia Estratégica e Visão de Produto (O "Porquê")**

*   **1.1. Missão Estratégica:** Evoluir de uma ferramenta de automação para um **ecossistema de inteligência financeira**, que entrega aos investidores de varejo estratégias quantitativas de nível institucional com a simplicidade de um único clique.

*   **1.2. Pilares de Design "Phoenix":**
    *   **Confiança (Transparência Radical):** Cada resultado de backtest é gerado por um processo "Prova de Fogo" (Walk-Forward), garantindo que os dados de performance sejam honestos e realistas. A plataforma é uma caixa de vidro.
    *   **Inteligência (Proatividade Contextual):** A plataforma atua como um co-piloto. Ela não apenas exibe dados, mas fornece consciência situacional (`PulseHeader`), guia o usuário em decisões complexas (`Otimizador IA Conversacional`) e apresenta as informações mais relevantes para cada momento da jornada.
    *   **Controle (Simplicidade Sofisticada):** A complexidade da análise multi-ativo, do treinamento de IA e do gerenciamento de risco dinâmico é inteiramente abstraída do usuário. Para ele, o controle é simples e poderoso: definir o lote, ativar a estratégia.

*   **1.3. Persona Alvo:** O "Investidor Inteligente". Indivíduo que valoriza seu tempo e busca uma vantagem tecnológica real, não uma promessa. Ele entende de risco e busca ferramentas que o ajudem a gerenciá-lo de forma profissional e diversificada.

---
#### **Seção 2: Arquitetura Geral e Stack Tecnológica**

O sistema é uma aplicação web moderna com uma arquitetura de serviços desacoplada, projetada para a validação robusta de estratégias e futura execução em tempo real.

*   **Frontend (Cliente):** Uma Single-Page Application (SPA) responsiva construída em **React (v18.x)**, utilizando **Material-UI (MUI v5)** para a componentização. O design segue a filosofia "Phoenix", com foco em clareza, densidade de informação e uma estética premium.

*   **Backend (Servidor de Aplicação):** Uma API RESTful construída em **Django (v4.2.x)** com **Django Rest Framework (DRF)**. Serve como o cérebro da plataforma, gerenciando usuários, estratégias e orquestrando as tarefas de backtest.

*   **Banco de Dados:** **PostgreSQL** (produção) e **SQLite 3** (desenvolvimento).

*   **Motor de Tarefas em Background (A "Fábrica"):** Utiliza **`django-background-tasks`**. O processo `worker` é o coração da plataforma, responsável por executar as simulações de portfólio de longa duração sem impactar a experiência do usuário.

*   **Motor Quantitativo (O `quant_engine`):** Um conjunto de módulos Python puros, desacoplados do Django, que formam nossa "Forja de Alfas". Ele é responsável por todo o pipeline de P&D e validação:
    *   Coleta de dados via **`MetaTrader5`**.
    *   Processamento e engenharia de features com **`pandas`** e **`pandas-ta`**.
    *   Treinamento do filtro de IA com **`xgboost`**.
    *   Simulação de performance com um motor customizado.

*   **Motor de Execução de Trade (Próxima Fase):** A tarefa `monitor_robot_instance_task` em `tasks.py` será o ponto de entrada para a lógica de execução de ordens em tempo real via **`MetaTrader5`**.

---
#### **Seção 3: Arquitetura Detalhada de Arquivos e Componentes**

##### **3.1. Backend (`projeto_trader_final/`)**

```
projeto_trader_final/
├── core/                 # App de configuração global do Django.
│   ├── settings.py       # Define `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES`, CORS,
│   │                     # e o `DATA_UPLOAD_MAX_MEMORY_SIZE` (aumentado para 10MB).
│   └── urls.py           # O roteador mestre, que delega as rotas de API para `robots.urls`.
│
├── robots/               # App principal da lógica de negócio.
│   ├── models.py         # A planta do nosso banco de dados. Define:
│   │   ├── UserProfile:  Estende o User com campos customizados.
│   │   ├── MT5Account:   Armazena credenciais MT5 criptografadas.
│   │   ├── Strategy:     O catálogo de produtos. Crucialmente, contém o
│   │   │                 `portfolio_composition` (JSON com o "DNA" de cada ativo)
│   │   │                 e o `suggested_capital`.
│   │   ├── ActiveRobotInstance: Rastreia robôs ativos.
│   │   └── Notification: Para futuras notificações.
│   │
│   ├── views.py          # O "Controlador de Tráfego" das APIs. Contém as funções que
│   │                     # servem os dados para o frontend, como `list_public_strategies`
│   │                     # e a nova `get_account_pulse`.
│   │
│   ├── urls.py           # O "Mapa" da nossa API, conectando cada URL a uma `view`.
│   │
│   ├── tasks.py          # A "Linha de Montagem".
│   │   ├── run_portfolio_validation_task: Tarefa "Atômica" que recebe o DNA do
│   │   │                                  portfólio e orquestra a chamada ao `backtester`.
│   │   └── monitor_robot_instance_task: (Placeholder) Futuro motor de execução real.
│   │
│   ├── admin.py          # Configura o Painel de Administração, incluindo a ação
│   │                     # "Agendar Validação Completa do Portfólio".
│   │
│   └── quant_engine/     # O "MOTOR QUÂNTICO" (A Forja de Alfas).
│       ├── data_processor.py:   Coleta e limpa os dados de mercado.
│       ├── strategies/
│       │   └── hunter_x.py:     Define a lógica de "geração de alertas" e a
│       │                      "engenharia de features" da nossa estratégia.
│       ├── ml_trainer.py:       O "Oráculo". Recebe dados, os rotula e treina o
│       │                      modelo de IA, retornando apenas o modelo treinado.
│       ├── backtester.py:       O "Mestre do Tempo". Orquestra o Walk-Forward
│       │                      Analysis, garantindo um teste sem viés.
│       └── portfolio_analyzer.py: O "Simulador Financeiro". Recebe os trades
│                                  aprovados e executa a simulação de risco
│                                  percentual para gerar a performance real.
│
├── manage.py             # Script de utilidades do Django.
└── ...
```

##### **3.2. Frontend (`frontend/src/`)**

```
frontend/
└── src/
    ├── api/axios.js      # Configuração central do cliente HTTP.
    ├── theme/theme.js    # A "Bíblia de Estilo" do Projeto Phoenix.
    │
    ├── components/
    │   ├── MainLayout.js:      O esqueleto responsivo (Desktop/Mobile) da aplicação.
    │   ├── PulseHeader.js:     O "Pulso da Manhã", nosso header dinâmico do Dashboard.
    │   ├── RobotCard.js:       O "Dossiê de Performance", cartão de apresentação dos robôs.
    │   ├── MetricCard.js:      Sub-componente para exibição de métricas.
    │   ├── MarketTicker.js:    A barra de cotações no rodapé.
    │   └── ... (Modais, Gráficos, etc.)
    │
    └── pages/
        ├── DashboardPage.js:       A "Sala de Comando". Orquestra o `PulseHeader`,
        │                         a "Frota Ativa" e o "Radar de Oportunidades".
        ├── RobotDetailPage.js:     A vitrine completa de uma estratégia, com o gráfico
        │                         principal e o dossiê completo de métricas.
        ├── OperationsPage.js:      A "Mesa de Análise Pós-Voo", com cards de posição e
        │                         tabela de histórico inteligente.
        ├── PortfolioOptimizerPage.js: O "Co-Piloto IA", nossa experiência de
        │                              consultoria guiada.
        └── ... (Login, Contas, Perfil)
```
---
#### **Seção 4: Desafios Críticos e Soluções Encontradas (A Jornada de P&D)**

A transição de um protótipo para um motor quantitativo robusto foi uma jornada marcada por desafios críticos. Cada erro foi uma lição que fortaleceu nossa arquitetura.

*   **Desafio 1: A Ilusão do `Lookahead Bias`**
    *   **Problema:** Nossos resultados de backtest iniciais eram fantasticamente irreais (ex: 95% de Win Rate). A análise profunda revelou que a lógica de entrada usava informações do fechamento do candle para tomar uma decisão naquele mesmo candle, uma "trapaça" que é impossível em tempo real.
    *   **Solução:** Re-arquitetura completa do pipeline. A geração de "alertas" foi separada da "tomada de decisão". A IA agora analisa as condições no fechamento do candle de sinal e a execução ocorre no candle *seguinte*, eliminando o viés.

*   **Desafio 2: O Perigo do `Data Leakage`**
    *   **Problema:** Os resultados continuavam otimistas demais. Descobrimos que, ao treinar a IA, estávamos usando `train_test_split` aleatório. Isso permitia que o modelo fosse treinado com dados do futuro para prever o passado.
    *   **Solução:** Implementação do **Walk-Forward Analysis** como padrão ouro. O `backtester.py` agora orquestra um loop onde a IA é sempre treinada em um bloco de dados do passado e testada em um bloco de dados do futuro, garantindo que a performance reportada seja honesta.

*   **Desafio 3: A Miragem do Risco Fixo**
    *   **Problema:** O Drawdown Máximo parecia irrealisticamente baixo (ex: 1.08%). A causa era a simulação da biblioteca `backtesting`, que usa um tamanho de lote fixo, mascarando o risco percentual real à medida que o capital crescia.
    *   **Solução:** Abandono da simulação financeira da biblioteca. Construímos nosso próprio motor em `portfolio_analyzer.py`, que executa uma simulação trade a trade aplicando uma regra de **risco percentual sobre o capital dinâmico**, revelando o drawdown verdadeiro da estratégia.

*   **Desafio 4: A Saga das Migrações e Tipos de Dados**
    *   **Problema:** Encontramos uma série de erros (`AttributeError`, `KeyError`, `OperationalError`, `TypeError`) que impediam a execução. As causas variavam de inconsistências de nomenclatura (`high` vs `High`), migrações de banco de dados quebradas e, o mais persistente, a falha em converter tipos de dados do NumPy/Pandas para tipos nativos do Python antes de salvar no JSONField do Django.
    *   **Solução:** Padronização da nomenclatura, implementação do protocolo de reset de banco de dados "Terra Arrasada" para resolver conflitos de migração, e a blindagem final do `portfolio_analyzer.py` para garantir que ele converta **explicitamente** cada valor para um tipo JSON-safe antes de retornar os resultados.

---
#### **Seção 5: Onde Estamos e o que Falta**

*   **O que Fizemos (Sprints 1, 2 e 3 Concluídos):**
    *   **Construímos a "Fábrica":** Um motor `quant_engine` completo, robusto e à prova de viés, capaz de validar e otimizar estratégias de portfólio complexas.
    *   **Forjamos o "Produto":** Criamos e validamos o **"Portfólio Quimera Global"**, nosso primeiro produto de elite, com performance honesta e robusta.
    *   **Reimaginamos a "Experiência":** O frontend foi completamente redesenhado sob a filosofia "Phoenix", resultando em uma interface de usuário de nível mundial, responsiva e focada em clareza e estética funcional.

*   **Onde Estamos:**
    *   A plataforma está **100% funcional em ambiente de desenvolvimento**. O backtest é executado com sucesso, os dados são salvos corretamente e a interface reflete os resultados de forma precisa e profissional. A aplicação está **Pronta para o Lançamento Interno**.

*   **O que Falta (Roadmap Futuro):**
    *   **Sprint 4 - Ativação do Motor de Execução (Prioridade Máxima):**
        1.  Dar vida à tarefa `monitor_robot_instance_task` em `tasks.py`. Esta tarefa será o "worker" de tempo real que irá:
            *   Verificar os robôs ativos.
            *   Baixar os dados de mercado mais recentes.
            *   Executar a lógica de `gerar_alertas` e `definir_features`.
            *   Usar o modelo de IA treinado (ou treiná-lo em tempo real, uma decisão de arquitetura que tomaremos).
            *   Se a previsão for `1`, conectar-se à conta MT5 do cliente e **executar a ordem real**.
    *   **Sprint 5 - Deploy e Lançamento Interno:**
        1.  Executar o plano de deploy em uma VPS Windows.
        2.  Liberar o acesso para o grupo de 20 testadores em contas demo.
        3.  Coletar feedback e monitorar a performance em tempo real.
    *   **Fases Futuras (Pós-Lançamento):** Implementar o "Centro de Notificações", a "Análise da Aura" com LLM, e a revolucionária "Birdstone Algo-Gen™".

---
#### **Seção 6: Cofre de Credenciais e Acessos**

*   **Repositório Git:** `https://github.com/RenatoVargasF/Game.git` (Branch: `main`)
*   **Acesso ao Admin Local:** `http://127.0.0.1:8000/admin/`
    *   **Usuário:** (definido no `createsuperuser`)
    *   **Senha:** (definida no `createsuperuser`)
*   **Conta de Teste MetaTrader 5 (Infinox):**
    *   **Login:** `100072107`
    *   **Senha:** `c1758B!2`
    *   **Servidor:** `InfinoxLimited-MT5Demo`
*   **Chaves de Ambiente (`.env`):**
    *   **`SECRET_KEY`:** `#W(Dt9y-!r@uh9:LZ)E0ZWV]]G^0>%` (Gerar uma nova para produção)
    *   **`ENCRYPTION_KEY`:** `mZJ-Ig38L04L27-a9kHwSxfb4kFqFe7h5eGzY-4u2eM=`
    *   **`OPENAI_API_KEY`:** `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` (Para fases futuras)

---
#### **Seção 7: Protocolo de Inicialização do Ambiente**

1.  **Pré-requisitos:** Conda, Python 3.9, Node.js.
2.  **Clonar o Repositório:** `git clone https://github.com/RenatoVargasF/Game.git`
3.  **Ambiente Backend (`projeto_trader_env`):**
    *   `conda create --name projeto_trader_env python=3.9`
    *   `conda activate projeto_trader_env`
    *   `pip install -r requirements.txt`
4.  **Banco de Dados (Primeira vez ou Reset):**
    *   (Se `db.sqlite3` não existir) `python manage.py makemigrations robots`
    *   `python manage.py migrate`
    *   `python manage.py createsuperuser`
5.  **Ambiente Frontend:**
    *   `cd frontend`
    *   `npm install`
6.  **Execução (4 Componentes):**
    *   Terminal 1 (Worker): `python manage.py process_tasks`
    *   Terminal 2 (Backend): `python manage.py runserver`
    *   Terminal 3 (Frontend): `npm start`
    *   Aplicação Externa: Manter o MT5 aberto e logado.

---
#### **Seção 8: Guia de Cadastro de Estratégias**

Para cadastrar o "Portfólio Quimera Global":

*   **Name:** `Portfólio Quimera Global`
*   **Description:** `Uma estratégia de portfólio diversificada...`
*   **Assets:** `EURUSD, GBPUSD, XAUUSD, USDJPY, NZDUSD, USDCAD, USDCHF`
*   **Timeframe:** `M15`
*   **Suggested Capital:** `500.00`
*   **Portfolio Composition:** (Colar o JSON completo dos 7 ativos)
*   **Strategy File:** `hunter_x`
*   **Is Public:** Marcar

RenatoBirdstone2025@#$