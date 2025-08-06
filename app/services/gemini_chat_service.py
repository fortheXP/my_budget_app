import google.generativeai as genai
import json
from sqlalchemy.orm import Session


class GeminiAIChatService:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def process_message_stream(self, message: str, user_id: int, db: Session):
        try:
            response = self.model.generate_content(contents=message)
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            print(e)
