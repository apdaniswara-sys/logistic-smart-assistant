import os
import tkinter as tk
from tkinter import scrolledtext
from src.nlp_logic import process_query
from src.tts_manager import TTSManager

tts = TTSManager()

class LogisticAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Logistic Assistant")
        self.root.geometry("720x520")
        self.root.configure(bg="#f2f2f2")

        # Chatbox
        self.chat_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state='disabled',
            bg="white", fg="black", font=("Segoe UI", 10)
        )
        self.chat_box.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # Input
        input_frame = tk.Frame(self.root, bg="#f2f2f2")
        input_frame.pack(fill=tk.X, padx=15, pady=(0,10))
        self.entry = tk.Entry(input_frame, font=("Segoe UI", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,10))
        self.entry.bind("<Return>", self.send_message)
        send_btn = tk.Button(input_frame, text="Kirim", command=self.send_message, bg="#4CAF50", fg="white")
        send_btn.pack(side=tk.RIGHT)

        self.display_message("", "Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")
        tts.speak("Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")

        # Hentikan TTS saat window ditutup
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def display_message(self, sender, message):
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, f"{sender} {message}\n")
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.display_message("🧍 Anda:", user_input)
        self.entry.delete(0, tk.END)
        try:
            response = process_query(user_input)
        except Exception as e:
            response = f"⚠️ Error: {e}"
        self.display_message("🤖 Bot:", response)
        tts.speak(response)

    def on_close(self):
        tts.stop()
        self.root.destroy()


def run_gui():
    root = tk.Tk()
    app = LogisticAssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
