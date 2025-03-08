import speech_recognition as sr

def example_speech_recognition():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        
        print("Listening for Bangla speech...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="bn-BD")
        print(f"Recognized text: {text}")
    except Exception as e:
        print(f"Recognition failed: {e}")

example_speech_recognition()