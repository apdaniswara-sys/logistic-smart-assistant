import os
import threading
import asyncio
from playsound import playsound
import edge_tts

class TTSManager:
    def __init__(self):
        self.current_task = None
        self.filename = "reply.mp3"
        self.stop_flag = False

    async def _speak_async(self, text):
        try:
            tts = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")
            if os.path.exists(self.filename):
                os.remove(self.filename)
            async for chunk in tts.stream():
                if self.stop_flag:
                    break
                if chunk["type"] == "audio":
                    with open(self.filename, "ab") as f:
                        f.write(chunk["data"])
            if not self.stop_flag and os.path.exists(self.filename):
                playsound(self.filename)
                os.remove(self.filename)
        except Exception as e:
            print(f"[❌] Gagal memutar suara: {e}")

    def speak(self, text):
        """Jalankan TTS di thread terpisah"""
        self.stop_flag = False
        if self.current_task and self.current_task.is_alive():
            self.stop()  # hentikan task sebelumnya
        self.current_task = threading.Thread(target=lambda: asyncio.run(self._speak_async(text)), daemon=True)
        self.current_task.start()

    def stop(self):
        """Hentikan TTS yang sedang berjalan"""
        self.stop_flag = True
        if os.path.exists(self.filename):
            try:
                os.remove(self.filename)
            except:
                pass
