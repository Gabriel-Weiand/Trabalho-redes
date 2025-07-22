# p2p_client.py
import socket
import json
import sys
import time
from game import determine_winner, CHOICE_MAPPING, generate_hash, encrypt_message, decrypt_message

# --- Configurações de Rede ---
# MUDAR AQUI: Use o IP do computador que está rodando p2p_server.py
# Se estiver testando no mesmo PC, pode ser '127.0.0.1' ou o IP obtido pelo p2p_server.py
SERVER_HOST = '127.0.0.1' # Ex: '192.168.1.100' se for em PCs diferentes
SERVER_PORT = 65432       # Deve ser a mesma porta do p2p_server.py

def p2p_client_game():
    print("--- Pedra, Papel e Tesoura P2P (Cliente) ---")
    
    # Pergunta o IP do servidor ao usuário
    custom_host = input(f"Digite o IP do servidor (padrão: {SERVER_HOST}): ")
    host_to_connect = custom_host if custom_host else SERVER_HOST

    client_socket = None
    try:
        # Cria um socket TCP/IP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host_to_connect, SERVER_PORT)) # Conecta ao servidor
        print(f"Conectado ao servidor em {host_to_connect}:{SERVER_PORT}")

        player_score = 0
        opponent_score = 0
        
        # Chave de criptografia (deve ser a mesma do servidor)
        encryption_key = "super_secret_p2p_key"

        # Loop do jogo
        while True:
            print("\n--- Nova Rodada ---")
            
            # 1. Pegar a jogada do jogador (cliente)
            while True:
                player_choice_char = input("Sua escolha (P/A/T) ou 'sair' para encerrar: ").upper()
                if player_choice_char in ['P', 'A', 'T', 'SAIR']:
                    break
                else:
                    print("Escolha inválida. Por favor, digite P, A, T ou 'sair'.")
            
            if player_choice_char == 'SAIR':
                client_socket.sendall(json.dumps({'type': 'quit'}).encode('utf-8'))
                print("Você encerrou o jogo.")
                break

            # 2. Enviar a jogada para o oponente
            message_to_send = {'type': 'play', 'choice': player_choice_char}
            json_message = json.dumps(message_to_send)
            
            # Criptografar e adicionar hash
            encrypted_json_message = encrypt_message(json_message, encryption_key)
            msg_hash = generate_hash(json_message)
            final_message_payload = json.dumps({'encrypted_data': encrypted_json_message, 'hash': msg_hash})
            
            client_socket.sendall(final_message_payload.encode('utf-8'))
            print(f"Você escolheu: {CHOICE_MAPPING[player_choice_char]}. Aguardando a jogada do oponente...")

            # 3. Receber a jogada do oponente
            data = client_socket.recv(1024) # Recebe até 1024 bytes
            if not data:
                print("Servidor desconectou.")
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
                continue

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
        print(f"Erro: Conexão recusada. Verifique se o servidor está rodando no IP {host_to_connect} e porta {SERVER_PORT}.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if client_socket:
            client_socket.close()
        print("Conexão encerrada.")

if __name__ == "__main__":
    p2p_client_game()
