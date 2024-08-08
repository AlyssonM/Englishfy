#from telebot import TeleBot
#from telebot import apihelper
from telegram.ext import Application
from telegram import Update
from os import environ
from dotenv import load_dotenv
from agents.crewai_telemetry import *
from command_handlers import telegram_handlers_v2
from tools.tools import TelegramTools
from text_speech.deepgram import DeepgramTranscriber, DeepgramAudioSynthesizer
import time
import google.generativeai as genai
from gemini.GeminiFactory import GeminiFactory
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import json 

load_dotenv()

# Carrega as API keys
API_KEY = environ.get("DG_API_KEY")
#GOOGLE_API_KEY = environ.get('GOOGLE_API_KEY')

# apihelper.SESSION_TIME_TO_LIVE = 60*5
# bot = TeleBot(environ.get("BOT_TOKEN2"))

# Configura modelo llm Gemini
#genai.configure(api_key=environ.get('GOOGLE_API_KEY'))
#model = genai.GenerativeModel('gemini-1.5-flash')
#gemini = model.start_chat(history=[])

# Configura Text-to-Speech IBM Watson
authenticator = IAMAuthenticator(environ.get('IBM_API_KEY'))
IBMtts = TextToSpeechV1(
    authenticator=authenticator
)
IBMtts.set_service_url(environ.get('IBM_API_URL'))
#voices = text_to_speech.list_voices().get_result()
#print(json.dumps(voices, indent=2))
#voice = text_to_speech.get_voice('en-US_MichaelV3Voice').get_result()

# Inicializa as ferramentas do Telegram
#tools = TelegramTools(bot)

# Configura text-to-speech e speech-to-text
transcriber = DeepgramTranscriber(API_KEY)
audio_synth = DeepgramAudioSynthesizer(API_KEY)

# Configura os handlers
#telegram_handlers.setup_handlers(bot, transcriber, audio_synth, gemini, IBMtts)

# Desabilita a telemetria da Crew AI
disable_crewai_telemetry()


# Inicia o bot
# def start_bot():
#     while True:
#         try:
#             bot.infinity_polling(timeout=10, long_polling_timeout=5)
#         except Exception as e:
#             print(f"Error: {e}")
#             print("Reiniciando o polling em 15 segundos...")
#             time.sleep(15)  # Espera 15 segundos antes de reiniciar o polling

if __name__ == "__main__":
    #bot.infinity_polling(timeout=10, long_polling_timeout=5)
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(environ.get("BOT_TOKEN3")).build()
    telegram_handlers_v2.setup_handlers(application, GeminiFactory(), IBMtts)
    # Run the bot until the user presses Ctrl-C
 
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
