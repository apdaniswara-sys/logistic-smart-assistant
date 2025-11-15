import threading
import customtkinter as ctk
from src.nlp_logic import process_query
from src.tts_manager import TTSManager

tts = TTSManager()

# Appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Logistic Assistant")
        self.geometry("750x580")
        self.minsize(600, 500)

        # =========================
        # FRAME CHAT (WhatsApp style)
        # =========================
        self.chat_frame = ctk.CTkScrollableFrame(
            self,
            width=730,
            height=480,
            fg_color="#ECE5DD"   # warna WA background
        )
        self.chat_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # =========================
        # INPUT AREA (proporsional)
        # =========================
        input_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=15)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        # ENTRY
        self.entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ketik pesan...",
            height=40
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=8)
        self.entry.bind("<Return>", self.send_message)

        # BUTTON
        send_btn = ctk.CTkButton(
            input_frame,
            text="Kirim",
            width=90,
            height=40,
            corner_radius=8,
            command=self.send_message
        )
        send_btn.pack(side="right", padx=(5, 10), pady=8)

        # =========================
        # WELCOME MESSAGE
        # =========================
        welcome = "Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?"
        self.add_message("🤖 Bot", welcome)
        threading.Thread(target=lambda: tts.speak(welcome), daemon=True).start()

    # =================================================================
    # TAMBAHKAN BUBBLE CHAT (ala WhatsApp)
    # =================================================================
    def add_message(self, sender, message):
        is_user = "🧍" in sender

        bubble_color = "#DCF8C6" if is_user else "#FFFFFF"
        anchor_side = "e" if is_user else "w"

        bubble = ctk.CTkLabel(
            self.chat_frame,
            text=message,
            justify="left",
            wraplength=520,
            fg_color=bubble_color,
            text_color="black",
            corner_radius=12,
            padx=12,
            pady=8
        )

        bubble.pack(anchor=anchor_side, pady=4, padx=10)

    # =================================================================
    # KIRIM PESAN
    # =================================================================
    def send_message(self, event=None):
        user_input = self.entry.get().strip()   # ← sudah diperbaiki
        if not user_input:
            return

        self.add_message("🧍 Anda", user_input)
        self.entry.delete(0, "end")

        try:
            response = process_query(user_input)
        except Exception as e:
            response = f"⚠️ Error: {e}"

        self.add_message("🤖 Bot", response)
        threading.Thread(target=lambda: tts.speak(response), daemon=True).start()


# ============================================================
# AGAR BISA DIPANGGIL DARI main.py
# ============================================================
def run_gui():
    app = ChatApp()
    app.mainloop()
