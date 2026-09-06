import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class CodeAssistant:

    def __init__(self):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=api_key,
            temperature=0
        )

    def _content_to_text(self, content):
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []

            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

            return "\n\n".join(part for part in text_parts if part).strip()

        return str(content)

    def generate_answer(self, query, documents):

        context = "\n\n".join(
            document.page_content
            for document in documents
        )

        prompt = f"""
            You are an AI coding assistant.

            Use the following repository code to answer the user's question.

            Repository context:
            {context}

            User question:
            {query}

            Instructions:
            - Answer based on the provided code.
            - Do not invent functionality.
            - Mention relevant files or functions when useful.
            - If the context is insufficient, say so.
        """

        response = self.llm.invoke(prompt)

        return self._content_to_text(response.content)
