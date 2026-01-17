import MetaTrader5 as mt5

login = 100078703 # <--- Use o login correto
password = "2f8e!Nn2" # <--- Use a senha correta
server = "InfinoxLimited-MT5Demo" # <--- Use o servidor correto

print("Tentando inicializar a conexão...")

if not mt5.initialize(login=login, password=password, server=server, timeout=60000):
    print("initialize() falhou, código do erro =", mt5.last_error())
    quit()

print("Conexão bem-sucedida!")
print(mt5.account_info())

mt5.shutdown()
print("Conexão encerrada.")