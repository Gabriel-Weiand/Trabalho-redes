# p2p_server.py
import socket
import json
import random
import sys
import time
from game import determine_winner, CHOICE_MAPPING, generate_hash, encrypt_message, decrypt_message

# --- Configurações de Rede ---
HOST = '0.0.0.0'  # Escuta em todas as interfaces de rede disponíveis
PORT = 65432      # Porta não privilegiada (> 1023)

def get_local_ip():
    """Tenta obter o IP local da máquina para exibição."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Conecta a um IP externo (Google DNS) para obter o IP da interface
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1 (Não foi possível obter o IP externo)"

def p2p_server_game():
    print("--- Pedra, Papel e Tesoura P2P (Servidor) ---")
    local_ip = get_local_ip()
    print(f"Aguardando conexão na porta {PORT} no IP: {local_ip}")
    print("Peça para seu oponente se conectar a este IP e porta.")

    server_socket = None
    conn = None
    try:
        # Cria um socket TCP/IP
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reutilizar endereço (útil para testes)
        server_socket.bind((HOST, PORT)) # Liga o socket ao endereço e porta
        server_socket.listen(1) # Começa a escutar por uma conexão (máximo 1 cliente para 1x1)

        conn, addr = server_socket.accept() # Aceita a conexão do cliente
        print(f"Conectado por {addr}")

        player_score = 0
        opponent_score = 0

        # Chave de criptografia (simplificada para demonstração)
        # Em um cenário real, usaria um protocolo de troca de chaves como Diffie-Hellman
        encryption_key = "super_secret_p2p_key" 

        # Loop do jogo
        while True:
            print("\n--- Nova Rodada ---")
            
            # 1. Pegar a jogada do jogador (servidor)
            while True:
                player_choice_char = input("Sua escolha (P/A/T) ou 'sair' para encerrar: ").upper()
                if player_choice_char in ['P', 'A', 'T', 'SAIR']:
                    break
                else:
                    print("Escolha inválida. Por favor, digite P, A, T ou 'sair'.")
            
            if player_choice_char == 'SAIR':
                conn.sendall(json.dumps({'type': 'quit'}).encode('utf-8'))
                print("Você encerrou o jogo.")
                break

            # 2. Enviar a jogada para o oponente
            message_to_send = {'type': 'play', 'choice': player_choice_char}
            json_message = json.dumps(message_to_send)
            
            # Criptografar e adicionar hash (objetivo distante)
            encrypted_json_message = encrypt_message(json_message, encryption_key)
            msg_hash = generate_hash(json_message) # Hash do JSON original
            final_message_payload = json.dumps({'encrypted_data': encrypted_json_message, 'hash': msg_hash})
            
            conn.sendall(final_message_payload.encode('utf-8'))
            print(f"Você escolheu: {CHOICE_MAPPING[player_choice_char]}. Aguardando a jogada do oponente...")

            # 3. Receber a jogada do oponente
            data = conn.recv(1024) # Recebe até 1024 bytes
            if not data:
                print("Oponente desconectou.")
                break

            try:
                received_payload = json.loads(data.decode('utf-8'))
                encrypted_opponent_message = received_payload.get('encrypted_data')
                opponent_msg_hash = received_payload.get('hash')

                # Descriptografar e verificar hash
                decrypted_opponent_message = decrypt_message(encrypted_opponent_message, encryption_key)
                
                if generate_hash(decrypted_opponent_message) != opponent_msg_hash:
                    print("AVISO: Integridade da mensagem do oponente comprometida! (Hash não corresponde)")
                    # Em um jogo real, você poderia abortar a rodada ou a conexão aqui.
                
                opponent_data = json.loads(decrypted_opponent_message)

                if opponent_data.get('type') == 'quit':
                    print("O oponente encerrou o jogo.")
                    break
                
                opponent_choice_char = opponent_data.get('choice')

            except json.JSONDecodeError:
                print("Erro ao decodificar a mensagem JSON do oponente.")
                continue # Pula para a próxima rodada ou encerra

            # 4. Determinar o vencedor
            print(f"Seu oponente escolheu: {CHOICE_MAPPING[opponent_choice_char]}")
            
            result = determine_winner(player_choice_char, opponent_choice_char)

            if result == 0:
                print("Resultado: Empate!")
            elif result == 1:
                player_score += 1
                print("Resultado: Você Venceu!")
            else:
                opponent_score += 1
                print("Resultado: Você Perdeu!")
            
            print(f"Placar: Você {player_score} x {opponent_score} Oponente")
            
    except ConnectionRefusedError:
        print("Erro: Nenhuma conexão aceita. Certifique-se de que o cliente está tentando se conectar ao IP e porta corretos.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if conn:
            conn.close()
        if server_socket:
            server_socket.close()
        print("Conexão encerrada.")

if __name__ == "__main__":
    p2p_server_game()
