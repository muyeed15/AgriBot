"""
AgriBot - Voice Assistant for Bangladeshi Farmers

A voice-activated assistant providing agricultural advice in Bengali. Uses speech recognition, 
machine translation, and text-to-speech to interact with users. Processes queries specifically 
related to Bangladeshi agriculture as defined in instructions.txt.

Usage:
1. Hold 'Control' key to record voice query in Bengali
2. Release 'Control' to process query
3. Press 'ESC' to exit

Architecture Components:
- VoiceRecorder: Captures audio input
- KeyHandler: Manages push-to-talk functionality
- AgriBot: Coordinates translation, AI processing, and speech output
- AgriAI: Interface with LM Studio language model
- AgriTranslator: Handles EN<->BN translations
- AgriTTS: Manages text-to-speech output

Dependencies: speech_recognition, gtts, googletrans, vlc, pynput, lmstudio
"""

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
import re

class AgriAI:
    """Interface with LM Studio language model for agricultural queries"""
    def __init__(self, model):
        """
        Initialize AI model interface
        :param model: Name of LM Studio model (e.g., "hermes-3-llama-3.2-3b")
        """
        self.model = model
        self.system_prompt = (
            "You are Agri, a mature, precise, and friendly voice assistant specializing exclusively in Bangladeshi agriculture and fisheries. "
            "Your expertise covers crop management, irrigation, pest control, soil health, modern farming techniques, and sustainable fish farming practices in Bangladesh. "
            "For every query, first determine if it relates to Bangladeshi agriculture or fisheries; if not, reply only with: "
            "'I specialize in Bangladeshi agricultural and fisheries advice. How can I help with your farming needs?' "
            "If it does, provide one to two concise and pinpoint sentences with direct, mature advice that answers exactly as asked. "
            "For queries that require quantitative guidance, such as fertilizer amounts, include a specific recommendation based on common Bangladeshi practices, using numbers fully written out in words and avoiding numeric digits or symbols. "
            "User Query: "
        )

    def ask(self, prompt):
        """Get response from language model"""
        full_prompt = f"{self.system_prompt}{prompt}\nAnswer:"
        return lms.llm(self.model).respond(full_prompt)

class AgriTranslator:
    """Handles text translation between Bengali and English"""
    def __init__(self):
        self.translator = Translator()
        
    async def translate(self, text, src, dest):
        """
        Async text translation
        :param text: Input text to translate
        :param src: Source language code (e.g., 'en')
        :param dest: Target language code (e.g., 'bn')
        :return: Translated text
        """
        translation = await self.translator.translate(text, src=src, dest=dest)
        return translation.text

class AgriTTS:
    """Text-to-speech system with rate control and thread management"""
    def __init__(self):
        self.is_speaking = False
        self.speech_thread = None
        self.player = None

    def speak(self, text, lang, slow):
        """Internal speech generation method (runs in thread)"""
        self.is_speaking = True
        try:
            myobj = gTTS(text=text, lang=lang, slow=slow)
            myobj.save("output.mp3")
            self.player = vlc.MediaPlayer("output.mp3")
            self.player.set_rate(1.5)  # 1.5x playback speed
            self.player.play()
            # Maintain playback until audio ends or interrupted
            while self.player.get_state() not in [vlc.State.Ended, vlc.State.Stopped] and self.is_speaking:
                time.sleep(0.1)
        finally:
            self.is_speaking = False
            self.player = None

    def start_speaking(self, text, lang="bn", slow=False):
        """Start speech output in dedicated thread"""
        self.stop()
        self.speech_thread = threading.Thread(target=self.speak, args=(text, lang, slow))
        self.speech_thread.daemon = True
        self.speech_thread.start()

    def stop(self):
        """Interrupt current speech output"""
        if self.is_speaking and self.player:
            self.player.stop()
        self.is_speaking = False

class AgriBot:
    """Main assistant class coordinating translation and processing"""
    def __init__(self, model):
        """
        :param model: LM Studio model name for AgriAI
        """
        self.model = model
        self.translator = AgriTranslator()
        self.tts = AgriTTS()
        self.is_processing = False
        self.processing_task = None
        
    async def ask(self, prompt):
        """Process user query pipeline:
        1. BN -> EN translation
        2. Get AI response
        3. EN -> BN translation
        4. Speech output
        """
        self.is_processing = True
        try:
            en_prompt = await self.translator.translate(text=prompt, src="bn", dest="en")
            en_ai_result = str(AgriAI(model=self.model).ask(prompt=en_prompt))
            # Remove <think>...</think> tags and content between them, then strip extra spaces
            cleaned_en_ai_result = re.sub(r'<think>.*?</think>', '', en_ai_result, flags=re.DOTALL).strip()
            # Remove extra blank lines
            cleaned_en_ai_result = re.sub(r'\n{2,}', '\n', cleaned_en_ai_result).strip()
            bn_ai_result = await self.translator.translate(text=cleaned_en_ai_result, src="en", dest="bn")
            
            self.tts.start_speaking(bn_ai_result)
            return bn_ai_result
        finally:
            self.is_processing = False
        
    def stop_speaking(self):
        """Stop current speech output"""
        self.tts.stop()
        
    def cancel_processing(self):
        """Cancel ongoing processing tasks"""
        self.stop_speaking()
        if self.processing_task:
            self.processing_task.cancel()
            self.is_processing = False

class VoiceRecorder:
    """Handles audio input through microphone"""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = None
        self.recording = False
        self.frames = []
        self.audio_source = None
        self.sample_rate = None
        self.sample_width = None
        
    def start_recording(self):
        """Initialize audio capture settings"""
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
        """Internal method for continuous audio capture"""
        try:
            with self.mic as source:
                while self.recording:
                    # Capture audio in 0.1s chunks
                    buffer = self.recognizer.record(source, duration=0.1)
                    self.frames.append(buffer.frame_data)
                    time.sleep(0.05)
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self.recording = False
    
    def stop_recording(self):
        """Stop audio capture"""
        self.recording = False
        
    def get_audio_data(self):
        """Compile captured audio into AudioData object"""
        if not self.frames:
            return None
        
        audio_data = b''.join(self.frames)
        return sr.AudioData(audio_data, self.sample_rate, self.sample_width)

class KeyHandler:
    """Manages push-to-talk functionality and keyboard input"""
    def __init__(self, bot):
        """
        :param bot: AgriBot instance to handle processing
        """
        self.bot = bot
        self.recorder = VoiceRecorder()
        self.key_listener = None
        self.exit_requested = False
        self.ctrl_pressed = False
        
    def on_press(self, key):
        """Handle key press events"""
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
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
        """Handle key release events"""
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r) and self.ctrl_pressed:
            self.ctrl_pressed = False
            self.recorder.stop_recording()
            threading.Thread(target=self._process_audio).start()

    def _process_audio(self):
        """Process captured audio after recording"""
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
        """Execute processing pipeline for recognized text"""
        response = await self.bot.ask(prompt=text)
        print("\nএগ্রিবট উত্তর (AgriBot response):")
        print(f"➤ {response}")

    def start(self):
        """Start keyboard listener"""
        self.key_listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.key_listener.start()
        
        # Main loop monitoring exit status
        while not self.exit_requested and self.key_listener.is_alive():
            time.sleep(0.1)
        
        self.recorder.stop_recording()
        self.bot.stop_speaking()

async def main():
    """Main entry point with dependency checks and initialization"""
    required_packages = ["speech_recognition", "gtts", "googletrans", "lmstudio", "vlc", "pynput"]
    missing_packages = []
    
    # Verify required packages are installed
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