import os
import threading
import asyncio
import tkinter as tk
from tkinter import scrolledtext
from playsound import playsound
import edge_tts
from src.nlp_logic import process_query, load_data

# 🗣️ Fungsi untuk TTS Natural (Bahasa Indonesia)
async def speak_async(text):
    try:
        filename = "reply.mp3"
        tts = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")

        # edge_tts >= 6.0 pakai async generator
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                with open(filename, "ab") as f:
                    f.write(chunk["data"])

        if os.path.exists(filename):
            playsound(filename)
            os.remove(filename)

    except Exception as e:
        print(f"[❌] Gagal memutar suara: {e}")


def speak(text):
    """Jalankan TTS di thread terpisah"""
    threading.Thread(target=lambda: asyncio.run(speak_async(text)), daemon=True).start()


# 🧠 GUI Utama Smart Logistic Assistant
class LogisticAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Logistic Assistant (v2.2)")
        self.root.geometry("720x520")
        self.root.configure(bg="#f2f2f2")

        # 🔹 Area output percakapan
        self.chat_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state='disabled',
            bg="white", fg="black", font=("Segoe UI", 10)
        )
        self.chat_box.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

        # 🔹 Input user
        input_frame = tk.Frame(self.root, bg="#f2f2f2")
        input_frame.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.entry = tk.Entry(input_frame, font=("Segoe UI", 11))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry.bind("<Return>", self.send_message)

        send_btn = tk.Button(
            input_frame, text="Kirim", command=self.send_message,
            bg="#4CAF50", fg="white", font=("Segoe UI", 10)
        )
        send_btn.pack(side=tk.RIGHT)

        # Sapaan awal
        self.display_message("🤖 Bot", "Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")
        speak("Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")

    def display_message(self, sender, message):
        """Tampilkan pesan di chatbox"""
        self.chat_box.config(state='normal')
        self.chat_box.insert(tk.END, f"{sender}: {message}\n")
        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def send_message(self, event=None):
        """Proses input teks user"""
        user_input = self.entry.get().strip()
        if not user_input:
            return

        self.display_message("🧍 Anda", user_input)
        self.entry.delete(0, tk.END)

        # Proses query pakai NLP (versi terbaru)
        try:
            response = process_query(user_input)  # ✅ hanya 1 argumen
        except Exception as e:
            response = f"⚠️ Error: {e}"

        self.display_message("🤖 Bot", response)
        speak(response)


# 🚀 Fungsi main untuk jalankan GUI
def run_gui():
    root = tk.Tk()
    app = LogisticAssistantGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
