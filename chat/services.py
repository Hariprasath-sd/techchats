import openai
from django.conf import settings
from rag_system.services import RAGService

class ChatService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def generate_response(self, user_input, conversation_history=None):
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg.is_user else "assistant"
                messages.append({"role": role, "content": msg.content})
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

    def generate_rag_response(self, query, collection_id, user):
        rag_service = RAGService()
        return rag_service.query_documents(query, collection_id, user)