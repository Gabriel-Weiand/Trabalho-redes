# cliente_cli.py (Protocolo JSON, sem GUI)

import socket
import threading
import sys
import os
import json # Importar a biblioteca json

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


def enviar_comando(client_socket, comando_type, payload_data={}):
    """
    Envia uma mensagem JSON para o servidor.
    comando_type: string (ex: 'CON', 'ROC', 'RAN')
    payload_data: dict (dados a serem incluídos no payload)
    """
    try:
        mensagem_json = {
            "type": comando_type.upper(),
            "payload": payload_data
        }
        mensagem = json.dumps(mensagem_json) + '\n'  # Adiciona a quebra de linha no final
        client_socket.sendall(mensagem.encode('utf-8'))
    except (BrokenPipeError, ConnectionResetError):
        print(f"[ERRO] Conexão com o servidor foi perdida ao tentar enviar comando '{comando_type}'.")
        os._exit(1) # Força a saída em caso de erro crítico
    except Exception as e:
        print(f"[ERRO] Ao enviar comando '{comando_type}' para o servidor: {e}")


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

                try:
                    mensagem_json = json.loads(linha)
                    comando = mensagem_json.get('type', '').upper()
                    payload = mensagem_json.get('payload', {})
                except json.JSONDecodeError:
                    print(f"\n[ERRO] Mensagem JSON inválida recebida do servidor: {linha}")
                    continue # Ignora a mensagem inválida e continua

                print()  # Linha em branco para formatação

                if comando == 'MAT':
                    oponente = payload.get('oponente', 'Desconhecido')
                    print(f"🔥 Partida encontrada! Você está jogando contra: {oponente}")
                elif comando == 'PLA':
                    print("Sua vez! Digite 'rock', 'paper' ou 'scissors':")
                elif comando == 'WIN':
                    jogada_oponente_raw = payload.get('jogada_oponente', 'TIMEOUT').lower()
                    jogada_oponente = COMANDOS_MAP.get(jogada_oponente_raw, jogada_oponente_raw)
                    print(f"✅ Você venceu! O oponente jogou: {jogada_oponente}")
                elif comando == 'LOS':
                    jogada_oponente_raw = payload.get('jogada_oponente', 'TIMEOUT').lower()
                    jogada_oponente = COMANDOS_MAP.get(jogada_oponente_raw, jogada_oponente_raw)
                    print(f"❌ Você perdeu. O oponente jogou: {jogada_oponente}")
                elif comando == 'TIE':
                    jogada_oponente_raw = payload.get('jogada_oponente', 'TIMEOUT').lower()
                    jogada_oponente = COMANDOS_MAP.get(jogada_oponente_raw, jogada_oponente_raw)
                    print(f"🤝 Empate! O oponente também jogou: {jogada_oponente}")
                elif comando == 'RAN':
                    print("--- RANKING DE VENCEDORES ---")
                    ranking_data = payload.get('ranking', [])
                    if not ranking_data:
                        print("Ainda não há vencedores.")
                    else:
                        # Garante que a lista de ranking seja classificada por vitórias
                        ranking_data.sort(key=lambda x: x.get('vitorias', 0), reverse=True)
                        for item in ranking_data:
                            nome = item.get('nome', 'Desconhecido')
                            vitorias = item.get('vitorias', 0)
                            print(f"- {nome}: {vitorias} vitórias")
                    print("-----------------------------")
                elif comando == 'END':
                    mensagem_final = payload.get('mensagem', 'Partida finalizada.').strip()
                    print("\n--- FIM DE JOGO ---")
                    print(f"Mensagem do servidor: {mensagem_final}")
                    print("A aplicação será encerrada.")
                    client_socket.close()  # Fecha o socket para a thread principal terminar
                    os._exit(0)  # Força o encerramento

                # Reimprime o prompt do usuário
                print(f"{nome_jogador}> ", end="", flush=True)

        except (ConnectionResetError, IndexError) as e:
            print(f"\n[ERRO] Conexão perdida ou dados inválidos do servidor: {e}")
            break
        except Exception as e:
            print(f"\n[ERRO INESPERADO] {e}")
            break

    print("Thread de escuta encerrada.")


def main():
    global nome_jogador
    global HOST

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

    # 1. Enviar comando de conexão (CON com payload de nome)
    enviar_comando(client_socket, 'CON', {"nome": nome_jogador})

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
                enviar_comando(client_socket, comando_protocolo, {}) # Jogadas tem payload vazio
            elif comando_usuario == 'ran':
                enviar_comando(client_socket, 'RAN', {}) # RAN tem payload vazio
            elif comando_usuario == 'quit':
                enviar_comando(client_socket, 'QUI', {}) # QUI tem payload vazio
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