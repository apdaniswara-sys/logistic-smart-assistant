import customtkinter as ctk
from src.nlp_logic import process_query
from src.tts_manager import TTSManager

tts = TTSManager()

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Logistic Assistant")
        self.geometry("720x520")

        # Frame chat
        self.chat_frame = ctk.CTkScrollableFrame(self, width=700, height=450)
        self.chat_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Input
        self.entry = ctk.CTkEntry(self, placeholder_text="Ketik pesan...")
        self.entry.pack(side="left", padx=(10,0), pady=10, fill="x", expand=True)
        self.entry.bind("<Return>", self.send_message)

        send_btn = ctk.CTkButton(self, text="Kirim", command=self.send_message)
        send_btn.pack(side="right", padx=(0,10), pady=10)

        # Tampilan awal
        self.add_message("🤖 Bot", "Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")
        tts.speak("Selamat datang di Smart Logistic Assistant, apakah ada yang bisa saya bantu?")

    def add_message(self, sender, message):
        bubble = ctk.CTkLabel(self.chat_frame, text=message, wraplength=500, justify="left", 
                               fg_color="#DCF8C6" if "🧍" in sender else "#FFFFFF", 
                               corner_radius=15, padx=10, pady=5)
        bubble.pack(anchor="w" if "🧍" in sender else "e", pady=5, padx=5)

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return
        self.add_message("🧍 Anda", user_input)
        self.entry.delete(0, "end")
        try:
            response = process_query(user_input)
        except Exception as e:
            response = f"⚠️ Error: {e}"
        self.add_message("🤖 Bot", response)
        tts.speak(response)

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
    
