import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import sounddevice as sd
import scipy.io.wavfile as wav
from playsound import playsound
import os

# ====== 1. Cấu hình Gemini API ======
API_KEY = "AIzaSyD0r0KdTPHshd9FTCT1OCmMnC8Ug5wo-9E"   # ⚠️ thay bằng API key thật
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# ====== 2. Text-to-Speech bằng gTTS + playsound ======
def speak(text):
    try:
        filename = "reply.mp3"
        tts = gTTS(text=text, lang="vi")
        tts.save(filename)

        # 🔥 Phát luôn không cần mở app ngoài
        playsound(filename)

        return filename
    except Exception as e:
        print("❌ Lỗi TTS:", e)
        return None

# ====== 3. Thu âm mic bằng sounddevice ======
def listen_from_mic(duration=5, fs=16000):
    print(f"🎤 Đang nghe trong {duration} giây...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="int16")
    sd.wait()
    filename = "input.wav"
    wav.write(filename, fs, recording)
    
    # Nhận dạng với Google Speech Recognition
    r = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language="vi-VN")
        print("🗣️ Bạn nói:", text)
        return text
    except sr.UnknownValueError:
        print("❌ Không nhận dạng được giọng nói.")
        return None
    except sr.RequestError as e:
        print("❌ Lỗi khi gọi Google Speech Recognition:", e)
        return None

# ====== 4. Chat loop ======
def chat_loop():
    while True:
        user_text = listen_from_mic(duration=5)
        if not user_text:
            continue
        if user_text.lower() in ["thoát", "dừng", "exit", "quit"]:
            print("👋 Kết thúc trò chuyện.")
            break

        # Gửi lên Gemini API
        response = model.generate_content(user_text)
        bot_reply = response.text
        print("🤖 Bot:", bot_reply)

        # Bot nói lại
        speak(bot_reply)

if __name__ == "__main__":
    chat_loop()
