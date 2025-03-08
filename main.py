import speech_recognition as sr
import sys
import asyncio
import time
import threading
from pynput import keyboard
from gtts import gTTS
from googletrans import Translator
import vlc
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
    def __init__(self):
        self.is_speaking = False
        self.speech_thread = None
        self.player = None

    def speak(self, text, lang, slow):
        self.is_speaking = True
        try:
            myobj = gTTS(text=text, lang=lang, slow=slow)
            myobj.save("output.mp3")
            self.player = vlc.MediaPlayer("output.mp3")
            self.player.set_rate(1.5)
            self.player.play()
            while self.player.get_state() not in [vlc.State.Ended, vlc.State.Stopped] and self.is_speaking:
                time.sleep(0.1)
        finally:
            self.is_speaking = False
            self.player = None

    def start_speaking(self, text, lang="bn", slow=False):
        self.stop()
        self.speech_thread = threading.Thread(target=self.speak, args=(text, lang, slow))
        self.speech_thread.daemon = True
        self.speech_thread.start()

    def stop(self):
        if self.is_speaking and self.player:
            self.player.stop()
        self.is_speaking = False


class AgriBot:
    def __init__(self, model):
        self.model = model
        self.translator = AgriTranslator()
        self.tts = AgriTTS()
        self.is_processing = False
        self.processing_task = None
        
    async def ask(self, prompt):
        self.is_processing = True
        try:
            en_prompt = await self.translator.translate(text=prompt, src="bn", dest="en")
            en_ai_result = AgriAI(model=self.model).ask(prompt=en_prompt)
            bn_ai_result = await self.translator.translate(text=en_ai_result, src="en", dest="bn")
            
            self.tts.start_speaking(bn_ai_result)
            
            return bn_ai_result
        finally:
            self.is_processing = False
        
    def stop_speaking(self):
        self.tts.stop()
        
    def cancel_processing(self):
        self.stop_speaking()
        if self.processing_task:
            self.processing_task.cancel()
            self.is_processing = False


class VoiceRecorder:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = None
        self.recording = False
        self.frames = []
        self.audio_source = None
        self.sample_rate = None
        self.sample_width = None
        
    def start_recording(self):
        if self.recording:
            return
            
        self.recording = True
        self.frames = []

        try:
            self.mic = sr.Microphone()
            with self.mic as source:
                self.audio_source = source
                self.sample_rate = source.SAMPLE_RATE
                self.sample_width = source.SAMPLE_WIDTH
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
            
            
            threading.Thread(target=self._record_audio).start()
            
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.recording = False
    
    def _record_audio(self):
        try:
            with self.mic as source:
                while self.recording:
                    buffer = self.recognizer.record(source, duration=0.1)
                    self.frames.append(buffer.frame_data)
                    time.sleep(0.05)
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self.recording = False
    
    def stop_recording(self):
        self.recording = False
        
    def get_audio_data(self):
        if not self.frames:
            return None
        
        audio_data = b''.join(self.frames)
        return sr.AudioData(audio_data, self.sample_rate, self.sample_width)


class KeyHandler:
    def __init__(self, bot):
        self.bot = bot
        self.recorder = VoiceRecorder()
        self.key_listener = None
        self.exit_requested = False
        self.ctrl_pressed = False
        
    def on_press(self, key):
        if key == keyboard.Key.ctrl:
            if not self.ctrl_pressed:
                self.ctrl_pressed = True
                print("\nশুনছি... (Listening...)")

                self.bot.cancel_processing()
                self.recorder.start_recording()
                
        elif key == keyboard.Key.esc:
            print("\nপ্রোগ্রাম বন্ধ করা হচ্ছে (Exiting program)")
            self.exit_requested = True
            return False
    
    def on_release(self, key):
        if key == keyboard.Key.ctrl and self.ctrl_pressed:
            self.ctrl_pressed = False
            self.recorder.stop_recording()
            threading.Thread(target=self._process_audio).start()
    
    def _process_audio(self):
        audio_data = self.recorder.get_audio_data()
        if not audio_data:
            print("কোন আওয়াজ শোনা যায়নি (No speech detected)")
            return
            
        try:
            print("শনাক্ত করা হচ্ছে... (Recognizing...)")
            text = self.recorder.recognizer.recognize_google(audio_data, language="bn-BD")
            
            print("\nআপনার কথা (Your speech):")
            print(f"➤ {text}")
            print("\nএগ্রিবট প্রসেসিং... (AgriBot processing...)")

            loop = asyncio.new_event_loop()
            self.bot.processing_task = loop.create_task(self._run_processing(loop, text))
            loop.run_until_complete(self.bot.processing_task)
            
        except sr.UnknownValueError:
            print("দুঃখিত, আপনার কথা বোঝা যায়নি (Sorry, couldn't understand audio)")
        except sr.RequestError as e:
            print(f"Google Speech Recognition সার্ভিস ব্যর্থ হয়েছে; {e}")
        except asyncio.CancelledError:
            print("প্রক্রিয়া বাতিল করা হয়েছে (Processing cancelled)")
        except Exception as e:
            print(f"ত্রুটি (Error): {str(e)}")
    
    async def _run_processing(self, loop, text):
        response = await self.bot.ask(prompt=text)
        print("\nএগ্রিবট উত্তর (AgriBot response):")
        print(f"➤ {response}")
    
    def start(self):
        self.key_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.key_listener.start()
        
        while not self.exit_requested and self.key_listener.is_alive():
            time.sleep(0.1)
        
        self.recorder.stop_recording()
        self.bot.stop_speaking()


async def main():
    required_packages = ["speech_recognition", "gtts", "googletrans", "lmstudio", "vlc", "pynput"]
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
    
    try:
        print("এগ্রিবট v0.0.2a (Hold-to-Speak)")
        print("--------------------------------")
        print("'Control' চেপে ধরুন কথা বলার জন্য, ছেড়ে দিন শেষ করার জন্য")
        print("(Hold 'Control' to speak, release to finish)")
        print("'ESC' চাপুন প্রোগ্রাম বন্ধ করার জন্য (Press 'ESC' to exit)")
        
        bot = AgriBot(model="hermes-3-llama-3.2-3b")
        key_handler = KeyHandler(bot)
        key_handler.start()
        
    except KeyboardInterrupt:
        print("\nপ্রোগ্রাম বন্ধ করা হচ্ছে (Exiting program)")
    except Exception as e:
        print(f"অপ্রত্যাশিত ত্রুটি (Unexpected error): {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())