import asyncio
from googletrans import Translator

async def translate_texts():
    translator = Translator()
    translation_en_bn = await translator.translate("Hello, how are you?", src='en', dest='bn')
    print("English to Bangla:", translation_en_bn.text)

    translation_bn_en = await translator.translate("আপনি কেমন আছেন?", src='bn', dest='en')
    print("Bangla to English:", translation_bn_en.text)

asyncio.run(translate_texts())
