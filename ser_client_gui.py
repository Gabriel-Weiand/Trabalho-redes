# cliente_final_gui.py (Protocolo JSON com Interface Gráfica Melhorada)

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import threading
import queue
import json  # Protocolo agora usa JSON


# --- Classe de Rede (Adaptada para o Protocolo JSON) ---
class NetworkClient:
    """Gerencia a comunicação de rede com o servidor usando o protocolo JSON."""

    def __init__(self, message_queue):
        self.client_socket = None
        self.message_queue = message_queue

    def connect(self, host, port, name):
        """Tenta conectar ao servidor e se identifica."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            # Envia o comando de conexão no formato JSON correto
            self.send_json("CON", {"nome": name})
            self.start_listening()
            return True
        except Exception as e:
            self.message_queue.put({"type": "ERROR", "payload": {"msg": f"Falha ao conectar: {e}"}})
            return False

    def send_json(self, command_type, payload_data={}):
        """Envia um comando formatado como JSON para o servidor."""
        if not self.client_socket:
            return
        try:
            message_obj = {"type": command_type.upper(), "payload": payload_data}
            message_str = json.dumps(message_obj) + '\n'
            self.client_socket.sendall(message_str.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            self.message_queue.put({"type": "ERROR", "payload": {"msg": "Conexão com o servidor perdida."}})

    def _listen_for_server_messages(self):
        """Escuta mensagens do servidor em uma thread separada."""
        buffer = ""
        while self.client_socket:
            try:
                data = self.client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        # Decodifica a mensagem JSON e a coloca na fila
                        message_obj = json.loads(line)
                        self.message_queue.put(message_obj)
            except (ConnectionResetError, OSError):
                break
            except json.JSONDecodeError:
                print(f"AVISO: Recebido JSON inválido do servidor: {line}")
                continue

        # Sinaliza o fim da conexão
        self.message_queue.put({"type": "ERROR", "payload": {"msg": "Desconectado do servidor."}})
        self.client_socket = None

    def start_listening(self):
        """Inicia a thread de escuta."""
        thread = threading.Thread(target=self._listen_for_server_messages, daemon=True)
        thread.start()

    def disconnect(self):
        """Envia o comando de desconexão e fecha o socket."""
        if self.client_socket:
            self.send_json("QUI")
            self.client_socket.close()
            self.client_socket = None


# --- Classe principal da Aplicação GUI ---
class App(tk.Tk):
    """Controlador principal da aplicação, gerenciando janelas e comunicação."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Pedra, papel, tesoura")
        self.geometry("450x550")
        self.resizable(False, False)

        # Estilo visual moderno
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.message_queue = queue.Queue()
        self.network_client = NetworkClient(self.message_queue)

        container = ttk.Frame(self, padding="10")
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ConnectScreen, GameScreen):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ConnectScreen")
        self.process_queue()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def process_queue(self):
        """Processa mensagens da fila de rede para atualizar a GUI."""
        try:
            message = self.message_queue.get_nowait()

            command = message.get("type", "").upper()
            payload = message.get("payload", {})

            game_frame = self.frames["GameScreen"]

            if command == 'ERROR':
                messagebox.showerror("Erro de Conexão", payload.get("msg"))
                self.on_closing(force=True)
                return
            elif command == 'MAT':
                game_frame.add_log(f"🔥 Partida encontrada contra: {payload.get('oponente', 'Desconhecido')}", "info")
            elif command == 'PLA':
                game_frame.add_log("Sua vez! Faça sua jogada.", "info_bold")
                game_frame.toggle_move_buttons(tk.NORMAL)
            elif command == 'WIN':
                game_frame.add_log(f"✅ Você venceu! Oponente jogou: {payload.get('jogada_oponente')}", "win")
            elif command == 'LOS':
                game_frame.add_log(f"❌ Você perdeu. Oponente jogou: {payload.get('jogada_oponente')}", "loss")
            elif command == 'TIE':
                game_frame.add_log(f"🤝 Empate! Ambos jogaram: {payload.get('jogada_oponente')}", "tie")
            elif command == 'RAN':
                # Agora o ranking é uma janela pop-up, não uma tela separada
                RankingWindow(self, payload.get('ranking', []))
            elif command == 'END':
                game_frame.add_log(f"--- FIM DE JOGO ---", "info_bold")
                game_frame.add_log(payload.get('mensagem', 'Partida finalizada.'), "info")
                game_frame.toggle_move_buttons(tk.DISABLED)
                messagebox.showinfo("Fim da Partida", payload.get('mensagem'))

        except queue.Empty:
            pass  # Fila vazia, nada a fazer
        finally:
            self.after(100, self.process_queue)  # Verifica a fila novamente em 100ms

    def on_closing(self, force=False):
        """Lida com o fechamento da janela."""
        if force or messagebox.askokcancel("Sair", "Você tem certeza que quer sair?"):
            self.network_client.disconnect()
            self.destroy()


# --- Telas da GUI ---
class ConnectScreen(ttk.Frame):
    """Tela inicial para conexão ao servidor."""

    def __init__(self, parent, controller):
        super().__init__(parent, padding="20")
        self.controller = controller

        ttk.Label(self, text="Conectar ao Jogo", font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))

        # Frame para os campos de entrada
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)

        ttk.Label(form_frame, text="IP do Servidor:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.ip_entry = ttk.Entry(form_frame, width=30, font=("Segoe UI", 10))
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Seu Nome:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = ttk.Entry(form_frame, width=30, font=("Segoe UI", 10))
        self.name_entry.grid(row=1, column=1, padx=5, pady=5)

        self.connect_button = ttk.Button(self, text="Conectar", command=self.handle_connect, style='Accent.TButton')
        self.connect_button.pack(pady=20, ipadx=10, ipady=5)

        self.status_label = ttk.Label(self, text="", font=("Segoe UI", 9))
        self.status_label.pack(pady=5)

    def handle_connect(self):
        ip, name = self.ip_entry.get(), self.name_entry.get()
        if not ip or not name:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha o IP e o seu nome.")
            return

        self.status_label.config(text="Conectando...")
        self.connect_button.config(state=tk.DISABLED)

        if self.controller.network_client.connect(ip, 12345, name):
            self.controller.show_frame("GameScreen")
            self.controller.frames["GameScreen"].add_log(f"Bem-vindo, {name}! Aguardando oponente...", "info")
        else:
            self.status_label.config(text="")
            self.connect_button.config(state=tk.NORMAL)


class GameScreen(ttk.Frame):
    """Tela principal do jogo."""

    def __init__(self, parent, controller):
        super().__init__(parent, padding="10")
        self.controller = controller

        # Log de texto com estilos
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD, height=15,
                                                  font=("Segoe UI", 10))
        self.log_text.pack(padx=5, pady=5, fill="both", expand=True)
        self.log_text.tag_config('win', foreground='green', font=('Segoe UI', 10, 'bold'))
        self.log_text.tag_config('loss', foreground='red', font=('Segoe UI', 10, 'bold'))
        self.log_text.tag_config('tie', foreground='blue')
        self.log_text.tag_config('info', foreground='gray')
        self.log_text.tag_config('info_bold', foreground='black', font=('Segoe UI', 10, 'bold'))

        # Frame para os botões de jogada
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        self.rock_button = ttk.Button(button_frame, text="Pedra ✊", command=lambda: self.make_move("ROC"))
        self.paper_button = ttk.Button(button_frame, text="Papel ✋", command=lambda: self.make_move("PAP"))
        self.scissors_button = ttk.Button(button_frame, text="Tesoura ✌️", command=lambda: self.make_move("SCI"))

        self.rock_button.grid(row=0, column=0, padx=5, ipady=5)
        self.paper_button.grid(row=0, column=1, padx=5, ipady=5)
        self.scissors_button.grid(row=0, column=2, padx=5, ipady=5)
        self.toggle_move_buttons(tk.DISABLED)

        # Botão de ranking agora requisita ao servidor
        self.ranking_button = ttk.Button(self, text="Ver Ranking",
                                         command=lambda: self.controller.network_client.send_json("RAN"))
        self.ranking_button.pack(pady=10)

    def make_move(self, move):
        self.controller.network_client.send_json(move)
        move_map = {"ROC": "Pedra", "PAP": "Papel", "SCI": "Tesoura"}
        self.add_log(f"Você jogou: {move_map.get(move)}", "info")
        self.toggle_move_buttons(tk.DISABLED)

    def add_log(self, message, tag=None):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)  # Auto-scroll

    def toggle_move_buttons(self, state):
        self.rock_button.config(state=state)
        self.paper_button.config(state=state)
        self.scissors_button.config(state=state)


# A CLASSE FALTANTE ESTÁ AQUI
class RankingWindow(tk.Toplevel):
    """Janela pop-up para exibir o ranking."""

    def __init__(self, parent, ranking_data):
        super().__init__(parent)
        self.title("Ranking de Vitórias")
        self.geometry("400x400")
        self.transient(parent)  # Mantém a janela no topo
        self.grab_set()  # Modal

        ttk.Label(self, text="Ranking de Vitórias", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # Usando Treeview para uma aparência de tabela
        cols = ('Posição', 'Nome', 'Vitórias')
        tree = ttk.Treeview(self, columns=cols, show='headings', height=15)

        for col in cols:
            tree.heading(col, text=col)
        tree.column("Posição", width=60, anchor="center")
        tree.column("Nome", width=200)
        tree.column("Vitórias", width=80, anchor="center")

        tree.pack(fill="both", expand=True, padx=10, pady=5)

        if not ranking_data:
            tree.insert("", "end", values=("", "Ranking vazio.", ""))
        else:
            # Ordena os dados por vitória (já deve vir do servidor, mas garantimos)
            ranking_data.sort(key=lambda x: x.get('vitorias', 0), reverse=True)
            for i, player in enumerate(ranking_data, 1):
                tree.insert("", "end", values=(f"{i}º", player.get('nome', '?'), player.get('vitorias', 0)))

        close_button = ttk.Button(self, text="Fechar", command=self.destroy)
        close_button.pack(pady=10)


if __name__ == "__main__":
    app = App()
    # Adicionando um estilo para o botão de conectar
    app.style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background='#0078D7')
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()