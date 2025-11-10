import os
import asyncio
import speech_recognition as sr
import edge_tts
from playsound import playsound
import time

# 🎤 Dengarkan suara user dan ubah ke teks (pakai Google Speech API)
def listen_and_recognize():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print("🧍 Anda: Silakan bicara...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)

    try:
        text = recognizer.recognize_google(audio, language="id-ID")
        print(f"🧍 Anda berkata: {text}")
        return text
    except sr.UnknownValueError:
        print("🤖 Bot: Maaf, saya tidak dapat mendengar dengan jelas.")
        return None
    except sr.RequestError:
        print("🤖 Bot: Gagal menghubungi layanan pengenalan suara. Coba lagi sebentar...")
        time.sleep(3)
        return None
    except Exception as e:
        print(f"🤖 Bot: Terjadi error saat mendengarkan: {e}")
        return None


# 🔊 Bacakan teks secara natural dengan Edge TTS (Microsoft online)
async def speak(text):
    try:
        filename = "reply.mp3"
        communicate = edge_tts.Communicate(text, voice="id-ID-ArdiNeural")

        # Simpan hasil ke file
        await communicate.save(filename)

        if os.path.exists(filename):
            playsound(filename)
            os.remove(filename)
        else:
            print("🤖 Bot: File suara tidak ditemukan.")
    except Exception as e:
        print(f"⚠️ Gagal memutar suara: {e}")
        # fallback: print teks jika suara gagal
        print(f"🤖 {text}")
