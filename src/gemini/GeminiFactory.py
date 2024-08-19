import asyncio
import requests
from google.generativeai import configure, GenerativeModel
import base64
import json
import aiohttp
from gemini.retry_decorator import retry  # Importando o decorator

class GeminiFactory:
    def __init__(self, api_key):
        self.lock = asyncio.Lock()
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        self.api_key = api_key
        self.session = aiohttp.ClientSession()  # Cria uma sessão HTTP para reuso em chamadas API
        self.status = False
        self.history = []
        self.quizzes = []
        
    async def create_instance(self, api_key):
        async with self.lock:
            self.base_url = self.base_url + f"key={api_key}",
            #self.api_key = api_key
            # configure(api_key=api_key)
            # model = GenerativeModel('gemini-1.5-flash')
            # gemini = await model.start_chat(history=[])
            #return gemini
            return {
                "baseurl": self.base_url + f"key={api_key}",
                "gemini": self,
                "status": False,
                "conversation_history": [],
                "quizzes": []
            }
                
    async def send_prompt(self, text):    
        # Endereço da API
        url = self.base_url
        # Preparando o cabeçalho
        headers = {
            'Content-Type': 'application/json'
        }
        # Construindo o corpo da requisição
        payload = {
            "contents": [{
                "parts": [
                    {"text": text},
                ]
            }]
        }
   
        # Fazendo a requisição POST
        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to send message: {response.status}, {await response.text()}")
    
    @retry(max_retries=3, delay=2, backoff=2, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))        
    async def send_message(self, message='', mime_type=None, file_path=None):
        headers = {
            'Content-Type': 'application/json'
        }

        if mime_type and file_path:
            with open(file_path, "rb") as data_file:
                base64_file = base64.b64encode(data_file.read()).decode('utf-8')
            await self.update_history(message, 'user', mime_type, base64_file)
        else:
            await self.update_history(message, 'user')

        contents = []
        for msg in self.history:
            parts = [{'text': msg['content']['text']}] if 'text' in msg['content'] else []
            if 'inline_data' in msg['content']:
                parts.append({'inline_data': msg['content']['inline_data']})
            contents.append({
                "role": msg['role'],
                "parts": parts
            })

        payload = {
            "contents": contents
        }

        async with self.session.post(self.base_url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                # Atualiza o histórico com a resposta do modelo, se houver
                if 'text' in data.get('contents', [{}])[0]:
                    await self.update_history(data['contents'][0]['text'], 'model')
                return data
            else:
                raise Exception(f"Failed to send message: {response.status}, {await response.text()}")

    async def update_history(self, message, role='user', mime_type=None, data=None):
        content = {}
        if message:
            content['text'] = message
        if mime_type and data:
            content['inline_data'] = {'mime_type': mime_type, 'data': data}
        self.history.append({'role': role, 'content': content})
        
    async def close(self):
        await self.session.close()