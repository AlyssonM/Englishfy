from telebot import TeleBot
from telebot import apihelper
from os import environ
from dotenv import load_dotenv
from command_handlers import telegram_handlers
from tools.tools import TelegramTools
from text_speech.deepgram import DeepgramTranscriber, DeepgramAudioSynthesizer
import time
import google.generativeai as genai
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import json 

load_dotenv()

# Carrega as API keys
API_KEY = environ.get("DG_API_KEY")
GOOGLE_API_KEY = environ.get('GOOGLE_API_KEY')

apihelper.SESSION_TIME_TO_LIVE = 60*5
bot = TeleBot(environ.get("BOT_TOKEN"))

# Configura modelo llm Gemini
genai.configure(api_key=environ.get('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-pro-latest')
gemini = model.start_chat(history=[])

# Configura Text-to-Speech IBM Watson
authenticator = IAMAuthenticator(environ.get('IBM_API_KEY'))
IBMtts = TextToSpeechV1(
    authenticator=authenticator
)
IBMtts.set_service_url('https://api.us-south.text-to-speech.watson.cloud.ibm.com/instances/77de050e-305c-4fff-8a7e-57023427ccf9')
#voices = text_to_speech.list_voices().get_result()
#print(json.dumps(voices, indent=2))
#voice = text_to_speech.get_voice('en-US_MichaelV3Voice').get_result()

# Inicializa as ferramentas do Telegram
tools = TelegramTools(bot)

# Configura text-to-speech e speech-to-text
transcriber = DeepgramTranscriber(API_KEY)
audio_synth = DeepgramAudioSynthesizer(API_KEY)
# Configura os handlers
telegram_handlers.setup_handlers(bot, transcriber, audio_synth, gemini, IBMtts)




# Inicia o bot
def start_bot():
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"Error: {e}")
            print("Reiniciando o polling em 15 segundos...")
            time.sleep(15)  # Espera 15 segundos antes de reiniciar o polling

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
