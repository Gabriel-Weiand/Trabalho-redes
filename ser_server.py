# servidor.py (Protocolo JSON)

import socket
import threading
import time
import sys
import os
import json  # Importar a biblioteca json

# --- Configurações do Servidor ---
HOST = '0.0.0.0'
PORT = 12345

# --- Estado Global do Servidor ---
global_lock = threading.Lock()
jogadores_em_espera = []
clientes_conectados = []  # Lista de todos os sockets para broadcast
ranking = {}


# --- Lógica do Jogo ---
def determinar_vencedor(jogada1, jogador1, jogada2, jogador2):
    # Regra: Timeout/None sempre perde
    if jogada1 == 'TIMEOUT' and jogada2 != 'TIMEOUT':
        return jogador2, jogador1
    if jogada2 == 'TIMEOUT' and jogada1 != 'TIMEOUT':
        return jogador1, jogada2
    if jogada1 == 'TIMEOUT' and jogada2 == 'TIMEOUT':
        return None, None  # Ambos perdem

    regras = {'roc': 'sci', 'sci': 'pap', 'pap': 'roc'}
    if jogada1 == jogada2:
        return None, None  # Empate
    elif regras.get(jogada1) == jogada2:
        return jogador1, jogador2
    else:
        return jogador2, jogador1


# --- Comunicação ---
def enviar_comando(cliente_socket, comando_type, payload_data={}):
    """
    Envia uma mensagem JSON para o cliente.
    comando_type: string (ex: 'MAT', 'PLA', 'WIN')
    payload_data: dict (dados a serem incluídos no payload)
    """
    try:
        mensagem_json = {
            "type": comando_type.upper(),
            "payload": payload_data
        }
        mensagem = json.dumps(mensagem_json) + '\n'  # Adiciona a quebra de linha no final
        cliente_socket.sendall(mensagem.encode('utf-8'))
    except (BrokenPipeError, ConnectionResetError):
        print(f"AVISO: Conexão com o cliente foi perdida ao tentar enviar comando '{comando_type}'.")
    except Exception as e:
        print(f"ERRO ao enviar comando '{comando_type}' para o cliente: {e}")


def enviar_ranking_para_cliente(cliente_socket):
    with global_lock:
        # Converte o dicionário de ranking para o formato de lista de objetos JSON
        ranking_list = [{"nome": nome, "vitorias": vitorias} for nome, vitorias in ranking.items()]
    enviar_comando(cliente_socket, 'RAN', {"ranking": ranking_list})


def broadcast_comando(comando_type, payload_data={}):
    with global_lock:
        clientes_a_notificar = list(clientes_conectados)

    print(f"Enviando '{comando_type}' para {len(clientes_a_notificar)} clientes.")
    for sock in clientes_a_notificar:
        enviar_comando(sock, comando_type, payload_data)


# --- Gerenciamento da Lógica ---
def gerenciar_partida():
    while True:
        jogador1_info, jogador2_info = None, None
        with global_lock:
            if len(jogadores_em_espera) >= 2:
                jogador1_info = jogadores_em_espera.pop(0)
                jogador2_info = jogadores_em_espera.pop(0)

        if jogador1_info and jogador2_info:
            print(f"Iniciando partida entre {jogador1_info['nome']} e {jogador2_info['nome']}")
            # MAT: oponente
            enviar_comando(jogador1_info['socket'], 'MAT', {"oponente": jogador2_info['nome']})
            enviar_comando(jogador2_info['socket'], 'MAT', {"oponente": jogador1_info['nome']})
            time.sleep(0.5)

            pontos = {jogador1_info['nome']: 0, jogador2_info['nome']: 0}
            for rodada in range(1, 4):
                print(f"Partida {jogador1_info['nome']} vs {jogador2_info['nome']} - Rodada {rodada}")
                # PLA: payload vazio
                enviar_comando(jogador1_info['socket'], 'PLA')
                enviar_comando(jogador2_info['socket'], 'PLA')

                tempo_limite = time.time() + 300  # 5 minutos
                while (jogador1_info.get('jogada_atual') is None or jogador2_info.get(
                        'jogada_atual') is None) and time.time() < tempo_limite:
                    time.sleep(0.1)

                jogada1 = jogador1_info.get('jogada_atual', 'TIMEOUT')
                jogada2 = jogador2_info.get('jogada_atual', 'TIMEOUT')

                vencedor_info, perdedor_info = determinar_vencedor(jogada1, jogador1_info, jogada2, jogador2_info)

                if not vencedor_info:
                    # Empate: envia a jogada do oponente (que é a mesma)
                    enviar_comando(jogador1_info['socket'], 'TIE', {"jogada_oponente": jogada2})
                    enviar_comando(jogador2_info['socket'], 'TIE', {"jogada_oponente": jogada1})
                else:
                    # Vitória/Derrota
                    if vencedor_info == jogador1_info:
                        enviar_comando(jogador1_info['socket'], 'WIN', {"jogada_oponente": jogada2})
                        enviar_comando(jogador2_info['socket'], 'LOS', {"jogada_oponente": jogada1})
                    else:  # vencedor_info == jogador2_info
                        enviar_comando(jogador2_info['socket'], 'WIN', {"jogada_oponente": jogada1})
                        enviar_comando(jogador1_info['socket'], 'LOS', {"jogada_oponente": jogada2})

                    pontos[vencedor_info['nome']] += 1
                    with global_lock:
                        ranking[vencedor_info['nome']] = ranking.get(vencedor_info['nome'], 0) + 1

                jogador1_info['jogada_atual'] = None
                jogador2_info['jogada_atual'] = None
                time.sleep(2)

            vencedor_final_nome = None
            if pontos[jogador1_info['nome']] > pontos[jogador2_info['nome']]:
                vencedor_final_nome = jogador1_info['nome']
            elif pontos[jogador2_info['nome']] > pontos[jogador1_info['nome']]:
                vencedor_final_nome = jogador2_info['nome']

            msg_final = "A partida terminou em empate!" if not vencedor_final_nome else f"O vencedor da partida foi {vencedor_final_nome}!"

            # END: mensagem
            enviar_comando(jogador1_info['socket'], 'END', {"mensagem": msg_final})
            enviar_comando(jogador2_info['socket'], 'END', {"mensagem": msg_final})
            print(f"Partida entre {jogador1_info['nome']} e {jogador2_info['nome']} finalizada.")

        time.sleep(1)


def lidar_com_cliente(conn, addr):
    print(f"[NOVA CONEXÃO] {addr} conectado.")
    jogador_info = None
    buffer = ""
    try:
        while True:
            dados = conn.recv(4096).decode('utf-8')
            if not dados: break

            buffer += dados
            while '\n' in buffer:
                linha, buffer = buffer.split('\n', 1)

                try:
                    mensagem_json = json.loads(linha)
                    comando = mensagem_json.get('type', '').upper()
                    payload = mensagem_json.get('payload', {})
                except json.JSONDecodeError:
                    print(f"ERRO: Mensagem JSON inválida recebida de {addr}: {linha}")
                    continue  # Ignora a mensagem inválida e continua

                if comando == 'CON' and not jogador_info:
                    nome_jogador = payload.get('nome')
                    if nome_jogador:
                        jogador_info = {
                            'socket': conn, 'addr': addr, 'nome': nome_jogador, 'jogada_atual': None
                        }
                        with global_lock:
                            jogadores_em_espera.append(jogador_info)
                            if nome_jogador not in ranking: ranking[nome_jogador] = 0
                        print(f"Jogador '{nome_jogador}' associado à conexão {addr}.")
                    else:
                        print(f"ERRO: Comando CON sem nome de jogador de {addr}.")

                elif comando in ['ROC', 'PAP', 'SCI']:
                    if jogador_info:
                        print(f"Recebida jogada '{comando}' de {jogador_info['nome']}")
                        jogador_info['jogada_atual'] = comando.lower()
                    else:
                        print(f"AVISO: Jogada '{comando}' recebida de cliente não identificado ({addr}).")

                elif comando == 'RAN':
                    enviar_ranking_para_cliente(conn)

                elif comando == 'QUI':
                    print(
                        f"Cliente {addr} ({jogador_info['nome'] if jogador_info else 'Desconhecido'}) solicitou desconexão.")
                    break  # Sai do loop para fechar a conexão
                else:
                    print(f"Comando desconhecido '{comando}' de {addr}.")

    except (ConnectionResetError, IndexError, ValueError) as e:
        print(f"Erro com o cliente {addr}: {e}")
    finally:
        with global_lock:
            if conn in clientes_conectados:
                clientes_conectados.remove(conn)
            if jogador_info and jogador_info in jogadores_em_espera:
                jogadores_em_espera.remove(jogador_info)
        conn.close()
        print(f"[CONEXÃO FECHADA] {addr} - Clientes online: {len(clientes_conectados)}")


def gerenciar_servidor_input(servidor_socket):
    """Thread para ler comandos do administrador no console do servidor."""
    print("Console do servidor iniciado. Digite 'end <mensagem>' para encerrar.")
    for linha in sys.stdin:
        partes = linha.strip().split(' ', 1)
        comando = partes[0].lower()
        payload_msg = partes[1] if len(partes) > 1 else "O servidor foi encerrado pelo administrador."

        if comando == "end":
            print("Comando de encerramento recebido...")
            broadcast_comando("END", {"mensagem": payload_msg})  # Adiciona a mensagem ao payload
            time.sleep(1)  # Dá um tempo para as mensagens serem enviadas
            servidor_socket.close()
            print("Servidor encerrado.")
            os._exit(0)  # Força o encerramento de todas as threads
        else:
            print(f"Comando '{comando}' desconhecido.")


def get_local_ip():
    """Função para obter o endereço de IP local da máquina."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Não precisa ser alcançável, apenas força o SO a escolher uma interface
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'  # Fallback para localhost
    finally:
        s.close()
    return IP


def main():
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor_socket.bind((HOST, PORT))
    servidor_socket.listen(5)

    local_ip = get_local_ip()
    print("=" * 40)
    print(f"[*] Servidor (protocolo JSON) iniciado.")
    print(f"[*] Escutando em todas as interfaces: {HOST}:{PORT}")
    print(f"[*] IP local para conexão na rede: {local_ip}:{PORT}")
    print("=" * 40)

    # Thread para gerenciar o início das partidas
    thread_gerenciador_partida = threading.Thread(target=gerenciar_partida, daemon=True)
    thread_gerenciador_partida.start()

    # Thread para ler comandos do console do servidor
    thread_input_servidor = threading.Thread(target=gerenciar_servidor_input, args=(servidor_socket,), daemon=True)
    thread_input_servidor.start()

    try:
        while True:
            conn, addr = servidor_socket.accept()
            with global_lock:
                clientes_conectados.append(conn)
            print(f"Nova conexão aceita de {addr}. Clientes online: {len(clientes_conectados)}")
            thread_cliente = threading.Thread(target=lidar_com_cliente, args=(conn, addr))
            thread_cliente.start()
    except OSError:
        print("Socket do servidor foi fechado. Encerrando...")
    finally:
        print("Loop principal do servidor finalizado.")


if __name__ == "__main__":
    main()