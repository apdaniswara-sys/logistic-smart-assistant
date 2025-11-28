# src/gui.py
import os
import threading
import time
import traceback

import customtkinter as ctk
from PIL import Image

from src.nlp_logic import process_query
from src.tts_manager import TTSManager

# optional audio libs
try:
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False

# speechrecognition availability for voice_stt fallback (listen_and_recognize uses SR)
try:
    import speech_recognition as sr  # noqa: F401
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False

# optional whisper (keberadaan tidak dipakai untuk Google hold-to-talk)
try:
    import whisper  # noqa: F401
    WHISPER_AVAILABLE = True
except Exception:
    WHISPER_AVAILABLE = False

# assets folder
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
SEND_ICON = os.path.join(ASSETS_DIR, "send.png")
MIC_ICON = os.path.join(ASSETS_DIR, "mic.png")
MIC_REC_ICON = os.path.join(ASSETS_DIR, "mic_rec.png")
BOT_AVATAR = os.path.join(ASSETS_DIR, "bot.png")
USER_AVATAR = os.path.join(ASSETS_DIR, "user.png")
LOGO_ICON = os.path.join(ASSETS_DIR, "logo.png")

tts = TTSManager()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


def load_ctk_image(path, size=None):
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


class PremiumChatGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Logistic Assistant")
        self.geometry("1000x700")
        self.minsize(900, 650)

        # state
        self.conversations = []
        self.is_recording = False
        self.record_file = None
        self.auto_play_recordings = False
        self.wake_word_enabled = False
        self._wake_thread = None
        self._wake_stop_flag = threading.Event()

        # images
        self.img_send = load_ctk_image(SEND_ICON, (26, 26))
        self.img_mic = load_ctk_image(MIC_ICON, (24, 24))
        self.img_mic_rec = load_ctk_image(MIC_REC_ICON, (24, 24))
        self.avatar_bot = load_ctk_image(BOT_AVATAR, (42, 42))
        self.avatar_user = load_ctk_image(USER_AVATAR, (42, 42))
        self.logo_img = load_ctk_image(LOGO_ICON, (28, 28))

        # layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self._build_sidebar()

        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nswe", padx=8, pady=8)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.chat_scroll = ctk.CTkScrollableFrame(self.main_frame, fg_color="#0f1414")
        self.chat_scroll.grid(row=0, column=0, sticky="nswe", padx=8, pady=(8, 4))

        self._build_input_area()

        # typing bubble ref
        self.typing_bubble = None
        self.typing = False

        # welcome
        self.add_bot_message("Selamat datang di Smart Logistic Assistant.")
        threading.Thread(target=lambda: tts.speak("Selamat datang di Smart Logistic Assistant. Apakah ada yang bisa saya bantu?"), daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_sidebar(self):
        header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header.pack(fill="x", pady=(8, 6))
        if self.logo_img:
            lbl_logo = ctk.CTkLabel(header, image=self.logo_img, text="")
            lbl_logo.pack(side="left", padx=(8, 6))
        ctk.CTkLabel(header, text="SmartLog", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")

        ctk.CTkLabel(self.sidebar, text="Daily Diagnostic", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(8, 6))
        qf = ctk.CTkFrame(self.sidebar)
        qf.pack(fill="x", padx=8)

        diagnostic_cmds = [
            ("Kondisi safety", "Bagaimana kondisi safety hari ini"),
            ("Absensi hari ini", "Bagaimana rekap absensi karyawan hari ini"),
            ("Kondisi stock", "material apa saja yang shortage hari ini"),            
            ("top 5 Critical stock", "Berikan top 5 stock paling kritikal"),
            ("Delivery Performance", "Bagaimana performance delivery hari ini"),            
            ("jadwal meeting", "event meeting apa saja yang dijadwalkan hari ini"),
        ]
        for title, cmd in diagnostic_cmds:
            ctk.CTkButton(qf, text=title, fg_color="#2E7D32", corner_radius=8, command=lambda c=cmd: self._quick_send(c)).pack(fill="x", pady=6)

        ctk.CTkLabel(self.sidebar, text="Conversation History", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(12, 4))
        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, height=260)
        self.history_frame.pack(fill="both", padx=8, pady=(0, 8), expand=True)

    def _quick_send(self, text):
        self.entry_text.set(text)
        self._on_send()

    def _build_input_area(self):
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.grid(row=1, column=0, sticky="we", padx=8, pady=6)
        input_frame.grid_columnconfigure(0, weight=1)

        self.entry_text = ctk.StringVar()

        entry = ctk.CTkEntry(input_frame, textvariable=self.entry_text, placeholder_text="Ketik pesan...", height=44)
        entry.grid(row=0, column=0, sticky="we", padx=(6, 6))
        entry.bind("<Return>", lambda e: self._on_send())

        btn_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        # MIC: *no click-to-toggle* to avoid double events; uses press/release for hold-to-talk
        self.btn_mic = ctk.CTkButton(btn_frame, text="", width=48, height=40, corner_radius=12, image=self.img_mic, fg_color="#1B5E20", hover_color="#388E3C", command=None)
        self.btn_mic.grid(row=0, column=0, padx=(0, 6))

        # bind press/release (best-effort)
        try:
            self.btn_mic.bind("<ButtonPress-1>", lambda e: self._on_mic_press_start())
            self.btn_mic.bind("<ButtonRelease-1>", lambda e: self._on_mic_press_release())
        except Exception:
            # fallback toggle if bind not supported
            self.btn_mic.configure(command=lambda: threading.Thread(target=self._on_mic_click_toggle, daemon=True).start())

        self.btn_send = ctk.CTkButton(btn_frame, width=58, height=44, text="", corner_radius=12, command=self._on_send, image=self.img_send)
        self.btn_send.grid(row=0, column=1)

    # Message handlers
    def add_user_message(self, text):
        self._add_message(text, side="right", avatar=self.avatar_user)

    def add_bot_message(self, text):
        self._add_message(text, side="left", avatar=self.avatar_bot)

    def _add_message(self, text, side="left", avatar=None):
        try:
            row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
            row.pack(fill="x", pady=6)
            if side == "left" and avatar:
                ctk.CTkLabel(row, image=avatar, text="").pack(side="left", padx=(6, 10))

            bubble_color = "#2E7D32" if side == "right" else "#1F2A2B"
            lbl = ctk.CTkLabel(row, text=text, wraplength=640, justify="left", fg_color=bubble_color, corner_radius=12, padx=12, pady=10, text_color="white")
            if side == "left":
                lbl.pack(side="left")
            else:
                lbl.pack(side="right")

            if side == "right" and avatar:
                ctk.CTkLabel(row, image=avatar, text="").pack(side="right", padx=(10, 6))

            self.chat_scroll.update_idletasks()
            try:
                self.after(20, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))
            except Exception:
                pass

            self.conversations.append((side, text))
            self._update_history()
        except Exception:
            traceback.print_exc()

    def _update_history(self):
        for w in self.history_frame.winfo_children():
            w.destroy()
        for _, text in self.conversations[-12:]:
            short = text[:40] + "..." if len(text) > 40 else text
            ctk.CTkLabel(self.history_frame, text=short, anchor="w").pack(fill="x", padx=6, pady=3)

    # Send / backend
    def _on_send(self):
        txt = self.entry_text.get().strip()
        if not txt:
            return
        self.entry_text.set("")
        self.add_user_message(txt)
        self._start_typing()
        threading.Thread(target=self._backend_process, args=(txt,), daemon=True).start()

    def _backend_process(self, text):
        try:
            reply = process_query(text)
        except Exception:
            reply = "Maaf, terjadi masalah pada sistem."
        self._stop_typing()
        self.add_bot_message(reply)
        try:
            tts.speak(reply)
        except Exception:
            pass

    # Hold-to-talk behavior
    def _on_mic_click_toggle(self):
        if not SOUND_AVAILABLE or not SR_AVAILABLE:
            return
        if not self.is_recording:
            self._on_mic_press_start()
        else:
            self._on_mic_press_release()

    def _on_mic_press_start(self):
        if not SR_AVAILABLE:
            return
        if self.is_recording:
            return
        self.is_recording = True
        try:
            if self.img_mic_rec:
                self.btn_mic.configure(image=self.img_mic_rec, fg_color="#C62828")
            else:
                self.btn_mic.configure(fg_color="#C62828")
        except Exception:
            pass

    def _on_mic_press_release(self):
        if not SR_AVAILABLE:
            return
        if not self.is_recording:
            return
        self.is_recording = False
        try:
            if self.img_mic:
                self.btn_mic.configure(image=self.img_mic, fg_color="#1B5E20")
            else:
                self.btn_mic.configure(fg_color="#1B5E20")
        except Exception:
            pass
        # transcribe using src.voice_stt.listen_and_recognize (Google STT)
        threading.Thread(target=self._voice_from_google, daemon=True).start()

    def _voice_from_google(self):
        try:
            from src.voice_stt import listen_and_recognize
        except Exception:
            return
        text = listen_and_recognize()
        if not text or text.startswith("❌"):
            return
        self.add_user_message(text)
        self._start_typing()
        try:
            reply = process_query(text)
        except Exception:
            reply = "Maaf, terjadi masalah."
        self._stop_typing()
        self.add_bot_message(reply)
        try:
            tts.speak(reply)
        except Exception:
            pass

    # Typing bubble (race-safe)
    def _start_typing(self):
        # stop any previous animation
        self._stop_typing()

        bubble = ctk.CTkFrame(self.chat_scroll, fg_color="#1F2A2B", corner_radius=12)
        bubble.pack(anchor="w", padx=10, pady=6)
        self.typing_bubble = bubble
        self.typing = True

        dot_frame = ctk.CTkFrame(bubble, fg_color="transparent")
        dot_frame.pack(padx=8, pady=6)

        dots = []
        for i in range(3):
            d = ctk.CTkLabel(dot_frame, text="●", text_color="#888", font=ctk.CTkFont(size=12))
            d.grid(row=0, column=i, padx=2)
            dots.append(d)

        def animate(bubble_ref, dots_ref):
            index = 0
            while self.typing:
                # check existence
                if bubble_ref is None or not bubble_ref.winfo_exists():
                    break
                for i, dot in enumerate(dots_ref):
                    if not dot.winfo_exists():
                        return
                    color = "white" if i == index else "#555"
                    try:
                        # schedule on main thread
                        self.after(0, lambda d=dot, c=color: d.configure(text_color=c))
                    except Exception:
                        return
                index = (index + 1) % 3
                time.sleep(0.35)

            # remove bubble safely
            try:
                if bubble_ref and bubble_ref.winfo_exists():
                    self.after(0, bubble_ref.destroy)
            except Exception:
                pass

        threading.Thread(target=animate, args=(bubble, dots), daemon=True).start()
        self.chat_scroll.update_idletasks()
        try:
            self.after(20, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))
        except Exception:
            pass

    def _stop_typing(self):
        self.typing = False

    def on_close(self):
        try:
            tts.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def run_gui():
    app = PremiumChatGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
