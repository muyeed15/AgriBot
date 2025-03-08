import speech_recognition as sr
import sys
import asyncio
import vlc
from gtts import gTTS
from googletrans import Translator
import lmstudio as lms

class AgriAI:
    def __init__(self, model):
        self.model = model

    def ask(self, prompt):
        return lms.llm(self.model).respond(prompt)


class AgriTranslator:
    def __init__(self):
        self.translator = Translator()
        
    async def translate(self, text, src, dest):
        translation = await self.translator.translate(text, src=src, dest=dest)
        return translation.text


class AgriTTS:
    @staticmethod
    def speak(text, lang, slow):
        myobj = gTTS(text=text, lang=lang, slow=slow)
        myobj.save("output.mp3")
        player = vlc.MediaPlayer("output.mp3")
        player.set_rate(1.5)
        player.play()


class AgriBot:
    def __init__(self, model):
        self.model = model
        self.translator = AgriTranslator()
        
    async def ask(self, prompt):
        en_prompt = await self.translator.translate(text=prompt, src="bn", dest="en")
        en_ai_result = AgriAI(model=self.model).ask(prompt=en_prompt)
        bn_ai_result = await self.translator.translate(text=en_ai_result, src="en", dest="bn")
        AgriTTS.speak(text=bn_ai_result, lang="bn", slow=False)
        return bn_ai_result


async def recognize_bangla_speech_with_agribot():
    """
    Captures audio from the microphone, converts Bangla speech to text,
    and processes it through AgriBot.
    """
    recognizer = sr.Recognizer()
    bot = AgriBot(model="hermes-3-llama-3.2-3b")
    
    print("এগ্রিবট v0.0.1a")
    print("-------------")
    print("কথা বলুন... (Speak now...)")
    
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source)
                print("শনাক্ত করা হচ্ছে... (Recognizing...)")
                text = recognizer.recognize_google(audio, language="bn-BD")
                print("\nআপনার কথা (Your speech):")
                print(f"➤ {text}")
                print("\nএগ্রিবট প্রসেসিং... (AgriBot processing...)")
                response = await bot.ask(prompt=text)
                print("\nএগ্রিবট উত্তর (AgriBot response):")
                print(f"➤ {response}")
                print("\nআবার বলতে চান? (য/ন) [Want to speak again? (y/n)]")
                choice = input().lower()
                if choice not in ['য', 'y']:
                    break
                    
        except sr.UnknownValueError:
            print("দুঃখিত, আপনার কথা বোঝা যায়নি (Sorry, couldn't understand audio)")
        except sr.RequestError as e:
            print(f"Google Speech Recognition সার্ভিস ব্যর্থ হয়েছে; {e}")
            break
        except KeyboardInterrupt:
            print("\nপ্রোগ্রাম বন্ধ করা হচ্ছে (Exiting program)")
            break


async def main():
    required_packages = ["speech_recognition", "gtts", "googletrans", "lmstudio", "vlc"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Required packages not installed. Please install:")
        print(f"pip install {' '.join(missing_packages)}")
        print("For SpeechRecognition, you'll also need pyaudio:")
        if sys.platform == "win32":
            print("pip install pipwin && pipwin install pyaudio")
        elif sys.platform == "darwin":  # macOS
            print("brew install portaudio && pip install pyaudio")
        else:  # Linux
            print("sudo apt-get install python3-pyaudio")
        sys.exit(1)
    
    await recognize_bangla_speech_with_agribot()


if __name__ == "__main__":
    asyncio.run(main())