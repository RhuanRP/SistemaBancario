import socket
import json
import threading
import random
import time

print_lock = threading.Lock()

def realizar_operacao(tipo, conta, valor=0, conta_destino=None):
    try:
        cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente_socket.settimeout(10)
        cliente_socket.connect(('localhost', 12345))

        operacao = {
            'tipo': tipo,
            'conta': conta,
            'valor': valor
        }

        if tipo == 'transferencia':
            operacao['conta_origem'] = conta
            operacao['conta_destino'] = conta_destino

        cliente_socket.send(json.dumps(operacao).encode())
        resposta = cliente_socket.recv(1024).decode()

        with print_lock:
            if tipo == 'transferencia':
                print(f"[Transferência] {conta} -> {conta_destino} | Valor: {valor} | Resposta: {resposta}")
            else:
                print(f"[{tipo.capitalize()}] Conta: {conta} | Valor: {valor} | Resposta: {resposta}")
        
    except socket.timeout:
        with print_lock:
            print(f"Timeout ao conectar com o servidor para a operação {tipo}.")
    except Exception as e:
        with print_lock:
            print(f"Erro na operação {tipo}: {str(e)}")
    finally:
        cliente_socket.close()

def cliente_bancario(num_clientes, num_transacoes):
    threads = []

    for _ in range(num_clientes):
        for _ in range(num_transacoes):
            tipo = random.choice(['deposito', 'saque', 'consulta', 'transferencia'])
            conta = f"conta_{random.randint(1, 10)}"
            valor = random.randint(1, 1000)
            if tipo == 'transferencia':
                conta_destino = f"conta_{random.randint(1, 10)}"
                if conta != conta_destino:
                    thread = threading.Thread(target=realizar_operacao, args=(tipo, conta, valor, conta_destino))
                    threads.append(thread)
                    thread.start()
            else:
                thread = threading.Thread(target=realizar_operacao, args=(tipo, conta, valor))
                threads.append(thread)
                thread.start()

            time.sleep(random.uniform(0.1, 0.5)) 

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    num_clientes = int(input("Digite o número de clientes: "))
    num_transacoes = int(input("Digite o número de transações por cliente: "))
    
    cliente_bancario(num_clientes, num_transacoes)
