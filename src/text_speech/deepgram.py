import os
import re
import requests
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

class DeepgramTranscriber:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = DeepgramClient(api_key)
    
    def transcribe_audio(self, audio_file):
        try:
            with open(audio_file, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
            )

            response = self.client.listen.prerecorded.v("1").transcribe_file(payload, options)
            return response.to_json(indent=4)

        except Exception as e:
            return f"Exception: {e}"

class DeepgramAudioSynthesizer:
    DEEPGRAM_URL = 'https://api.deepgram.com/v1/speak?model=aura-zeus-en'
    
    def __init__(self, api_key):
        self.headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
    
    def segment_text_by_sentence(self, text):
        sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
        boundaries_indices = [boundary.start() for boundary in sentence_boundaries]
        
        segments = []
        start = 0
        for boundary_index in boundaries_indices:
            segments.append(text[start:boundary_index + 1].strip())
            start = boundary_index + 1
        segments.append(text[start:].strip())

        return segments
    
    def synthesize_audio(self, text, output_file):
        payload = {"text": text}
        with requests.post(self.DEEPGRAM_URL, stream=True, headers=self.headers, json=payload) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    output_file.write(chunk)
    
    def create_audio_file(self, input_text, output_file_path):
        segments = self.segment_text_by_sentence(input_text)
        
        # Create or truncate the output file
        with open(output_file_path, "wb") as output_file:
            for segment_text in segments:
                self.synthesize_audio(segment_text, output_file)
        
        print("Audio file creation completed.")

class DeepgramAudioIntelligence:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = DeepgramClient(api_key)
        
    def audio_intelligence(self, audio_file):
        try:
            with open(audio_file, "rb") as file:
                buffer_data = file.read()

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                sentiment=True,
                # intents=True,
                # summarize="v2",
                # topics=True,
            )

            response = self.client.listen.prerecorded.v("1").transcribe_file(payload, options)
            return response.to_json(indent=4)

        except Exception as e:
            return f"Exception: {e}"