# cliente_cli.py (Protocolo Final, sem GUI)

import socket
import threading
import sys
import os

# --- Configurações do Cliente ---
HOST = '127.0.0.1'
PORT = 12345
nome_jogador = ""

# Mapeamento de jogadas do usuário para comandos do protocolo
JOGADAS_MAP = {
    "rock": "ROC",
    "paper": "PAP",
    "scissors": "SCI"
}
# Mapeamento de comandos do protocolo para texto legível
COMANDOS_MAP = {
    "roc": "Pedra",
    "pap": "Papel",
    "sci": "Tesoura",
    "timeout": "Tempo Esgotado"
}


def escutar_servidor(client_socket):
    """Thread que escuta comandos do servidor e os exibe."""
    buffer = ""
    while True:
        try:
            dados = client_socket.recv(4096).decode('utf-8')
            if not dados:
                print("\n[INFO] Desconectado do servidor.")
                break

            buffer += dados
            while '\n' in buffer:
                linha, buffer = buffer.split('\n', 1)
                linha = linha.strip()
                if not linha:
                    continue

                partes = linha.split(' ', 1)
                comando = partes[0].upper()
                payload = partes[1] if len(partes) > 1 else ""

                print()  # Linha em branco para formatação

                if comando == 'MAT':
                    print(f"🔥 Partida encontrada! Você está jogando contra: {payload}")
                elif comando == 'PLA':
                    print("Sua vez! Digite 'rock', 'paper' ou 'scissors':")
                elif comando == 'WIN':
                    jogada_oponente = COMANDOS_MAP.get(payload.lower(), payload)
                    print(f"✅ Você venceu! O oponente jogou: {jogada_oponente}")
                elif comando == 'LOS':
                    jogada_oponente = COMANDOS_MAP.get(payload.lower(), payload)
                    print(f"❌ Você perdeu. O oponente jogou: {jogada_oponente}")
                elif comando == 'TIE':
                    jogada_oponente = COMANDOS_MAP.get(payload.lower(), payload)
                    print(f"🤝 Empate! O oponente também jogou: {jogada_oponente}")
                elif comando == 'RAN':
                    print("--- RANKING DE VENCEDORES ---")
                    if not payload:
                        print("Ainda não há vencedores.")
                    else:
                        lista_ranking = [item.split(':') for item in payload.split(',')]
                        lista_ranking.sort(key=lambda x: int(x[1]), reverse=True)
                        for nome, vitorias in lista_ranking:
                            print(f"- {nome}: {vitorias} vitórias")
                    print("-----------------------------")
                elif comando == 'END':
                    print("\n--- FIM DE JOGO ---")
                    print(f"Mensagem do servidor: {payload}")
                    print("A aplicação será encerrada.")
                    client_socket.close()  # Fecha o socket para a thread principal terminar
                    os._exit(0)  # Força o encerramento

                # Reimprime o prompt do usuário
                print(f"{nome_jogador}> ", end="", flush=True)

        except (ConnectionResetError, IndexError):
            print("\n[ERRO] Conexão perdida ou dados inválidos do servidor.")
            break
        except Exception as e:
            print(f"\n[ERRO INESPERADO] {e}")
            break

    print("Thread de escuta encerrada.")


def main():
    global nome_jogador
    global HOST  # Adicionado para corrigir o UnboundLocalError

    server_ip_input = input("Digite o IP do servidor (ou pressione Enter para '127.0.0.1'): ")
    if server_ip_input:
        HOST = server_ip_input

    while not nome_jogador:
        nome_jogador = input("Digite seu nome: ").strip()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
    except ConnectionRefusedError:
        print(f"[ERRO] Não foi possível se conectar ao servidor em {HOST}:{PORT}.")
        sys.exit(1)
    except socket.gaierror:
        print(f"[ERRO] O endereço IP '{HOST}' é inválido ou não foi encontrado.")
        sys.exit(1)

    # 1. Enviar comando de conexão
    client_socket.sendall(f"CON {nome_jogador}\n".encode('utf-8'))

    # 2. Iniciar thread para escutar o servidor
    thread_escuta = threading.Thread(target=escutar_servidor, args=(client_socket,), daemon=True)
    thread_escuta.start()

    # 3. Loop principal para enviar comandos
    print("\nBem-vindo ao Pedra, Papel e Tesoura!")
    print("Comandos: 'rock', 'paper', 'scissors', 'ran' (ranking), ou 'quit'.")
    print("Aguardando partida...")

    while thread_escuta.is_alive():
        try:
            comando_usuario = input(f"{nome_jogador}> ").lower().strip()

            if comando_usuario in JOGADAS_MAP:
                comando_protocolo = JOGADAS_MAP[comando_usuario]
                client_socket.sendall(f"{comando_protocolo}\n".encode('utf-8'))
            elif comando_usuario == 'ran':
                client_socket.sendall(b"RAN\n")
            elif comando_usuario == 'quit':
                client_socket.sendall(b"QUI\n")
                break
            elif comando_usuario:
                print("[AVISO] Comando inválido.")

        except (KeyboardInterrupt, EOFError):
            print("\nSaindo...")
            break
        except (BrokenPipeError, ConnectionResetError):
            print("\n[ERRO] A conexão com o servidor foi encerrada.")
            break

    print("Encerrando o cliente...")
    client_socket.close()


if __name__ == "__main__":
    main()
