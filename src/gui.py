import tkinter as tk
from tkinter import scrolledtext
import asyncio
from src.nlp_voice import listen_and_recognize, speak
from src.nlp_logic import process_query




class LogisticAssistantGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Smart Logistic Assistant")
        self.window.geometry("600x500")
        self.window.configure(bg="#1E1E1E")  # latar belakang gelap modern

        # Judul
        self.title_label = tk.Label(
            self.window,
            text="🧠 Smart Logistic Assistant",
            font=("Segoe UI", 16, "bold"),
            bg="#1E1E1E",
            fg="#00BFFF"
        )
        self.title_label.pack(pady=10)

        # Area percakapan
        self.chat_area = scrolledtext.ScrolledText(
            self.window,
            wrap=tk.WORD,
            state="disabled",
            width=70,
            height=20,
            bg="#2D2D2D",
            fg="#FFFFFF",
            font=("Consolas", 10)
        )
        self.chat_area.pack(padx=10, pady=10)

        # Tombol voice
        self.voice_button = tk.Button(
            self.window,
            text="🎤 Bicara",
            font=("Segoe UI", 12, "bold"),
            bg="#00BFFF",
            fg="white",
            relief="flat",
            command=self.handle_voice_command
        )
        self.voice_button.pack(pady=10)

        # Sapaan awal dari bot
        self.display_message("🤖 Bot", "Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")
        asyncio.run(speak("Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?"))

        self.window.mainloop()

    # 🗨️ Tampilkan pesan di area chat
    def display_message(self, sender, message):
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, f"{sender}: {message}\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.yview(tk.END)

    # 🎤 Tangani perintah suara
    def handle_voice_command(self):
        self.display_message("🧍 Anda", "Silakan bicara...")
        try:
            text = listen_and_recognize()
            if not text:
                self.display_message("🤖 Bot", "Maaf, saya tidak mendengar dengan jelas.")
                return

            self.display_message("🧍 Anda", text)
            response = process_query(text)
            self.display_message("🤖 Bot", response)

            # Suara jawaban
            asyncio.run(speak(response))

        except Exception as e:
            self.display_message("⚠️ Error", str(e))


if __name__ == "__main__":
    gui = LogisticAssistantGUI()
    gui.mainloop()

