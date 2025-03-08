from gtts import gTTS
import os

def speak_text(text: str, lang: str, speed: bool) -> str:
    myobj = gTTS(text=text, lang=lang, slow=speed)
    myobj.save("output.mp3")
    os.system("output.mp3")

print(speak_text(text="দিপ-রা কেমন আছো?", lang="bn", speed=False))
