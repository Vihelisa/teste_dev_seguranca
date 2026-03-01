"""
Script de Teste de Latência — Pipeline de Decisão ML
Objetivo: Medir tempo total de Tick → Decisão → Ordem
Meta: < 500ms para evitar stale quotes
"""

import os
import sys
import django
import time
import statistics
from decimal import Decimal

# Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from trading_platform.models import Strategy, ActiveRobotInstance, TradingAccount, User
from trading_platform.quant_engine.decision_engine import analyze_and_get_signal
import importlib
import joblib

print("="*80)
print("TESTE DE LATÊNCIA — PIPELINE DE DECISÃO ML")
print("="*80)
print("Meta: < 500ms do tick até ordem pronta para envio")
print("="*80)

# ============================================================================
# SETUP — Carregar estratégia e modelo
# ============================================================================

try:
    strategy = Strategy.objects.get(id=1)
    print(f"\n✅ Estratégia carregada: {strategy.name}")
    print(f"   Arquivo: {strategy.strategy_file}")
except Strategy.DoesNotExist:
    print("\n❌ ERRO: Estratégia ID=1 não encontrada!")
    sys.exit(1)

# Carregar StrategyContract
try:
    strategy_file_name = strategy.strategy_file.replace('.py', '')
    module_path = f"trading_platform.quant_engine.strategies.{strategy_file_name}"
    StrategyContract = importlib.import_module(module_path)
    print(f"✅ StrategyContract carregado")
except Exception as e:
    print(f"❌ ERRO ao carregar StrategyContract: {e}")
    sys.exit(1)

# Carregar modelo ML
if not strategy.ml_model_path:
    print("❌ ERRO: Estratégia não tem modelo ML treinado!")
    print("   Rode: python validate_ml_pipeline.py primeiro")
    sys.exit(1)

try:
    model_path = os.path.join('media', strategy.ml_model_path.name)
    saved_ia = joblib.load(model_path)
    print(f"✅ Modelo ML carregado: {model_path}")
    print(f"   Features: {len(saved_ia['features'])}")
    print(f"   Threshold: {saved_ia.get('optimal_threshold', 'N/A')}")
except Exception as e:
    print(f"❌ ERRO ao carregar modelo: {e}")
    sys.exit(1)

# Criar instância fake para teste
try:
    user = User.objects.first()
    account = TradingAccount.objects.first()
    
    if not user or not account:
        print("❌ ERRO: Precisa ter pelo menos 1 usuário e 1 conta no banco!")
        sys.exit(1)
    
    # Instância temporária (não salva no banco)
    instance = ActiveRobotInstance(
        user=user,
        trading_account=account,
        strategy=strategy,
        lot_size=Decimal('0.01'),
        risk_mode='FIXED',
        is_active=True
    )
    print(f"✅ Instância de teste criada (em memória)")
except Exception as e:
    print(f"❌ ERRO ao criar instância: {e}")
    sys.exit(1)

# ============================================================================
# TESTE DE LATÊNCIA — 100 ITERAÇÕES
# ============================================================================

print("\n" + "="*80)
print("INICIANDO TESTES DE LATÊNCIA")
print("="*80)
print("Executando 100 chamadas ao decision_engine...\n")

latencies = []
successful_decisions = 0
failed_decisions = 0

# Simular preço FIX atual
simulated_fix_price = Decimal('1.10500')

for i in range(100):
    try:
        # Marca início
        start_time = time.time()
        
        # Chama o decision engine (simula tick chegando)
        trade_request = analyze_and_get_signal(
            instance=instance,
            StrategyContract=StrategyContract,
            saved_ia=saved_ia,
            log_prefix=f"[LATENCY_TEST #{i+1}]",
            fix_current_price=simulated_fix_price
        )
        
        # Marca fim
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000  # Converte para ms
        
        latencies.append(latency_ms)
        
        if trade_request:
            successful_decisions += 1
        else:
            failed_decisions += 1
        
        # Progresso a cada 10 iterações
        if (i + 1) % 10 == 0:
            avg_so_far = statistics.mean(latencies)
            print(f"   Progresso: {i+1}/100 | Média até agora: {avg_so_far:.2f}ms")
    
    except Exception as e:
        print(f"   ⚠️  Iteração {i+1} falhou: {e}")
        failed_decisions += 1

# ============================================================================
# ANÁLISE DOS RESULTADOS
# ============================================================================

print("\n" + "="*80)
print("RESULTADOS DO TESTE DE LATÊNCIA")
print("="*80)

if not latencies:
    print("❌ ERRO: Nenhuma medição bem-sucedida!")
    sys.exit(1)

# Estatísticas
mean_latency = statistics.mean(latencies)
median_latency = statistics.median(latencies)
min_latency = min(latencies)
max_latency = max(latencies)
stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0

# Percentis
sorted_latencies = sorted(latencies)
p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]

print(f"\n📊 ESTATÍSTICAS DE LATÊNCIA (em milissegundos):")
print(f"   Média:       {mean_latency:.2f} ms")
print(f"   Mediana:     {median_latency:.2f} ms")
print(f"   Mínima:      {min_latency:.2f} ms")
print(f"   Máxima:      {max_latency:.2f} ms")
print(f"   Desvio Padrão: {stdev_latency:.2f} ms")
print(f"   P95 (95%):   {p95_latency:.2f} ms")
print(f"   P99 (99%):   {p99_latency:.2f} ms")

print(f"\n📈 RESULTADOS:")
print(f"   Decisões bem-sucedidas: {successful_decisions}")
print(f"   Decisões que falharam:  {failed_decisions}")
print(f"   Taxa de sucesso:        {(successful_decisions/100)*100:.1f}%")

# ============================================================================
# AVALIAÇÃO FINAL
# ============================================================================

print("\n" + "="*80)
print("AVALIAÇÃO FINAL")
print("="*80)

# Meta: < 500ms
if mean_latency < 500:
    print(f"\n✅ APROVADO! Latência média ({mean_latency:.2f}ms) < 500ms")
    if p95_latency < 500:
        print(f"✅ EXCELENTE! 95% das requisições < 500ms")
    else:
        print(f"⚠️  ATENÇÃO: P95 ({p95_latency:.2f}ms) >= 500ms")
        print(f"   5% das requisições podem ter latência alta")
else:
    print(f"\n❌ REPROVADO! Latência média ({mean_latency:.2f}ms) >= 500ms")
    print(f"   RISCO: Pode executar ordens com preços desatualizados (stale quotes)")

# Análise de componentes
print("\n📋 PRÓXIMOS PASSOS:")

if mean_latency < 100:
    print("   ✅ Latência excelente! Sistema pronto para produção.")
elif mean_latency < 300:
    print("   ✅ Latência boa! Sistema aceitável para produção.")
elif mean_latency < 500:
    print("   ⚠️  Latência aceitável mas pode melhorar.")
    print("   Sugestões de otimização:")
    print("      - Usar cache Redis para features calculadas")
    print("      - Pre-carregar modelos ML na inicialização")
else:
    print("   ❌ Latência alta! Otimizações necessárias antes de produção.")
    print("   Possíveis gargalos:")
    print("      - data_processor.prepare_data_for_assets() muito lento")
    print("      - Modelo ML muito complexo")
    print("      - Conexão MT5 lenta")
    print("   Sugestão: Implementar TimescaleDB para cache de ticks")

print("\n" + "="*80)