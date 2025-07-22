# game.py (Conteúdo essencial para ser importado)

import random

# --- Lógica do Jogo ---

def determine_winner(player_choice_char, opponent_choice_char):
    """
    Determina o vencedor da rodada.
    Recebe caracteres ('P', 'A', 'T').
    Retorna:
        0 para Empate
        1 para Jogador 1 (você) vence
        -1 para Jogador 2 (oponente) vence
    """
    if player_choice_char == opponent_choice_char:
        return 0
    elif (player_choice_char == 'P' and opponent_choice_char == 'T') or \
         (player_choice_char == 'A' and opponent_choice_char == 'P') or \
         (player_choice_char == 'T' and opponent_choice_char == 'A'):
        return 1
    else:
        return -1

# Mapeamentos para exibir as escolhas
CHOICE_MAPPING = {'P': 'Pedra ✊', 'A': 'Papel ✋', 'T': 'Tesoura ✌️'}
REVERSE_CHOICE_MAPPING = {'Pedra': 'P', 'Papel': 'A', 'Tesoura': 'T'}

# Você pode manter as funções de console e GUI aqui também,
# mas para o P2P, o importante é ter determine_winner e os mapeamentos.

# As funções de criptografia e GameState (se for usar mais adiante para sincronização complexa)
# também ficariam aqui ou em um módulo 'networking_utils.py'
import hashlib
import json

def generate_hash(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

class GameState:
    # ... (a classe GameState do seu game.py anterior) ...
    def __init__(self):
        self.player1_score = 0
        self.player2_score = 0
        self.player1_choice = None
        self.player2_choice = None
        self.round_complete = False

    def to_json(self):
        return json.dumps({
            'player1_score': self.player1_score,
            'player2_score': self.player2_score,
            'player1_choice': self.player1_choice,
            'player2_choice': self.player2_choice,
            'round_complete': self.round_complete
        })

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        state = GameState()
        state.player1_score = data.get('player1_score', 0)
        state.player2_score = data.get('player2_score', 0)
        state.player1_choice = data.get('player1_choice')
        state.player2_choice = data.get('player2_choice')
        state.round_complete = data.get('round_complete', False)
        return state

def encrypt_message(message, key="secret"): # Adicionado um placeholder de chave
    return f"ENCRYPTED({message}, Key:{key})"

def decrypt_message(encrypted_message, key="secret"): # Adicionado um placeholder de chave
    return encrypted_message.replace(f", Key:{key})", "").replace("ENCRYPTED(", "")
