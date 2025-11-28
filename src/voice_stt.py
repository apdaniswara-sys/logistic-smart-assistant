# src/voice_stt.py
# Voice to Text menggunakan SpeechRecognition + Google Web Speech API

import speech_recognition as sr


def listen_and_recognize(timeout=6, phrase_time_limit=6):
    """
    Mendengarkan suara user lalu transkripsi ke teks.
    Menggunakan Google Speech Recognition (online).
    """
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            recognizer.energy_threshold = 300
            recognizer.pause_threshold = 0.8

            try:
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                return "❌ Tidak ada suara terdeteksi."

        try:
            # transkripsi menggunakan Google
            text = recognizer.recognize_google(audio, language="id-ID")
            return text.strip()

        except sr.UnknownValueError:
            return "❌ Suara tidak jelas."
        except sr.RequestError:
            return "❌ Tidak dapat menghubungi Google Speech API."

    except Exception as e:
        return f"❌ Error microphone: {e}"
