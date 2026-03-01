"""
Script de Validação do Pipeline de Machine Learning
Objetivo: Testar o backtest completo da estratégia Liquidity Hunter
"""

import os
import sys
import django

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from trading_platform.models import Strategy
from trading_platform.quant_engine import backtester
import json

print("="*80)
print("VALIDAÇÃO DO PIPELINE DE MACHINE LEARNING")
print("="*80)

# Buscar a estratégia Liquidity Hunter
try:
    strategy = Strategy.objects.get(id=1)
    print(f"\n✅ Estratégia encontrada: {strategy.name}")
    print(f"   Arquivo: {strategy.strategy_file}")
    print(f"   Ativos: {strategy.assets}")
    print(f"   Período backtest: {strategy.backtest_period_days} dias")
except Strategy.DoesNotExist:
    print("\n❌ ERRO: Estratégia ID=1 não encontrada no banco!")
    sys.exit(1)

# Remover .py se já estiver no nome
strategy_file_name = strategy.strategy_file.replace('.py', '')

# Validar se o arquivo da estratégia existe
strategy_file_path = f"trading_platform/quant_engine/strategies/{strategy_file_name}.py"
if not os.path.exists(strategy_file_path):
    print(f"\n❌ ERRO: Arquivo da estratégia não encontrado: {strategy_file_path}")
    sys.exit(1)

print(f"✅ Arquivo da estratégia existe: {strategy_file_path}")

# Rodar o backtest
print("\n" + "-"*80)
print("INICIANDO BACKTEST...")
print("-"*80)

try:
    assets = [asset.strip() for asset in strategy.assets.split(',')]
    
    results = backtester.run_strategy_backtest(
        strategy_name=strategy_file_name,  # ← SEM .py
        strategy_id=strategy.id,
        assets=assets,
        params=strategy.portfolio_composition,
        capital_inicial=float(strategy.suggested_capital),
        dias=strategy.backtest_period_days
    )
    
    print("\n" + "="*80)
    print("RESULTADOS DO BACKTEST")
    print("="*80)
    
    if not results:
        print("❌ Backtest retornou resultados vazios!")
        sys.exit(1)
    
    # Exibir resultados principais
    status = results.get('status', 'N/A')
    print(f"\nStatus: {status}")
    
    if 'results' in results and results['results']:
        metrics = results['results']
        print("\n📊 MÉTRICAS PRINCIPAIS:")
        print(f"   Retorno Total: {metrics.get('Retorno Total [%]', 'N/A')}%")
        print(f"   Sharpe Ratio: {metrics.get('Sharpe Ratio', 'N/A')}")
        print(f"   Win Rate: {metrics.get('Taxa de Acerto (Win Rate) [%]', 'N/A')}%")
        print(f"   Drawdown Máximo: {metrics.get('Drawdown Máximo [%]', 'N/A')}%")
        print(f"   Nº de Trades: {metrics.get('Nº de Trades Total', 'N/A')}")
    
    # Verificar se o modelo foi salvo
    model_path = results.get('model_path')
    if model_path:
        full_model_path = os.path.join('media', model_path)
        if os.path.exists(full_model_path):
            print(f"\n✅ Modelo ML salvo com sucesso!")
            print(f"   Caminho: {model_path}")
            
            # Verificar tamanho do arquivo
            size_kb = os.path.getsize(full_model_path) / 1024
            print(f"   Tamanho: {size_kb:.2f} KB")
        else:
            print(f"\n⚠️ AVISO: Caminho do modelo retornado mas arquivo não existe!")
            print(f"   Esperado em: {full_model_path}")
    else:
        print("\n⚠️ AVISO: Nenhum modelo foi salvo (status pode ser NO_TRADES)")
    
    # Salvar resultados no banco
    print("\n" + "-"*80)
    print("SALVANDO RESULTADOS NO BANCO...")
    print("-"*80)
    
    strategy.backtest_results = results.get('results', {})
    if model_path:
        strategy.ml_model_path = model_path
    strategy.save()
    
    print("✅ Estratégia atualizada no banco de dados!")
    
    print("\n" + "="*80)
    print("VALIDAÇÃO CONCLUÍDA COM SUCESSO! ✅")
    print("="*80)
    
    '''print("\n📋 PRÓXIMOS PASSOS:")
    print("   1. Verifique se as métricas estão aceitáveis")
    print("   2. Se Win Rate > 55% e Sharpe > 1.0, o modelo está bom")
    print("   3. Pode prosseguir para TimescaleDB (Fase 1.2.1)")'''
    
except Exception as e:
    print(f"\n❌ ERRO durante o backtest: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)