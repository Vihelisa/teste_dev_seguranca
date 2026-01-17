@echo off
echo Iniciando Celery Worker - Fila de Alta Prioridade: realtime_trading...
cd C:\birdstone
C:\Users\Renato\miniconda3\envs\projeto_trader_env\Scripts\celery -A core worker --pool=solo -l info -Q realtime_trading