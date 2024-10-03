import socket
import threading
import json
import time

lock = threading.Lock()
semaphore = threading.Semaphore(7)

try:
    with open('contas.json', 'r') as file:
        contas = json.load(file)
except FileNotFoundError:
    contas = {}

def salvar_contas():
    with open('contas.json', 'w') as file: 
        json.dump(contas, file, indent=4) 

def processar_requisicao(cliente_socket):
    global contas

    try:
        dados = cliente_socket.recv(1024).decode()
        operacao = json.loads(dados)
        resposta = ""

        with semaphore:
            if operacao['tipo'] == 'deposito':
                with lock:
                    contas[operacao['conta']] = contas.get(operacao['conta'], 0) + operacao['valor']
                    resposta = f"Depósito de {operacao['valor']} na conta {operacao['conta']} realizado com sucesso."
            elif operacao['tipo'] == 'saque':
                with lock:
                    if contas.get(operacao['conta'], 0) >= operacao['valor']:
                        contas[operacao['conta']] -= operacao['valor']
                        resposta = f"Saque de {operacao['valor']} da conta {operacao['conta']} realizado com sucesso."
                    else:
                        resposta = "Saldo insuficiente."
            elif operacao['tipo'] == 'consulta':
                saldo = contas.get(operacao['conta'], 0)
                resposta = f"Saldo da conta {operacao['conta']}: {saldo}."
            elif operacao['tipo'] == 'transferencia':
                with lock:
                    if contas.get(operacao['conta_origem'], 0) >= operacao['valor']:
                        contas[operacao['conta_origem']] -= operacao['valor']
                        contas[operacao['conta_destino']] = contas.get(operacao['conta_destino'], 0) + operacao['valor']
                        resposta = f"Transferência de {operacao['valor']} da conta {operacao['conta_origem']} para a conta {operacao['conta_destino']} realizada com sucesso."
                    else:
                        resposta = "Saldo insuficiente para transferência."
        
        salvar_contas()
        cliente_socket.send(resposta.encode())
    except Exception as e:
        cliente_socket.send(f"Erro: {str(e)}".encode())
    finally:
        cliente_socket.close()

def servidor_bancario():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('localhost', 12345))
    servidor.listen(5)
    print("Servidor bancário iniciado e aguardando conexões...")

    while True:
        cliente_socket, endereco = servidor.accept()
        print(f"Conexão estabelecida com {endereco}")
        thread = threading.Thread(target=processar_requisicao, args=(cliente_socket,))
        thread.start()

if __name__ == "__main__":
    servidor_bancario()
