#from langchain.agents import Tool
#from langchain.agents import load_tools
from langchain_community.tools import DuckDuckGoSearchRun
from crewai_tools import tool
from telebot import TeleBot
from os import environ
from dotenv import load_dotenv

load_dotenv()

bot = TeleBot(environ.get("BOT_TOKEN2"))


class TelegramTools:
    # def __init__(self, bot):
    #     self.bot = bot
    
    @tool('DuckDuckGoSearch')
    def search(search_query: str):
        """Search the web for information on a given topic"""
        return DuckDuckGoSearchRun().run(search_query)
    
    # @tool
    # def user_send_message(user_id:str, response:str) -> str:
    #     """
    #     Function to interact with students in the telegram chat.
        
    #     Args:
    #         user_id (str): The unique identifier for the user.
    #         response (str): The message to be sent to the user.
        
    #     Returns:
    #         str: The message that was sent to the user.
    #     """
    #     try:
    #         bot.send_message(user_id, response, parse_mode='Markdown')
    #     except Exception as inst:
    #         print(inst)
    #     return response
    
    @tool
    def quiz(user_id:str, quiz_id:int, question:str, alt1:str, alt2:str, alt3:str, alt4:str, answer:str) -> str:
        """
        Function to generate a single quiz question to a user_id in telegram with multiple choice answers.
        
        Args:
            user_id (str): The unique telegram identifier for the user.
            quiz_id (int): The unique quiz id.
            question (str): The quiz question to be presented to the user.
            alt1 (str): The text for the first answer option.
            alt2 (str): The text for the second answer option.
            alt3 (str): The text for the third answer option.
            alt4 (str): The text for the fourth answer option.
            answer(str): The correct alternative field name (alt1 or alt2 or alt3 or alt4)
            
        Returns:
            json_output(str): A json formatted output string from Args.
        """
        json_output = {}
    
        json_output = {
            "quiz_id" : quiz_id,
            "question" : question,
            "alt1": alt1,
            "alt2": alt2,
            "alt3": alt3,
            "alt4": alt4,
            "answer": answer
        }
        
        # try:
        #     bot.send_message(user_id, f"❓ {escape_markdown(question)}", parse_mode="Markdown", reply_markup=markup)
        # except Exception as inst:
        #     print(inst)
        return json_output
    
    
    
        
    
    
            
    
