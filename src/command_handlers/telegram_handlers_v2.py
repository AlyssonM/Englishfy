import json
import re
import os
from PIL import Image
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, CallbackContext, ConversationHandler
)
import google.generativeai as genai
from crewai import Crew, Process
from agents.agents import Agents
from tasks.tasks import InstructorTasks, AssistantTasks
from tools.tools import TelegramTools
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun

user_sessions = {}

QUIZ_CATEGORY, QUIZ_LEVEL, CONVERSATION, QUIZ_QUESTION = range(4)


def escape_markdown(text):
    escape_chars = r'\_[]()~`>#|{}'
    return ''.join([f'\\{char}' if char in escape_chars else char for char in text])

search = DuckDuckGoSearchRun()
search_tool = Tool(
    name="search\_tool",
    description="A search tool used to query DuckDuckGo for search results when trying to find information from the internet.",
    func=search.run
    )

def setup_handlers(app, gemini_factory, IBMtts):
    # Configure o Crew AI
    agents = Agents([])
    Instructor_agent = agents.instructor_agent()
    Assistant_agent = agents.assistant_agent()
    tasks = InstructorTasks(agent=Instructor_agent)
    assist = AssistantTasks(agent=Assistant_agent)
    
    # Definir comando para iniciar a conversação
    async def start_bot(update: Update, context: CallbackContext) -> None:
        user_id = update.effective_user.id
        await update.message.reply_text("Please, send your Gemini Api Key with the command /set_api.")
        
        
    async def set_api(update: Update, context: CallbackContext) -> None:
        user_id = update.effective_user.id
        api_key = update.message.text.split(maxsplit=1)[1]
        user_sessions[user_id] = {
            "api_key": api_key,
            "gemini": gemini_factory.create_instance(api_key),  # Substitua por sua instância real
            "status": False,
            "conversation_history": [],
            "quizzes": []
        }
        await update.message.reply_text("API key configured successfully. Let's start!")
        await update.message.delete()
    
    async def fallback(update: Update, context: CallbackContext):
        await update.message.reply_text("Workflow error. Try again....")
        return ConversationHandler.END  # ou QUIZ_CATEGORY para reiniciar o quiz
   
    async def cancel(update: Update, context: CallbackContext) -> int:
        user_id = update.effective_user.id
        await context.bot.send_message(chat_id=user_id, text="End of conversation.")
        return ConversationHandler.END
    
    async def handle_photo(update: Update, context: CallbackContext) -> None:
        user_id = update.effective_user.id
        if user_id not in user_sessions:
            await update.message.reply_text("Please, configure your API key with the command /set_api.")
            return
        session = user_sessions[user_id]
        gemini = session["gemini"]
        photo_file = await update.message.photo[-1].get_file()
        photo_path = f'./temp_{user_id}.jpg'
        await photo_file.download_to_drive(custom_path=photo_path)
        text = update.message.caption if update.message.caption else "" 
        image = Image.open(photo_path)
        response = gemini.send_message([text, image])  # Simulação de uma função de processamento
        print(response.text)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError("No valid JSON found in the response text")
        response_json = json.loads(json_str)
        output = response_json['output']
        try:
            await update.message.reply_text(output, parse_mode='Markdown')
        except Exception as e:
            try:
                await update.message.reply_text(output)
            except Exception as inst:
                print(inst)

        os.remove(photo_path)

    async def start_conversation(update: Update, context: CallbackContext) -> int:
        user_id = update.effective_user.id
        
        await update.message.reply_text("Nice, let's talk...")
        session = user_sessions[user_id]
        gemini = session["gemini"]
        if not session["status"]:
            session["status"] = True
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
            print(response.text)
        
        return CONVERSATION

    async def handle_conversation(update: Update, context: CallbackContext) -> int:
        user_id = update.effective_user.id
        if user_id not in user_sessions:
            await update.message.reply_text("Please, configure your API key with the command /set_api.")
            return
        session = user_sessions[user_id]
        gemini = session["gemini"]
        if update.message.voice:
            # Processamento de mensagens de voz
            voice_file = await update.message.voice.get_file()
            voice_path = f"./voice_{user_id}.ogg"
            await voice_file.download_to_drive(custom_path=voice_path)
            # Aqui você precisaria integrar seu próprio STT
            audio_file = genai.upload_file(f"./voice_{user_id}.ogg",mime_type='audio/ogg') 
            response = gemini.send_message(['', audio_file])
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No valid JSON found in the response text")
            
            response_json = json.loads(json_str)
            os.remove(voice_path)
            # response_json = transcriber.transcribe_audio("./user_voice.ogg")
            # response = json.loads(response_json)
            # transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            transcript = response_json['transcription']
            if session["status"]:
                new_message = {
                    "role": user_id,
                    "content": transcript,
                }
                session["conversation_history"].append(new_message)

                new_message = {
                    "role": "Instructor",
                    "content": response_json['output'],
                }
                session["conversation_history"].append(new_message)
                
                audio_file_path = './conversation.ogg'
                with open(audio_file_path, 'wb') as audio_file:
                        audio_file.write(
                            IBMtts.synthesize(
                                response_json['output'],
                                voice='en-US_MichaelV3Voice',
                                accept='audio/ogg'        
                            ).get_result().content)
                
                await update.message.reply_text(response_json['output'], parse_mode='markdown')
                await context.bot.send_voice(chat_id=user_id, voice=open(audio_file_path, 'rb'))
                
                  
        else:
            # Processamento de mensagens de texto
            text = update.message.text
            response = user_sessions[user_id]['gemini'].send_message(text)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No valid JSON found in the response text")
            
            response_json = json.loads(json_str)
            await update.message.reply_text(response_json['output'], parse_mode='markdown')
            
        return CONVERSATION

    # async def handle_message(update: Update, context: CallbackContext) -> None:
    #     user_id = update.effective_user.id
    #     if user_id not in user_sessions:
    #         await update.message.reply_text("Por favor, configure sua chave API com o comando /set_api.")
    #         return
    #     text = update.message.text
    #     response = user_sessions[user_id]['gemini'].send_message(text)
    #     json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
    #     if json_match:
    #         json_str = json_match.group(0)
    #     else:
    #         raise ValueError("No valid JSON found in the response text")
        
    #     response_json = json.loads(json_str)
    #     await update.message.reply_text(response_json['output'], parse_mode='markdown')


    async def start_quiz(update: Update, context: CallbackContext) -> int:
        user_id = update.effective_user.id
        if user_id not in user_sessions:
            await update.message.reply_text("Please, configure your API key with the command /set_api.")
            return
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Grammar", callback_data="Grammar")],
            [InlineKeyboardButton("Vocabulary", callback_data="Vocabulary")],
            [InlineKeyboardButton("Culture", callback_data="Culture")],
            [InlineKeyboardButton("Sports", callback_data="Sports")],
            [InlineKeyboardButton("World", callback_data="World")],
            [InlineKeyboardButton("Pop", callback_data="Pop")],
            [InlineKeyboardButton("SciFi", callback_data="SciFi")],
        ])
        await update.message.reply_text("select the category:", reply_markup=markup)
        return QUIZ_CATEGORY

    async def quiz_category(update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
        category = query.data
        context.user_data["category"] = category
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Beginner", callback_data="Beginner")],
            [InlineKeyboardButton("Intermediate", callback_data="Intermediate")],
            [InlineKeyboardButton("Advanced", callback_data="Advanced")]
        ])
        await query.edit_message_text(f"Category {category} selected. Please, select the level:", reply_markup=markup)
        return QUIZ_LEVEL
    
    async def quiz_level(update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        await query.answer()
        level = query.data
        context.user_data["level"] = level
        await query.edit_message_text(f"Level *{level}* selected. Formulating question...", parse_mode="markdown")
        return await send_quiz_question(update, context)


    async def send_quiz_question(update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        user_id = update.effective_user.id
        session = user_sessions[user_id]
        Instructor_task1 = tasks.quiz(
                tools=[TelegramTools().quiz, search_tool], 
                user_id=user_id, 
                context=session["quizzes"], 
                level=context.user_data["level"],
                category=context.user_data["category"],
                callback=[])
        crew = Crew(
            agents=[Instructor_agent],
            tasks=[Instructor_task1],
            verbose=True
        )
        result = crew.kickoff()
        try:
            result_json =  re.sub(r'\}\s*[^}]*$', '}', Instructor_task1.output.raw)
            result_dict = json.loads(result_json) 
            session["quizzes"].append(result_dict)
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(session["quizzes"][-1]['alt1'], callback_data="alt1_correct" if session["quizzes"][-1]['answer'] == "alt1" else "alt1")],
                [InlineKeyboardButton(session["quizzes"][-1]['alt2'], callback_data="alt2_correct" if session["quizzes"][-1]['answer'] == "alt2" else "alt2")],
                [InlineKeyboardButton(session["quizzes"][-1]['alt3'], callback_data="alt3_correct" if session["quizzes"][-1]['answer'] == "alt3" else "alt3")],
                [InlineKeyboardButton(session["quizzes"][-1]['alt4'], callback_data="alt4_correct" if session["quizzes"][-1]['answer'] == "alt4" else "alt4")]
            ])
            await query.message.reply_text(f"❓ {escape_markdown(session['quizzes'][-1]['question'])}", reply_markup=markup)
        except Exception as inst:
                    print(inst)
                    return ConversationHandler.END
        
        return QUIZ_QUESTION

    async def quiz_answer(update: Update, context: CallbackContext) -> int:
        user_id = update.effective_user.id
        if user_id not in user_sessions:
            await context.bot.send_message(user_id, "Please, configure your API key with the command /set_api.")
            return ConversationHandler.END
        session = user_sessions[user_id]
        query = update.callback_query
        await query.answer()
        user_response = query.data  # This would be the user's selected answer
        user_answer = query.data.split('_')[0]
        if session["quizzes"] and 'user_alt' not in session["quizzes"][-1]:
            session["quizzes"][-1].setdefault('user_alt', user_answer)
            if "_correct" in query.data:
                await query.message.reply_text("Correct answer!")
                feedback_msg = "Good Work!"
            else:
                await query.message.reply_text("Incorrect answer. Try again!")
                Instructor_task2 = tasks.dar_feedback(
                tools=[], 
                user_id=user_id, 
                context=session["quizzes"][-1], 
                callback=[])
                crew = Crew(
                    agents=[Instructor_agent],
                    tasks=[Instructor_task2],
                    verbose=False
                )
                result = crew.kickoff()
                feedback_msg = Instructor_task2.output.raw
                
        
        audio_file_path = './feedback.ogg'
        with open(audio_file_path, 'wb') as audio_file:
                audio_file.write(
                    IBMtts.synthesize(
                        feedback_msg, # Instructor_task2.output.raw,
                        voice='en-US_MichaelV3Voice',
                        accept='audio/ogg'        
                    ).get_result().content)
        
        await query.message.reply_text(feedback_msg, parse_mode='markdown')
        await context.bot.send_voice(chat_id=user_id, voice=open(audio_file_path, 'rb'))     
         
        # Decide what to do next after an answer is given
        return ConversationHandler.END  # Optionally, continue the quiz or end the conversation


    app.add_handler(ConversationHandler(
        entry_points=[
            CommandHandler("start", start_bot),
            CommandHandler('startquiz', start_quiz), 
            CommandHandler('conversation', start_conversation),
            CommandHandler("set_api", set_api),
            CommandHandler('cancel', cancel)
        ],
        states={
            QUIZ_CATEGORY: [CallbackQueryHandler(quiz_category)],
            QUIZ_LEVEL: [CallbackQueryHandler(quiz_level)],
            CONVERSATION: [MessageHandler(filters.VOICE | filters.TEXT & ~filters.COMMAND, handle_conversation)],
            QUIZ_QUESTION: [CallbackQueryHandler(quiz_answer)]
        },
        fallbacks=[
            CommandHandler('cancel', cancel), 
            MessageHandler(filters.ALL, fallback)
        ]
    ))
    
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

