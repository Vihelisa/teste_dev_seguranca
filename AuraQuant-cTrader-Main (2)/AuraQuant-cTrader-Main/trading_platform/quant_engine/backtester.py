# trading_platform/quant_engine/backtester.py
import pandas as pd
from pprint import pprint
import traceback
import importlib
from . import data_processor, ml_trainer, portfolio_analyzer

def run_strategy_backtest(strategy_name: str, strategy_id: int, assets: list, params: dict, capital_inicial: float, dias: int) -> dict:
    """
    Motor de Backtest Universal V12 (Produção).
    Orquestra o pipeline com uma filosofia de "Confie, mas Verifique" e um
    fluxo de dados claro e sem ambiguidades.
    """
    print(f"\n[BACKTESTER_V12] INICIANDO VALIDAÇÃO: '{strategy_name.upper()}' (ID: {strategy_id})")
    try:
        # 1. CARREGAR O CONTRATO DA ESTRATÉGIA
        strategy_module = importlib.import_module(f".strategies.{strategy_name}", package='trading_platform.quant_engine')
        if not hasattr(strategy_module, 'StrategyContract'):
            raise AttributeError(f"Arquivo '{strategy_name}.py' não tem a classe 'StrategyContract'.")
        StrategyContract = strategy_module.StrategyContract

        # 2. COLETAR OS DADOS DE MERCADO
        market_data = data_processor.prepare_data_for_assets(assets, dias=dias)
        if market_data is None:
            raise ValueError("A coleta de dados falhou ou não retornou dados.")

        all_trades_to_process = pd.DataFrame()
        
        # 3. EXECUTAR E VALIDAR O PIPELINE PARA CADA ATIVO/PAR
        if isinstance(market_data, dict): # Múltiplos ativos (Portfólio)
            for asset_name, df_asset in market_data.items():
                asset_params = params.get(asset_name, {})
                potential_trades_df = _run_and_validate_pipeline_for_asset(StrategyContract, df_asset, asset_params, asset_name)
                if potential_trades_df is not None and not potential_trades_df.empty:
                    all_trades_to_process = pd.concat([all_trades_to_process, potential_trades_df])
        else: # Ativo Único ou Par
            param_key = ",".join(assets)
            potential_trades_df = _run_and_validate_pipeline_for_asset(StrategyContract, market_data, params.get(param_key, {}), param_key)
            if potential_trades_df is not None and not potential_trades_df.empty:
                all_trades_to_process = pd.concat([all_trades_to_process, potential_trades_df])

        # 4. TRATAMENTO GRACIOSO DE "NENHUM TRADE"
        if all_trades_to_process.empty:
            print(f"\n[BACKTESTER_V12] Nenhuma oportunidade de trade foi gerada por '{strategy_name}'. Fim da execução.")
            return {
                "status": "NO_TRADES_GENERATED", 
                "model_path": None, 
                "results": {"Nº de Trades Total": 0, "Retorno Total [%]": 0.0}
            }

    except Exception:
        print(f"!!!!!! [BACKTESTER_V12] FALHA CRÍTICA no pipeline de preparação: {traceback.format_exc()} !!!!!!")
        return {}

    all_trades_to_process.sort_values(by='time_entrada', inplace=True, ignore_index=True)

    # 5. TREINAR A IA E FILTRAR TRADES
    print(f"\n--- Total de {len(all_trades_to_process)} trades potenciais gerados. Entregando para o ml_trainer... ---")
    relative_model_path, approved_trades_df, _ = ml_trainer.run_walk_forward_prediction_and_save_model(
        dataset_rotulado=all_trades_to_process.copy(), 
        strategy_id=strategy_id
    )

    if approved_trades_df.empty:
        print("\n[BACKTESTER_V12] Nenhum trade foi aprovado pela IA.")
        return {"status": "NO_TRADES_APPROVED", "model_path": relative_model_path, "results": {}}

    # 6. EXECUTAR A SIMULAÇÃO FINANCEIRA FINAL
    print("\n--- Iniciando simulação financeira final... ---")
    portfolio_stats = portfolio_analyzer.run_financial_simulation(approved_trades_df, capital_inicial, dias)
    
    print("\n" + "#"*30 + " RELATÓRIO DE PERFORMANCE CONSOLIDADO " + "#"*30)
    pprint(portfolio_stats)
    
    # 7. RETORNAR O PACOTE DE RESULTADOS COMPLETO
    return {
        "results": portfolio_stats,
        "model_path": relative_model_path
    }


def _run_and_validate_pipeline_for_asset(StrategyContract, df_mercado: pd.DataFrame, params: dict, asset_name: str) -> pd.DataFrame:
    """
    (PRIVADO) V2.1 - Roda o pipeline de um ativo, delega responsabilidades
    e valida o contrato de dados retornado. Versão limpa para produção.
    """
    print(f"--- Processando pipeline para: {asset_name} ---")
    
    # Etapa 1: Enriquecer os dados brutos com indicadores.
    df_featured = StrategyContract.add_indicators(df_mercado, params)
    if df_featured is None or df_featured.empty: return None
    
    # Etapa 2: Gerar os alertas (eventos de interesse).
    alertas = StrategyContract.generate_alerts(df_featured, params)
    if alertas is None or alertas.empty: return None
    
    # Etapa 3: Transformar alertas em 'trades potenciais' com features.
    dataset_para_ia = StrategyContract.define_decision_points_and_features(alertas, df_featured, params)
    if dataset_para_ia is None or dataset_para_ia.empty: return None
    
    # Etapa 4: Rotular os dados usando o método padrão (pode ser trocado aqui).
    # Para usar a IA Estrategista, a chamada seria: portfolio_analyzer.discover_trade_potential_for_ai(...)
    dataset_rotulado = portfolio_analyzer.label_trades_with_fixed_targets(dataset_para_ia, df_featured, params)
    if dataset_rotulado is None or dataset_rotulado.empty: return None

    dataset_rotulado['Asset'] = asset_name
    
    # Etapa 5: VALIDAÇÃO DO CONTRATO
    is_pairs = 'zscore_entrada' in dataset_rotulado.columns
    # Para IA Estrategista, o Risco/Retorno pode não ser necessário, então a validação pode ser ajustada.
    # Por enquanto, a mantemos para as estratégias de regras fixas.
    has_risco_retorno = 'Risco_Retorno' in dataset_rotulado.columns and dataset_rotulado['Risco_Retorno'].notnull().any()
    
    if is_pairs and has_risco_retorno:
        raise ValueError(f"CONTRATO QUEBRADO: A estratégia de par '{asset_name}' retornou 'Risco_Retorno'.")
    if not is_pairs and not has_risco_retorno:
        raise ValueError(f"CONTRATO QUEBRADO: A estratégia de ativo único '{asset_name}' NÃO retornou 'Risco_Retorno'.")
            
    return dataset_rotulado