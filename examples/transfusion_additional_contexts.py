

import re
from typing import List, Optional
from schemas import OpenAIChatMessage
from pydantic import BaseModel
import requests
import os
import time
import asyncio
from functools import lru_cache
from chromadb.config import Settings
import chromadb
import chromadb.utils.embedding_functions as embedding_functions

from utils.pipelines.main import get_last_user_message, get_last_assistant_message


# Created by ABC
class Pipeline:
    collection = None

    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0
        OPENAI_API_KEY: str
        VECTORDB_HOST: str
        VECTORDB_PORT: int

    def __init__(self):
        print(f"Initializing {__name__}...")
        self.type = "filter"
        self.name = "Transfusion Additional Contexts"

        # Initialize
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],  # Connect to all pipelines
                "OPENAI_API_KEY": os.getenv(
                    "OPENAI_API_KEY", "your_API_key_here"
                ),
                "VECTORDB_HOST": os.getenv(
                    "VECTORDB_HOST", "localhost"
                ),
                "VECTORDB_PORT": os.getenv(
                    "VECTORDB_PORT", 3600
                )
            }
        )

        print(f"Valves: {self.valves.dict()}")

        # Initialize translation cache
        self.translation_cache = {}

        self.client = chromadb.HttpClient(host=self.valves.VECTORDB_HOST, port=self.valves.VECTORDB_PORT, settings=Settings())
        print(f"Chroma client: {self.client.list_collections()}")



    async def on_startup(self):
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        pass

    async def on_valves_updated(self):
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"inlet:{__name__}")

        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.valves.OPENAI_API_KEY,
            model_name="text-embedding-3-large"
        )
        print(f"Embedding function: {embedding_function}")
        self.collection = self.client.get_collection(name="transfusion_cosine",
                                                     embedding_function=embedding_function)

        messages = body["messages"]
        user_message = f"{get_last_user_message(messages)}\n\n"

        print(f"User message: {user_message}")

        try:

            results = self.collection.query(
                query_texts=[user_message],
                n_results=2
            )

            database_responses = [
                {
                    "title": f"Document from {meta['source']} (Page {meta['page']})",
                    "summary": doc
                }
                for meta, doc in zip(results['metadatas'][0], results['documents'][0])
            ]

            for i, response in enumerate(database_responses, 1):
                user_message += f"{i}. **Response {i}**:\n   - **Summary**: {response['summary']}\n\n"

            user_message += "Can you provide an analysis based on these responses and any additional information you may have?"

            print(f"User message with database responses: {user_message}")

            for message in reversed(messages):
                if message["role"] == "user":
                    message["content"] = user_message
                    break

            body = {**body, "messages": messages}
            return body
        except Exception as e:
            print(f"Error: {e}")
            return e