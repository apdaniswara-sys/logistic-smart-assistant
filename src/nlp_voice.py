import asyncio
import queue
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from edge_tts import Communicate
import playsound

# Queue untuk audio input
q = queue.Queue()

# Load Vosk model Bahasa Indonesia
# Pastikan model sudah di-download di folder "model/vosk-model-small-id"
model = Model("model/vosk-model-small-id")
rec = KaldiRecognizer(model, 16000)

def callback(indata, frames, time, status):
    """
    Callback untuk audio stream Vosk
    """
    q.put(bytes(indata))

def listen_and_recognize():
    """
    Mendengarkan voice command dan mengembalikan teks user.
    """
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        print("Silakan berbicara...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                user_text = result.get("text", "")
                if user_text:
                    return user_text

async def speak(text):
    """
    Text to Speech menggunakan Edge TTS.
    File audio disimpan sebagai reply.mp3 dan diputar dengan playsound.
    """
    communicate = Communicate(text, voice="id-ID-ArdiNeural")
    await communicate.save("reply.mp3")
    playsound.playsound("reply.mp3")

# Contoh penggunaan (test mandiri)
if __name__ == "__main__":
    # Tes text to speech
    asyncio.run(speak("Halo, saya siap membantu Anda!"))

    # Tes speech to text
    print("Mulai uji voice command...")
    user_input = listen_and_recognize()
    print(f"Anda berkata: {user_input}")
