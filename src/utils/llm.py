from groq import Groq

from config import settings
from utils.logging import logger


def get_llm_client():
    """Create a groq client"""
    client = Groq(api_key=settings.groq_api_key)
    return client

def test_llm_connection():
    logger.info("Testing connection to groq...")
    response = get_llm_client().chat.completions.create(
        model=settings.model_name,
        messages=[
        {
            "role": "system",
            "content": "Greet the user."
        },
        {
            "role": "user",
            "content": "Hi, I am Tushar"
        }
        ],
        temperature=1,
        max_completion_tokens=2048,
        top_p=1,
    )
    logger.info(response)