@echo off
echo Iniciando Celery Beat Scheduler...
cd C:\birdstone
C:\Users\Renato\miniconda3\envs\projeto_trader_env\Scripts\celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler