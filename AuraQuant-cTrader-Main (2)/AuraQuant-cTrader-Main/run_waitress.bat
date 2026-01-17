@echo off
echo Iniciando Servidor Backend Birdstone (Waitress) na porta 8000...
echo.
echo ATENCAO: Certifique-se de que o ambiente Conda/Python correto (ex: 'conda activate projeto_trader_env') esta ATIVO.
echo.
C:\Users\Renato\miniconda3\envs\projeto_trader_env\Scripts\waitress-serve --host=127.0.0.1 --port=8000 core.wsgi:application