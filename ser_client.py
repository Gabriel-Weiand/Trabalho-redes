# cliente.py (versão com protocolo de comandos)

import socket
import threading
import sys

# --- Configurações do Cliente ---
HOST = '127.0.0.1'
PORT = 12345
nome_jogador = ""


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

                if comando == 'MSG':
                    print(f"[SERVIDOR] {payload}")
                elif comando == 'RANKING':
                    print("--- RANKING DE VENCEDORES ---")
                    if not payload:
                        print("Ainda não há vencedores.")
                    else:
                        # Parse do payload: "nome1:score1,nome2:score2"
                        lista_ranking = [item.split(':') for item in payload.split(',')]
                        # Ordena pelo score (convertido para int)
                        lista_ranking.sort(key=lambda x: int(x[1]), reverse=True)
                        for nome, vitorias in lista_ranking:
                            print(f"- {nome}: {vitorias} vitórias")
                    print("-----------------------------")
                elif comando == 'GAME_START':
                    print(f"🔥 Partida encontrada! Você está jogando contra: {payload}")
                elif comando == 'PROMPT_MOVE':
                    print(f"--- RODADA {payload} ---")
                    print("Faça sua jogada! Digite 'rock', 'paper' ou 'scissors':")
                elif comando == 'ROUND_RESULT':
                    print(f"📊 {payload}")
                elif comando == 'GAME_OVER':
                    print(f"🏆 {payload}")
                    print("\nVocê voltou para a fila. Aguardando nova partida...")

                print(f"{nome_jogador}> ", end="", flush=True)

        except (ConnectionResetError, IndexError):
            print("\n[ERRO] Conexão perdida ou dados inválidos do servidor.")
            break

    client_socket.close()


def main():
    global nome_jogador

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

    # 1. Enviar comando de conexão
    client_socket.sendall(f"CONN {nome_jogador}\n".encode('utf-8'))

    # 2. Iniciar thread para escutar o servidor
    thread_escuta = threading.Thread(target=escutar_servidor, args=(client_socket,), daemon=True)
    thread_escuta.start()

    # 3. Loop principal para enviar comandos
    print("\nBem-vindo ao Pedra, Papel e Tesoura! Comandos: 'rock', 'paper', 'scissors' ou 'quit'.")
    while thread_escuta.is_alive():
        try:
            comando_usuario = input(f"{nome_jogador}> ").lower().strip()
            if comando_usuario in ['rock', 'paper', 'scissors', 'quit']:
                client_socket.sendall(f"{comando_usuario.upper()}\n".encode('utf-8'))
                if comando_usuario == 'quit':
                    break
            elif comando_usuario:
                print("[AVISO] Comando inválido. Tente 'rock', 'paper', 'scissors' ou 'quit'.")
        except (KeyboardInterrupt, EOFError):
            client_socket.sendall(b"QUIT\n")
            break

    print("Encerrando o cliente...")
    client_socket.close()


if __name__ == "__main__":
    main()