from crewai import Crew, Process
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from agents.agents import Agents
from tasks.tasks import InstructorTasks, AssistantTasks
from tools.tools import TelegramTools
from pydub import AudioSegment
import json 
import re 
import emoji
import google.generativeai as genai
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from PIL import Image
import os
#import torch
#from TTS.api import TTS

#device = "cuda" if torch.cuda.is_available() else "cpu"
#tts = TTS("tts_models/en/ljspeech/tacotron2-DDC").to(device)

history_users = {}
search = DuckDuckGoSearchRun()
search_tool = Tool(
    name="search\_tool",
    description="A search tool used to query DuckDuckGo for search results when trying to find information from the internet.",
    func=search.run
    )
    
# Função para criar um teclado inline
def create_quiz_inline_keyboard(alt1, alt2, alt3, alt4, correct_alt):
    markup = InlineKeyboardMarkup(row_width=1)
    button1 = InlineKeyboardButton(text=alt1, callback_data="alt1_correct" if correct_alt == "alt1" else "alt1")
    button2 = InlineKeyboardButton(text=alt2, callback_data="alt2_correct" if correct_alt == "alt2" else "alt2")
    button3 = InlineKeyboardButton(text=alt3, callback_data="alt3_correct" if correct_alt == "alt3" else "alt3")
    button4 = InlineKeyboardButton(text=alt4, callback_data="alt4_correct" if correct_alt == "alt4" else "alt4")
    markup.add(button1, button2, button3, button4)
    return markup

# Função para criar um teclado inline para selecionar a categoria
def create_category_selection_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    categories = ['Grammar', 'Vocabulary', 'Culture', 'SciFi', 'Pop', 'World']
    buttons = [InlineKeyboardButton(text=category, callback_data=f"category_{category.lower()}") for category in categories]
    markup.add(*buttons)
    return markup

def create_level_selection_keyboard():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [KeyboardButton(text=str(level)) for level in range(1, 6)]
    markup.add(*buttons)
    return markup

def escape_markdown(text):
    escape_chars = r'\_[]()~`>#|{}'
    return ''.join([f'\\{char}' if char in escape_chars else char for char in text])

def remove_emojis(text):
    # Converte emojis para texto (por exemplo, 😀 para :grinning_face:)
    text = emoji.demojize(text)
    # Remove os equivalentes de texto dos emojis
    return re.sub(r':\w+:', '', text)


# Função para converter mp3 para ogg com codificação Opus
def convert_mp3_to_ogg(mp3_file_path, ogg_file_path):
    audio = AudioSegment.from_mp3(mp3_file_path)
    audio.export(ogg_file_path, format="ogg", codec="libopus")

# Função para configurar os handlers
def setup_handlers(bot, transcriber, audio_synth, gemini, IBMtts):
    
    quizzes = []
    conversation_history = {
        "conversation_history": []
    }   
    conversation_status = False
    category = ""
    agents = Agents([])
    Instructor_agent = agents.instructor_agent()
    Assistant_agent = agents.assistant_agent()
    tasks = InstructorTasks(agent=Instructor_agent)
    assist = AssistantTasks(agent= Assistant_agent)

    def update_state1(output):
        print('End of Quiz')
        #print(output.raw_output)
        
    def update_state2(output):
        print('End of Feedback')
        #print(output.raw_output)
    
    # Handler para seleção da categoria do quiz
    @bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
    def handle_category_selection(call: CallbackQuery):
        nonlocal category
        category = call.data.split("_")[1]
        user_id = call.message.chat.id
        bot.send_message(user_id, f"You selected the category: {category.capitalize()}", parse_mode="Markdown")
        bot.send_message(
            user_id, 
            "Please select the difficulty level (1-5):", 
            parse_mode="Markdown", 
            reply_markup=create_level_selection_keyboard()
        )


    # Handler para seleção do nível de dificuldade do quiz
    @bot.message_handler(func=lambda message: message.text.isdigit() and 1 <= int(message.text) <= 5)
    def handle_level_selection(message):
        nonlocal quizzes
        nonlocal category
        user_id = message.chat.id
        level = int(message.text)
        send_quiz(user_id, level, category)
        
        
    @bot.callback_query_handler(func=lambda call: True)
    def handle_quiz_answer(call: CallbackQuery):
        nonlocal quizzes
        user_answer = call.data.split('_')[0]
        
        if quizzes and 'user_alt' not in quizzes[-1]:
            quizzes[-1].setdefault('user_alt', user_answer)
            if "_correct" in call.data:
                bot.send_message(call.message.chat.id, "Correct answer!")
            else:
                bot.send_message(call.message.chat.id, "Incorrect answer. Try again!")
            bot.answer_callback_query(call.id)
            Instructor_task2 = tasks.dar_feedback(
                tools=[TelegramTools(bot).user_send_message], 
                user_id=call.from_user.id, 
                context=quizzes[-1], 
                callback=update_state2)
            crew = Crew(
                agents=[Instructor_agent],
                tasks=[Instructor_task2],
                verbose=False
            )
            result = crew.kickoff()

            with open('./feedback.ogg', 'wb') as audio_file:
                audio_file.write(
                    IBMtts.synthesize(
                        Instructor_task2.output.raw,
                        voice='en-US_MichaelV3Voice',
                        accept='audio/ogg'        
                    ).get_result().content)

            #tts.tts_to_file(text=Instructor_task2.output.raw, file_path="./feedback.wav")
            # with open('./feedback.wav', "rb") as voice:
            #     bot.send_voice(call.from_user.id, voice)
            #audio_synth.create_audio_file(Instructor_task2.output.raw, './feedback.mp3')
            #convert_mp3_to_ogg('./feedback.mp3', './feedback.ogg')
            with open('./feedback.ogg', "rb") as voice:
                bot.send_voice(call.from_user.id, voice)
        # Notifica que a resposta foi processada
        
    
         
    @bot.message_handler(content_types=['voice'])
    def handle_voice_message(message):
        voice_file_id = message.voice.file_id
        file_info = bot.get_file(voice_file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("./user_voice.ogg", 'wb') as new_file:
            new_file.write(downloaded_file)
        
        audio_file = genai.upload_file(f'./user_voice.ogg',mime_type='audio/ogg')          
        response = gemini.send_message(['', audio_file])
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No valid JSON found in the response text")
        response_json = json.loads(json_str)
        # response_json = transcriber.transcribe_audio("./user_voice.ogg")
        # response = json.loads(response_json)
        # transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        transcript = response_json['transcription']
        nonlocal conversation_status
        if conversation_status:
            new_message = {
                "role": message.chat.id,
                "content": transcript,
            }
            conversation_history["conversation_history"].append(new_message)
    
            # Instructor_task3 = assist.conversation_assistant(
            #         tools=[TelegramTools(bot).search], 
            #         user_id=message.chat.id, 
            #         context=conversation_history["conversation_history"], 
            #         callback=[])
            # crew = Crew(
            #     agents=[Assistant_agent],
            #     tasks=[Instructor_task3],
            #     verbose=False
            # )
            # result = crew.kickoff()
            # task_output = Instructor_task3.output
            # print(task_output.raw)
           
            #task_output = transcript
            
            new_message = {
            "role": "Instructor",
            "content": response_json['output'],
            }
            #conversation_history["conversation_history"][-1]["content"] = task_output.raw
            conversation_history["conversation_history"].append(new_message)
            #audio_synth.create_audio_file(remove_emojis(task_output), './conversation.mp3')
            #convert_mp3_to_ogg('./conversation.mp3', './conversation.ogg')
            # with open('./conversation.ogg', 'wb') as audio_file:
            #     audio_file.write(
            #         IBMtts.synthesize(
            #             remove_emojis(task_output),
            #             voice='en-US_MichaelV3Voice',
            #             accept='audio/ogg'        
            #         ).get_result().content)
                
            # with open('./conversation.ogg', "rb") as voice:
            #     bot.send_voice(message.chat.id, voice)
            #bot.reply_to(message, f"{response_json['output']}")
            bot.reply_to(message, response_json['output'], parse_mode='markdown')
    
    # Definir comando para iniciar a conversação
    @bot.message_handler(commands=['conversation'])
    def start_conversation(message):
        user_id = message.chat.id
        nonlocal conversation_status
        nonlocal conversation_history
        if not conversation_status:
            conversation_status = True
            response = gemini.send_message("""For the conversation section, please avoid adding timestamps to 
                                           the student's voice recordings. You will receive the audio and should 
                                           continue the dialogue naturally, as you would in a typical conversation 
                                           session. Please respond without hesitation to what the student requests.
                                           Your response MUST be a json formatted string with the following format:
                                           {
                                               transcription: transcript,
                                               output: response 
                                           }
                                           where transcript is the transcription content of the user audio (if empty, transcript = ''), 
                                           and response is your naturally dialogue response.
                                           DO NOT ADD ANY COMMENTS OR ANYTHING ELSE, JUST EXACTLY THE FORMAT ABOVE.""")
            
            Instructor_task3 = tasks.conversation(
                    tools=[TelegramTools(bot).user_send_message], 
                    user_id=user_id, 
                    context=conversation_history["conversation_history"], 
                    callback=update_state2)
            crew = Crew(
                agents=[Instructor_agent],
                tasks=[Instructor_task3],
                verbose=False
            )
            result = crew.kickoff()
            task_output = Instructor_task3.output
            print(task_output.raw)
            new_message = {
            "role": "model",
            "content": (result),
            }
            conversation_history["conversation_history"].append(new_message)
            #audio_synth.create_audio_file(task_output.raw, './conversation.mp3')
            #convert_mp3_to_ogg('./conversation.mp3', './conversation.ogg')
            # with open('./conversation.ogg', 'wb') as audio_file:
            #     audio_file.write(
            #         IBMtts.synthesize(
            #             task_output.raw,
            #             voice='en-US_MichaelV3Voice',
            #             accept='audio/ogg'        
            #         ).get_result().content)
                
            # with open('./conversation.ogg', "rb") as voice:
            #     bot.send_voice(user_id, voice)
            #bot.send_message(user_id, task_output.raw, parse_mode="Markdown")
        
    # Definir comando para iniciar o quiz
    @bot.message_handler(commands=['startquiz'])
    def start_quiz(message):
        nonlocal quizzes
        user_id = message.chat.id
      
        parts = message.text.split()
        if len(parts) > 1 and parts[1].isdigit() and 1 <= int(parts[1]) <= 5:
            level = int(parts[1])
            bot.send_message(user_id, "Please select a category:", reply_markup=create_category_selection_keyboard())
        else:
            bot.send_message(user_id, "Please select a category:", reply_markup=create_category_selection_keyboard())
            #bot.send_message(user_id, "Please select the difficulty level (1-5):", reply_markup=create_level_selection_keyboard())

        
    def send_quiz(user_id, level, category):
        Instructor_task1 = tasks.quiz(
                tools=[TelegramTools(bot).quiz, search_tool], 
                user_id=user_id, 
                context=quizzes, 
                level=level,
                category=category,
                callback=update_state1)
        crew = Crew(
            agents=[Instructor_agent],
            tasks=[Instructor_task1],
            verbose=True
        )
        result = crew.kickoff()
        result_json =  re.sub(r'\}\s*[^}]*$', '}', Instructor_task1.output.raw)
        try:
            result_dict = json.loads(result_json) 
            quizzes.append(result_dict) 
            try:
                markup = create_quiz_inline_keyboard(
                    quizzes[-1]['alt1'], 
                    quizzes[-1]['alt2'], 
                    quizzes[-1]['alt3'], 
                    quizzes[-1]['alt4'], 
                    quizzes[-1]['answer']
                )
                bot.send_message(user_id, f"❓ {escape_markdown(quizzes[-1]['question'])}", parse_mode="Markdown", reply_markup=markup)
            except Exception as inst:
                    print(inst)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            
    # Manipulador de mensagens de texto
    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        chat_id = message.chat.id
        text = message.text
        response = []
        try:
            response = gemini.send_message(text)
            bot.send_message(chat_id, response.text, parse_mode='markdown')
        except:
            try:
                bot.send_message(chat_id, response.text)
            except Exception as inst:
                print(inst)    

    
    # Manipulador de fotos
    @bot.message_handler(content_types=['photo'])
    def handle_photo(message):
        chat_id = message.chat.id
        file_id = message.photo[-1].file_id # Pega a foto de maior resolução
        text = message.caption 

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open('./temp.jpg', 'wb') as new_file:
            new_file.write(downloaded_file)

        image = Image.open('./temp.jpg')
        response = gemini.send_message([text, image])
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No valid JSON found in the response text")
        response_json = json.loads(json_str)
        output = response_json['output']
        try:
            bot.send_message(chat_id, output, parse_mode='markdown')
        except:
            try:
                bot.send_message(chat_id, output)
            except Exception as inst:
                print(inst)   

        os.remove('./temp.jpg')