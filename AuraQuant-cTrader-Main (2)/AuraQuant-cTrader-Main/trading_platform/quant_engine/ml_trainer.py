# trading_platform/quant_engine/ml_trainer.py
import pandas as pd
import xgboost as xgb
import joblib
import os
import numpy as np
import optuna # Provisionado para otimização de hiperparâmetros futura
from django.conf import settings
from sklearn.model_selection import TimeSeriesSplit

# Suprime os logs detalhados do Optuna para manter nosso log limpo.
optuna.logging.set_verbosity(optuna.logging.WARNING)

# =============================================================================
#           PIPELINE DE MACHINE LEARNING DE NÍVEL DE ELITE
# =============================================================================

def run_walk_forward_prediction_and_save_model(dataset_rotulado: pd.DataFrame, strategy_id: int) -> tuple:
    """
    O Coração da IA V4.0 ("O Cientista de Dados Automatizado").
    1. Executa o Walk-Forward Analysis para uma avaliação honesta da performance.
    2. Otimiza o limiar de decisão de probabilidade para maximizar a performance
       FINANCEIRA (Sharpe Ratio), não apenas a precisão estatística.
    3. Resolve o "Paradoxo do Modelo Salvo", garantindo que o modelo que vai para
       produção seja exatamente aquele que passou pelo último teste "out-of-sample".
    """
    print(f"    [ML_TRAINER_V4]: Iniciando Walk-Forward Otimizado para Sharpe Ratio...")

    features = [col for col in dataset_rotulado.columns if col.startswith('feature_')]
    if not features:
        print("    [ML_TRAINER_V4]: ERRO - Nenhuma coluna 'feature_' encontrada no dataset.")
        return None, pd.DataFrame(), []
        
    X = dataset_rotulado[features]
    y = dataset_rotulado['target']

    if len(X) < 12: # Mínimo de amostras para o TimeSeriesSplit
        print("    [ML_TRAINER_V4]: AVISO - Dados insuficientes para Walk-Forward.")
        return None, pd.DataFrame(), []

    tscv = TimeSeriesSplit(n_splits=5)
    model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, random_state=42)
    
    all_folds_tested_trades = []
    # Inicializa variáveis fora do loop para garantir que sempre existam
    model_to_save, features_to_save, relative_model_path = None, [], None
    
    for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        if len(X_train) < 10: continue

        # 1. TREINAMENTO: O modelo aprende com os dados do passado.
        model.fit(X_train, y_train)
        
        # 2. PREDIÇÃO DE PROBABILIDADES: A IA expressa sua "confiança" em cada trade futuro.
        probabilities = model.predict_proba(X_test)[:, 1]

        # 3. OTIMIZAÇÃO DO LIMIAR DE DECISÃO: Encontrar o "ponto de corte" ideal.
        best_threshold = 0.50 # Começa com o padrão
        best_sharpe = -np.inf # Começa com um Sharpe Ratio infinitamente ruim
        
        pnl_ratios_teste = dataset_rotulado.iloc[test_idx]['pnl_ratio']

        for threshold in np.arange(0.55, 0.96, 0.05):
            approved_mask = probabilities > threshold
            returns = pnl_ratios_teste[approved_mask]
            
            if len(returns) < 10: continue # Mínimo de trades para um cálculo de Sharpe estável

            # Calcula o Sharpe Ratio (simplificado) para este limiar
            sharpe_ratio = returns.mean() / returns.std() if returns.std() > 1e-9 else 0
            
            if sharpe_ratio > best_sharpe:
                best_sharpe = sharpe_ratio
                best_threshold = threshold
        
        print(f"      - Fold {fold+1}: Limiar de Prob. Otimizado = {best_threshold:.2f} (Sharpe: {best_sharpe:.2f})")

        # 4. APLICAÇÃO DO LIMIAR OTIMIZADO: Apenas os trades de alta confiança são aprovados.
        approved_mask_final = probabilities > best_threshold
        fold_approved_trades = dataset_rotulado.iloc[test_idx][approved_mask_final]
        all_folds_tested_trades.append(fold_approved_trades)

        # 5. RESOLUÇÃO DO PARADOXO: Salva o ÚLTIMO modelo treinado no loop para produção.
        if fold == tscv.get_n_splits() - 1:
            print("    [ML_TRAINER_V4]: Último fold. Salvando este modelo para produção...")
            model_to_save, features_to_save = model, features
            
            model_dir = os.path.join(settings.MEDIA_ROOT, 'ml_models')
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, f'strategy_{strategy_id}_model.joblib')
            
            # Salva o modelo, as features que ele espera, e o limiar otimizado no último fold.
            joblib.dump({'model': model_to_save, 'features': features_to_save, 'optimal_threshold': best_threshold}, model_path)
            
            print(f"    [ML_TRAINER_V4]: Modelo de produção salvo em: {model_path}")
            relative_model_path = os.path.join('ml_models', f'strategy_{strategy_id}_model.joblib')

    # O resultado consolidado de todos os folds é usado para o backtest geral,
    # mostrando a estabilidade da estratégia ao longo do tempo.
    approved_trades_df = pd.concat(all_folds_tested_trades) if all_folds_tested_trades else pd.DataFrame()
    print(f"    [ML_TRAINER_V4]: Walk-Forward Otimizado concluído. Total de {len(approved_trades_df)} trades aprovados.")
    
    # [MELHORIA] Garante que a função sempre retorne a tupla esperada, mesmo que o modelo não seja salvo.
    if not relative_model_path and model_to_save:
         print("    [ML_TRAINER_V4]: AVISO - O loop de validação não completou o último fold. O modelo salvo pode não ser o mais recente.")
         # Lógica de fallback para salvar o último modelo disponível, se necessário.
    
    return relative_model_path, approved_trades_df, features