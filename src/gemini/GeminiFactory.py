import google.generativeai as genai
# Função factory para criar instâncias do Gemini
class GeminiFactory:
    def create_instance(self, api_key):
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        gemini = model.start_chat(history=[])
        return gemini
        