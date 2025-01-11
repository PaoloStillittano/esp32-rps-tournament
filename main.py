from flask import Flask, jsonify, request
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import threading
import queue
import time

app = Flask(__name__)

# Stato del gioco
game_state = {
    "current_player": 1,
    "moves": {1: None, 2: None},
    "current_set": {
        "plays": [],  # Lista delle giocate nel set corrente
        "scores": {1: 0, 2: 0}  # Punteggi nel set corrente
    },
    "sets": {1: 0, 2: 0},  # Set vinti da ciascun giocatore
    "match_history": [],  # Storia completa delle partite
    "game_phase": "IN_PROGRESS"  # IN_PROGRESS, SET_COMPLETE, MATCH_COMPLETE
}

# Coda per la comunicazione tra Flask e GUI
gui_queue = queue.Queue()

def determine_winner(move1, move2):
    if move1 == move2:
        return 0
    elif (
        (move1 == "rock" and move2 == "scissors") or
        (move1 == "paper" and move2 == "rock") or
        (move1 == "scissors" and move2 == "paper")
    ):
        return 1
    return 2

def check_set_winner():
    """Controlla se qualcuno ha vinto il set corrente"""
    set_scores = game_state["current_set"]["scores"]
    if set_scores[1] >= 2:
        return 1
    elif set_scores[2] >= 2:
        return 2
    elif len(game_state["current_set"]["plays"]) >= 3:
        # Se abbiamo giocato 3 volte, vince chi ha più punti
        return 1 if set_scores[1] > set_scores[2] else 2
    return None

def check_match_winner():
    """Controlla se qualcuno ha vinto la partita"""
    if game_state["sets"][1] >= 2:
        return 1
    elif game_state["sets"][2] >= 2:
        return 2
    return None

def reset_set():
    """Resetta lo stato per un nuovo set"""
    game_state["current_set"] = {
        "plays": [],
        "scores": {1: 0, 2: 0}
    }

def reset_match():
    """Resetta lo stato per una nuova partita"""
    game_state["sets"] = {1: 0, 2: 0}
    reset_set()
    game_state["game_phase"] = "IN_PROGRESS"

@app.route('/game_state/<int:player>', methods=['GET'])
def get_game_state(player):
    return jsonify({
        "is_turn": game_state["current_player"] == player,
        "last_move": game_state["moves"][player],
        "game_phase": game_state["game_phase"]
    })

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    player = data['player']
    move = data['move']
    
    if game_state["game_phase"] == "MATCH_COMPLETE":
        reset_match()
    
    game_state["moves"][player] = move
    
    # Se entrambi i giocatori hanno fatto la loro mossa
    if all(game_state["moves"].values()):
        # Determina il vincitore della giocata
        winner = determine_winner(game_state["moves"][1], game_state["moves"][2])
        
        # Registra la giocata
        play_result = {
            "moves": game_state["moves"].copy(),
            "winner": winner,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        # Aggiorna i punteggi del set
        if winner > 0:
            game_state["current_set"]["scores"][winner] += 1
        
        # Aggiungi la giocata al set corrente
        game_state["current_set"]["plays"].append(play_result)
        
        # Controlla se qualcuno ha vinto il set
        set_winner = check_set_winner()
        if set_winner:
            game_state["sets"][set_winner] += 1
            game_state["game_phase"] = "SET_COMPLETE"
            
            # Controlla se qualcuno ha vinto la partita
            match_winner = check_match_winner()
            if match_winner:
                game_state["game_phase"] = "MATCH_COMPLETE"
                game_state["match_history"].append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "winner": match_winner,
                    "sets": game_state["sets"].copy()
                })
        
        # Reset delle mosse
        game_state["moves"] = {1: None, 2: None}
        
        if game_state["game_phase"] == "SET_COMPLETE":
            reset_set()
            if not match_winner:  # Se la partita non è finita, continua con il prossimo set
                game_state["game_phase"] = "IN_PROGRESS"
        
        # Notifica la GUI
        gui_queue.put({
            "play_result": play_result,
            "current_set": game_state["current_set"].copy(),
            "sets": game_state["sets"].copy(),
            "game_phase": game_state["game_phase"]
        })
    
    # Cambia il turno
    game_state["current_player"] = 2 if player == 1 else 1
    
    return jsonify({"status": "success"})

class GameGUI:
    def __init__(self, root):
        self.root = root
        root.title("Rock Paper Scissors Tournament")
        root.minsize(1024, 768)
        
        # Configurazione dello stile
        style = ttk.Style()
        style.configure("Header.TLabel", font=('Helvetica', 24, 'bold'))
        style.configure("Score.TLabel", font=('Helvetica', 36, 'bold'))
        style.configure("Move.TLabel", font=('Helvetica', 14))
        style.configure("VS.TLabel", font=('Helvetica', 48, 'bold'))
        
        # Carica le immagini
        self.images = {
            'rock': tk.PhotoImage(file='rock.png').subsample(2, 2), 
            'paper': tk.PhotoImage(file='paper.png').subsample(2, 2),
            'scissors': tk.PhotoImage(file='scissors.png').subsample(2, 2)
        }
        
        # Variabili per tenere traccia delle mosse correnti
        self.current_moves = {1: None, 2: None}
        
        # Frame principale
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # Creazione dei frame
        self.create_header()
        self.create_score_frame()
        self.create_set_frame()
        self.create_match_frame()
        
        self.check_queue()
    
    def create_header(self):
        header = ttk.Label(
            self.main_frame, 
            text="ESP32 Rock Paper Scissors Tournament",
            style="Header.TLabel"
        )
        header.grid(row=0, column=0, columnspan=2, pady=(0, 20))
    
    def create_score_frame(self):
        self.score_frame = ttk.LabelFrame(self.main_frame, text="Punteggio Partita", padding="10")
        self.score_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Player 1 Sets
        p1_frame = ttk.Frame(self.score_frame)
        p1_frame.grid(row=0, column=0, padx=20)
        ttk.Label(p1_frame, text="Player 1", style="Move.TLabel").grid(row=0, column=0)
        self.p1_sets = ttk.Label(p1_frame, text="Set: 0", style="Score.TLabel")
        self.p1_sets.grid(row=1, column=0)
        
        # VS label
        ttk.Label(self.score_frame, text="VS", style="Score.TLabel").grid(row=0, column=1, padx=40)
        
        # Player 2 Sets
        p2_frame = ttk.Frame(self.score_frame)
        p2_frame.grid(row=0, column=2, padx=20)
        ttk.Label(p2_frame, text="Player 2", style="Move.TLabel").grid(row=0, column=0)
        self.p2_sets = ttk.Label(p2_frame, text="Set: 0", style="Score.TLabel")
        self.p2_sets.grid(row=1, column=0)
        
        self.score_frame.columnconfigure(0, weight=1)
        self.score_frame.columnconfigure(1, weight=0)
        self.score_frame.columnconfigure(2, weight=1)
    
    def create_set_frame(self):
        self.set_frame = ttk.LabelFrame(self.main_frame, text="Set Corrente", padding="10")
        self.set_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Punteggio del set corrente
        self.current_set_score = ttk.Label(
            self.set_frame,
            text="Set Score: 0 - 0",
            style="Move.TLabel"
        )
        self.current_set_score.grid(row=0, column=0, pady=10)
        
        # Ultima mossa
        self.current_move = ttk.Label(
            self.set_frame,
            text="In attesa delle mosse...",
            style="Move.TLabel",
            wraplength=300
        )
        self.current_move.grid(row=1, column=0, pady=10)
        
        # Stato del gioco
        self.game_status = ttk.Label(
            self.set_frame,
            text="",
            style="Move.TLabel"
        )
        self.game_status.grid(row=2, column=0, pady=10)
        
        # Indicatore del turno
        self.turn_indicator = ttk.Label(
            self.set_frame,
            text="Turno: Player 1",
            style="Move.TLabel"
        )
        self.turn_indicator.grid(row=3, column=0, pady=10)
    
    def create_match_frame(self):
        self.match_frame = ttk.LabelFrame(self.main_frame, text="Mosse Correnti", padding="20")
        self.match_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame per Player 1
        p1_frame = ttk.Frame(self.match_frame)
        p1_frame.grid(row=0, column=0, padx=20, pady=10)
        ttk.Label(p1_frame, text="Player 1", style="Move.TLabel").grid(row=0, column=0, pady=5)
        self.p1_move_image = ttk.Label(p1_frame)
        self.p1_move_image.grid(row=1, column=0, pady=10)
        
        # VS centrale
        ttk.Label(self.match_frame, text="VS", style="VS.TLabel").grid(row=0, column=1, padx=30)
        
        # Frame per Player 2
        p2_frame = ttk.Frame(self.match_frame)
        p2_frame.grid(row=0, column=2, padx=20, pady=10)
        ttk.Label(p2_frame, text="Player 2", style="Move.TLabel").grid(row=0, column=0, pady=5)
        self.p2_move_image = ttk.Label(p2_frame)
        self.p2_move_image.grid(row=1, column=0, pady=10)
        
        # Configurazione del grid
        self.match_frame.columnconfigure(0, weight=1)
        self.match_frame.columnconfigure(1, weight=0)
        self.match_frame.columnconfigure(2, weight=1)
    
    def check_queue(self):
        try:
            while True:
                game_data = gui_queue.get_nowait()
                self.update_gui(game_data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
    
    def update_gui(self, game_data):
        # Aggiorna punteggi dei set
        self.p1_sets.config(text=f"Set: {game_data['sets'][1]}")
        self.p2_sets.config(text=f"Set: {game_data['sets'][2]}")
        
        # Aggiorna punteggio del set corrente
        set_score = game_data['current_set']['scores']
        self.current_set_score.config(text=f"Set Score: {set_score[1]} - {set_score[2]}")
        
        # Aggiorna le mosse e le immagini
        play_result = game_data['play_result']
        move1 = play_result['moves'][1]
        move2 = play_result['moves'][2]
        
        # Mostra le immagini delle mosse
        if move1 in self.images:
            self.p1_move_image.configure(image=self.images[move1])
        if move2 in self.images:
            self.p2_move_image.configure(image=self.images[move2])
        
        # Aggiorna stato del gioco
        if game_data['game_phase'] == "SET_COMPLETE":
            self.game_status.config(text="Set Completato!")
        elif game_data['game_phase'] == "MATCH_COMPLETE":
            winner = 1 if game_data['sets'][1] > game_data['sets'][2] else 2
            self.game_status.config(text=f"Partita Completata! Vince Player {winner}")
        else:
            winner_text = "Pareggio!" if play_result["winner"] == 0 else f"Punto a Player {play_result['winner']}"
            self.game_status.config(text=winner_text)
        
        # Aggiorna indicatore del turno
        self.turn_indicator.config(text=f"Turno: Player {game_state['current_player']}")

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def main():
    root = tk.Tk()
    gui = GameGUI(root)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    root.mainloop()

if __name__ == '__main__':
    main()