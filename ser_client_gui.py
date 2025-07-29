# cliente_gui.py (Protocolo Final)

import tkinter as tk
from tkinter import messagebox, scrolledtext
import socket
import threading
import queue


# --- Classe de Rede (sem alterações necessárias) ---
class NetworkClient:
    def __init__(self):
        self.client_socket = None
        self.message_queue = queue.Queue()

    def connect(self, host, port, name):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.send_command(f"CON {name}")
            self.start_listening()
            return True
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor: {e}")
            return False

    def send_command(self, command):
        if self.client_socket:
            try:
                self.client_socket.sendall(f"{command}\n".encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                self.message_queue.put(('ERROR', 'Conexão com o servidor perdida.'))

    def _listen_for_server_messages(self):
        buffer = ""
        while self.client_socket:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data: break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line: self.message_queue.put(line.strip())
            except (ConnectionResetError, OSError):
                break
        self.message_queue.put(('ERROR', 'Desconectado do servidor.'))
        self.client_socket = None

    def start_listening(self):
        thread = threading.Thread(target=self._listen_for_server_messages, daemon=True)
        thread.start()

    def disconnect(self):
        if self.client_socket:
            self.send_command("QUI")
            self.client_socket.close()
            self.client_socket = None


# --- Classe principal da Aplicação GUI ---
class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Pedra, Papel e Tesoura (Protocolo Final)")
        self.geometry("400x500")

        self.network_client = NetworkClient()
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ConnectScreen, GameScreen, RankingScreen):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ConnectScreen")
        self.process_queue()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def request_ranking(self):
        """Envia o comando RAN para o servidor."""
        self.network_client.send_command("RAN")
        self.show_frame("RankingScreen")

    def process_queue(self):
        try:
            message = self.network_client.message_queue.get_nowait()

            if isinstance(message, tuple) and message[0] == 'ERROR':
                messagebox.showerror("Erro", message[1])
                self.on_closing(force=True)
                return

            parts = message.split(' ', 1)
            command = parts[0].upper()
            payload = parts[1] if len(parts) > 1 else ""

            game_frame = self.frames["GameScreen"]
            ranking_frame = self.frames["RankingScreen"]

            if command == 'MAT':
                game_frame.add_message(f"🔥 Partida encontrada contra: {payload}")
            elif command == 'PLA':
                game_frame.add_message("Sua vez! Faça sua jogada.")
                game_frame.toggle_move_buttons(tk.NORMAL)
            elif command == 'WIN':
                game_frame.add_message("✅ Você venceu esta rodada!")
            elif command == 'LOS':
                game_frame.add_message("❌ Você perdeu esta rodada.")
            elif command == 'TIE':
                game_frame.add_message("🤝 A rodada terminou em empate.")
            elif command == 'RAN':
                ranking_frame.update_ranking(payload)
                game_frame.add_message("[INFO] Ranking recebido.")
            elif command == 'END':
                game_frame.add_message(f"--- FIM DE JOGO ---")
                messagebox.showinfo("Fim da Partida", payload)
                self.on_closing(force=True)

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def on_closing(self, force=False):
        if force or messagebox.askokcancel("Sair", "Você tem certeza que quer sair?"):
            self.network_client.disconnect()
            self.destroy()


# --- Telas da GUI ---
class ConnectScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Conectar ao Servidor", font=("Helvetica", 16)).pack(pady=20)
        tk.Label(self, text="IP do Servidor:").pack(pady=(10, 0))
        self.ip_entry = tk.Entry(self, width=30);
        self.ip_entry.insert(0, "127.0.0.1");
        self.ip_entry.pack()
        tk.Label(self, text="Seu Nome:").pack(pady=(10, 0))
        self.name_entry = tk.Entry(self, width=30);
        self.name_entry.pack()
        self.connect_button = tk.Button(self, text="Conectar", command=self.handle_connect);
        self.connect_button.pack(pady=20)

    def handle_connect(self):
        ip, name = self.ip_entry.get(), self.name_entry.get()
        if not ip or not name:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha o IP e o seu nome.")
            return
        if self.controller.network_client.connect(ip, 12345, name):
            self.controller.show_frame("GameScreen")
            self.controller.frames["GameScreen"].add_message(f"Bem-vindo, {name}! Aguardando partida...")


class GameScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Log do Jogo", font=("Helvetica", 14)).pack(pady=10)
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD, height=15)
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)
        button_frame = tk.Frame(self);
        button_frame.pack(pady=10)

        # MODIFICADO: Comandos ROC, PAP, SCI
        self.rock_button = tk.Button(button_frame, text="Pedra ✊", command=lambda: self.make_move("ROC"))
        self.paper_button = tk.Button(button_frame, text="Papel ✋", command=lambda: self.make_move("PAP"))
        self.scissors_button = tk.Button(button_frame, text="Tesoura ✌️", command=lambda: self.make_move("SCI"))

        self.rock_button.grid(row=0, column=0, padx=5)
        self.paper_button.grid(row=0, column=1, padx=5)
        self.scissors_button.grid(row=0, column=2, padx=5)
        self.toggle_move_buttons(tk.DISABLED)

        # MODIFICADO: Botão de ranking agora requisita ao servidor
        self.ranking_button = tk.Button(self, text="Ver Ranking", command=controller.request_ranking)
        self.ranking_button.pack(pady=10)

    def make_move(self, move):
        self.controller.network_client.send_command(move)
        move_map = {"ROC": "Pedra", "PAP": "Papel", "SCI": "Tesoura"}
        self.add_message(f"Você jogou: {move_map.get(move)}")
        self.toggle_move_buttons(tk.DISABLED)

    def add_message(self, message):
        self.log_text.config(state='normal');
        self.log_text.insert(tk.END, message + "\n");
        self.log_text.config(state='disabled');
        self.log_text.see(tk.END)

    def toggle_move_buttons(self, state):
        self.rock_button.config(state=state);
        self.paper_button.config(state=state);
        self.scissors_button.config(state=state)


class RankingScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="Ranking de Vitórias", font=("Helvetica", 16)).pack(pady=20)
        self.ranking_listbox = tk.Listbox(self, font=("Courier", 12), height=15)
        self.ranking_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        back_button = tk.Button(self, text="Voltar para o Jogo", command=lambda: controller.show_frame("GameScreen"))
        back_button.pack(pady=10)

    def update_ranking(self, payload):
        self.ranking_listbox.delete(0, tk.END)
        if not payload:
            self.ranking_listbox.insert(tk.END, "  Ranking vazio.")
            return
        try:
            lista_ranking = [item.split(':') for item in payload.split(',')]
            lista_ranking.sort(key=lambda x: int(x[1]), reverse=True)
            for i, (nome, vitorias) in enumerate(lista_ranking, 1):
                self.ranking_listbox.insert(tk.END, f" {i:>2}. {nome:<20} {vitorias:>3} vitórias")
        except (ValueError, IndexError):
            self.ranking_listbox.insert(tk.END, "  Erro ao carregar ranking.")


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()