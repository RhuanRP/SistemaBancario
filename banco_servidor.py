import socket
import threading
import json
from collections import defaultdict
from threading import Lock, Semaphore
from pprint import pprint
from colorama import Fore, Style, init

init(autoreset=True)

contas = defaultdict(lambda: {"saldo": 0})
contas_lock = defaultdict(Lock)
operacoes_lock = Lock()
semaphore = Semaphore(4)

def carregar_dados():
    try:
        with open("contas.json", "r") as file:
            global contas
            contas = defaultdict(lambda: {"saldo": 0}, json.load(file))
    except FileNotFoundError:
        print(f"{Fore.YELLOW}Arquivo de dados não encontrado, iniciando com contas vazias.")

def salvar_dados():
    with open("contas.json", "w") as file:
        json.dump(contas, file, indent=4)

def processar_transacoes(cliente_socket, endereco):
    with semaphore:
        try:
            while True:
                dados = cliente_socket.recv(1024).decode()
                if not dados:
                    break
                
                operacao = json.loads(dados)
                tipo = operacao["tipo"]
                numero_conta = operacao["numero_conta"]

                with contas_lock[numero_conta]:
                    if tipo == "deposito":
                        valor = operacao["valor"]
                        contas[numero_conta]["saldo"] += valor
                        resultado = f"Depósito de {valor} realizado com sucesso."

                    elif tipo == "saque":
                        valor = operacao["valor"]
                        if contas[numero_conta]["saldo"] >= valor:
                            contas[numero_conta]["saldo"] -= valor
                            resultado = f"Saque de {valor} realizado com sucesso."
                        else:
                            resultado = f"Saldo insuficiente para saque de {valor}."

                    elif tipo == "consulta":
                        saldo = contas[numero_conta]["saldo"]
                        resultado = f"Saldo atual: {saldo}."

                    # Imprime a transação processada no servidor
                    with operacoes_lock:
                        print(f"{Fore.GREEN}{tipo.capitalize()} na conta {numero_conta} de {endereco}:")
                        pprint(operacao)
                        print(f"{Fore.CYAN}Resultado: {resultado}")

                    salvar_dados()

                    cliente_socket.send(resultado.encode())

        except Exception as e:
            print(f"{Fore.RED}Erro ao processar transações do cliente {endereco}: {e}")
        finally:
            cliente_socket.close()
            print(f"{Fore.YELLOW}Conexão com o cliente {endereco} encerrada.")

def iniciar_servidor():
    carregar_dados()
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind(("localhost", 12345))
    servidor_socket.listen(5)
    print(f"{Fore.GREEN}Servidor bancário iniciado e aguardando conexões...")

    try:
        while True:
            cliente_socket, endereco = servidor_socket.accept()
            print(f"{Fore.BLUE}Conexão estabelecida com {endereco}")

            threading.Thread(target=processar_transacoes, args=(cliente_socket, endereco)).start()

    except KeyboardInterrupt:
        print(f"{Fore.RED}Encerrando servidor bancário...")
    finally:
        servidor_socket.close()
        salvar_dados()
        print(f"{Fore.GREEN}Servidor encerrado.")

if __name__ == "__main__":
    iniciar_servidor()
