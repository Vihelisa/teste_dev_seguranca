@echo off
echo Iniciando Celery Worker - Fila de Baixa Prioridade: backtesting_heavy...
cd C:\birdstone
C:\Users\Renato\miniconda3\envs\projeto_trader_env\Scripts\celery -A core worker --pool=solo -l info -Q backtesting_heavy -c 1