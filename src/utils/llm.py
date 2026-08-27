import groq

from config import settings
from utils.logging import logger


def get_llm_client():
    """Create an async groq client"""
    client = groq.AsyncGroq(api_key=settings.groq_api_key)
    return client

async def test_llm_connection():
    logger.info("Testing connection to groq...")
    client = get_llm_client()
    try:
        response = await client.chat.completions.create(
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
    except groq.APIConnectionError as e:
        logger.error(f"The server could not be reached : {e}")
        # an underlying Exception, likely raised within httpx.
    except groq.RateLimitError as e:
        logger.error(f"A 429 status code was received; we should back off a bit : {e}")
    except groq.APIStatusError as e:
        logger.error(f"Another non-200-range status code was received : {e}")
        logger.error(f"Status code : {e.status_code}")
        logger.error(f"Response : {e.response}")