# AgriBot

AgriBot is a voice-activated assistant designed to provide precise agricultural advice to Bangladeshi farmers in Bengali. It integrates speech recognition, machine translation, and text-to-speech synthesis to deliver relevant farming insights efficiently.

## Features

- **Push-to-Talk Interaction**: Hold `Control` to speak, release to process, `ESC` to exit.
- **Localized Knowledge**: Answers exclusively pertain to Bangladeshi agriculture.
- **AI-Driven Responses**: Uses LM Studio models for intelligent query handling.
- **Real-Time Translation**: Converts Bengali speech to English for AI processing and translates responses back to Bengali.
- **Text-to-Speech Output**: Reads responses aloud in Bengali for accessibility.

## Architecture

- **VoiceRecorder** – Captures voice input.
- **KeyHandler** – Manages push-to-talk functionality.
- **AgriBot** – Orchestrates AI, translation, and speech output.
- **AgriAI** – Interfaces with LM Studio for AI-driven responses.
- **AgriTranslator** – Handles bidirectional English-Bengali translation.
- **AgriTTS** – Manages text-to-speech synthesis.

## Installation

Ensure Python 3.8+ is installed, then install dependencies:

```sh
pip install speech_recognition gtts googletrans vlc pynput lmstudio
```

For `pyaudio` (required for speech recognition):

- **Windows**: `pip install pipwin && pipwin install pyaudio`
- **Mac**: `brew install portaudio && pip install pyaudio`
- **Linux**: `sudo apt-get install python3-pyaudio`

## Usage

Run AgriBot with:

```sh
python main.py
```

- Hold `Control` to record a query in Bengali.
- Release `Control` to process and receive a response.
- Press `ESC` to exit.

## Limitations

- Only provides responses related to Bangladeshi agriculture.
- Does not handle non-agricultural or general knowledge queries.
- Requires an internet connection for translation and AI processing.

## License

MIT License. See `LICENSE` for details.
