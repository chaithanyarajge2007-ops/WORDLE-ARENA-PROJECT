import tkinter as tk
from tkinter import ttk, messagebox
import random
import requests

# ---------------- THEMES ----------------
THEMES = {
    "Classic": {"bg":"#121213","tile":"#3a3a3c","correct":"#6aaa64","present":"#c9b458","absent":"#3a3a3c","text":"white"},
    "Fire": {"bg":"#2b0b0b","tile":"#3b1010","correct":"#ff5722","present":"#ffca28","absent":"#757575","text":"white"},
    "Ocean": {"bg":"#001f3f","tile":"#003566","correct":"#2ecc71","present":"#4fc3f7","absent":"#6c757d","text":"white"},
    "Forest": {"bg":"#022c22","tile":"#064e3b","correct":"#22c55e","present":"#eab308","absent":"#9ca3af","text":"#ecfdf5"},
    "Pastel": {"bg":"#fde2f3","tile":"#e9d5ff","correct":"#86efac","present":"#fde68a","absent":"#e5e7eb","text":"#111827"},
}

# ---------------- DICTIONARY ----------------
def dictionary_lookup(word):
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=5
        )
        if r.status_code != 200:
            return None
        data = r.json()
        meanings = []
        for entry in data:
            for m in entry.get("meanings", []):
                for d in m.get("definitions", []):
                    meanings.append(d["definition"])
        return meanings
    except:
        return None

# ---------------- GAME ----------------
class WordleArena:
    def _init_(self, root):
        self.root = root
        self.root.title("Wordle Arena")
        self.root.geometry("900x820")   # wider window
        self.root.minsize(700, 700)

        # -------- FULL WIDTH SCROLLABLE LAYOUT --------
        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(
            self.container, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # ---- CENTERED GAME FRAME ----
        self.main = tk.Frame(self.canvas)
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.main, anchor="n"
        )

        self.canvas.bind("<Configure>", self._resize_canvas)
        self.main.bind("<Configure>", self._update_scrollregion)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # -------- VARIABLES --------
        self.theme = "Classic"
        self.word_len = tk.IntVar(value=5)
        self.timed = tk.BooleanVar()
        self.time_choice = tk.IntVar(value=120)

        self.score = 0
        self.games = 0
        self.wins = 0
        self.timer_job = None

        self.build_ui()
        self.new_game()

    # -------- CENTER CONTENT --------
    def _resize_canvas(self, event):
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _update_scrollregion(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------------- UI ----------------
    def build_ui(self):
        self.banner = tk.Label(self.main, text="🏰 WORDLE ARENA",
                               font=("Poppins",22,"bold"))
        self.banner.pack(pady=10)

        top = tk.Frame(self.main)
        top.pack(pady=5)

        ttk.Combobox(top, values=[4,5,6], width=3,
                     textvariable=self.word_len, state="readonly").grid(row=0,column=0,padx=4)

        self.theme_var = tk.StringVar(value="Pastel")
        ttk.Combobox(top, values=list(THEMES.keys()),
                     textvariable=self.theme_var,
                     state="readonly", width=8).grid(row=0,column=1,padx=4)

        tk.Checkbutton(top, text="⏱ Timed", variable=self.timed).grid(row=0,column=2,padx=4)

        ttk.Combobox(top, values=[60,90,120,180,240,300,360,420,480,540,600],
                     textvariable=self.time_choice,
                     width=4, state="readonly").grid(row=0,column=3)

        tk.Label(top, text="sec").grid(row=0,column=4)

        tk.Button(top, text="New Game", command=self.new_game).grid(row=0,column=5,padx=6)

        self.score_lbl = tk.Label(self.main, font=("Poppins",11,"bold"))
        self.score_lbl.pack(pady=6)

        self.timer_lbl = tk.Label(self.main, font=("Poppins",11,"bold"))
        self.timer_lbl.pack()

        self.grid_frame = tk.Frame(self.main)
        self.grid_frame.pack(pady=12)

        self.entry = tk.Entry(self.main, font=("Poppins",14), justify="center", width=18)
        self.entry.pack()
        self.entry.bind("<Return>", lambda e:self.submit())

        tk.Button(self.main, text="Guess", width=10,
                  command=self.submit).pack(pady=6)

        self.keyboard_frame = tk.Frame(self.main)
        self.keyboard_frame.pack(pady=12)

        self.apply_theme()

    # ---------------- GAME LOGIC ----------------
    def load_words(self):
        with open(f"words_{self.word_len.get()}.txt") as f:
            return [w.strip() for w in f.readlines()]

    def new_game(self):
        if self.timer_job:
            self.root.after_cancel(self.timer_job)

        self.words = self.load_words()
        self.target = random.choice(self.words)
        self.row = 0
        self.games += 1

        for w in self.grid_frame.winfo_children():
            w.destroy()

        self.tiles = []
        for r in range(6):
            row=[]
            for c in range(self.word_len.get()):
                lbl = tk.Label(
                    self.grid_frame,
                    width=4, height=2,
                    font=("Poppins",16,"bold"),
                    relief="solid", bd=2
                )
                lbl.grid(row=r,column=c,padx=6,pady=6)
                row.append(lbl)
            self.tiles.append(row)

        self.keyboard_state = {chr(i):"unused" for i in range(65,91)}
        for w in self.keyboard_frame.winfo_children():
            w.destroy()
        self.build_keyboard()

        self.entry.delete(0,"end")
        self.update_score()

        if self.timed.get():
            self.time_left = self.time_choice.get()
            self.update_timer()
        else:
            self.timer_lbl.config(text="")

        self.apply_theme()

    def submit(self):
        guess = self.entry.get().lower()
        if len(guess) != self.word_len.get():
            messagebox.showinfo("Oops", "Wrong length!")
            return
        if guess not in self.words:
            messagebox.showinfo("Invalid", "Word not in list!")
            return

        self.entry.delete(0,"end")
        target = list(self.target)
        colors = ["absent"]*self.word_len.get()

        for i in range(len(guess)):
            if guess[i] == target[i]:
                colors[i] = "correct"
                target[i] = None

        for i in range(len(guess)):
            if guess[i] in target and colors[i] == "absent":
                colors[i] = "present"
                target[target.index(guess[i])] = None

        for i,ch in enumerate(guess.upper()):
            self.tiles[self.row][i].config(
                text=ch, bg=THEMES[self.theme][colors[i]]
            )
            self.update_keyboard(ch, colors[i])

        if all(c=="correct" for c in colors):
            self.wins += 1
            self.score += 100
            self.show_result(True)
            return

        self.row += 1
        if self.row == 6:
            self.show_result(False)

    def show_result(self, won):
        meanings = dictionary_lookup(self.target) or ["Meaning not available."]
        popup = tk.Toplevel(self.root)
        popup.title("Game Over")
        popup.geometry("450x320")

        tk.Label(
            popup,
            text="🎉 YOU WON!" if won else "💀 GAME OVER",
            font=("Poppins",14,"bold")
        ).pack(pady=6)

        tk.Label(
            popup,
            text=f"Word: {self.target.upper()}",
            font=("Poppins",12,"bold")
        ).pack()

        text = tk.Text(popup, wrap="word", height=8)
        text.pack(padx=8,pady=6)

        for i,m in enumerate(meanings[:3],1):
            text.insert("end", f"{i}. {m}\n\n")

        text.config(state="disabled")

    def update_keyboard(self, ch, state):
        rank={"unused":0,"absent":1,"present":2,"correct":3}
        if rank[state] > rank[self.keyboard_state[ch]]:
            self.keyboard_state[ch] = state
            self.keys[ch].config(bg=THEMES[self.theme][state])

    def build_keyboard(self):
        self.keys={}
        rows=["QWERTYUIOP","ASDFGHJKL","ZXCVBNM"]
        for row in rows:
            f=tk.Frame(self.keyboard_frame)
            f.pack()
            for ch in row:
                b=tk.Button(f, text=ch, width=3)
                b.pack(side="left", padx=2)
                self.keys[ch]=b

    def update_timer(self):
        self.timer_lbl.config(text=f"⏳ Time: {self.time_left}s")
        if self.time_left == 0:
            self.show_result(False)
            return
        self.time_left -= 1
        self.timer_job = self.root.after(1000, self.update_timer)

    def update_score(self):
        self.score_lbl.config(
            text=f"🏅 Score: {self.score} | 🎮 Games: {self.games} | ✅ Wins: {self.wins}"
        )

    def apply_theme(self):
        self.theme = self.theme_var.get()
        t = THEMES[self.theme]

        self.root.config(bg=t["bg"])
        self.container.config(bg=t["bg"])
        self.canvas.config(bg=t["bg"])
        self.main.config(bg=t["bg"])

        self.banner.config(bg=t["bg"], fg=t["text"])
        self.score_lbl.config(bg=t["bg"], fg=t["text"])
        self.timer_lbl.config(bg=t["bg"], fg=t["text"])

        for row in getattr(self,"tiles",[]):
            for tile in row:
                if tile.cget("text")=="":
                    tile.config(bg=t["tile"])

# ---------------- RUN ----------------
root = tk.Tk()
WordleArena(root)
root.mainloop()
