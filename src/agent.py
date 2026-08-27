from groq.types.chat.chat_completion import ChatCompletion

from config import settings
from tools import TOOL_PARAMS_CLS, TOOL_SCHEMAS, TOOLS
from utils.json import dumps as json_dumps
from utils.json import loads as json_loads
from utils.llm import get_llm_client
from utils.logging import logger

SYSTEM_PROMPT = """You are a SQL agent that answers questions about a PostgreSQL database.
The database contains TPC-H benchmark data.
Use the available tools to discover the schema and run queries to answer the user's question.
Format your final answer as a clear, human-readable response."""


async def run_agent(user_question: str) -> str:
    """Run the sql agent with user question"""
    logger.info(f"User question: {user_question}")
    logger.info("-" * 50)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_question},
    ]

    for i in range(settings.max_agent_iterations):
        # send complete converstion to groq with available tools
        logger.info(f"Iteration {i}/{settings.max_agent_iterations}")
        llm_client = get_llm_client()
        response: ChatCompletion = await llm_client.chat.completions.create(
            model=settings.model_name,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json_loads(tool_call.function.arguments)
                logger.info(f"Tool : {tool_name}({tool_args if tool_args else ''})")

                if tool_name not in TOOLS:
                    result = {"error": f"Unknown tool : {tool_name}"}
                else:
                    tool_func = TOOLS[tool_name]
                    if tool_args:
                        # tool with parameters
                        result = await tool_func(
                            TOOL_PARAMS_CLS[tool_name](**tool_args)
                        )
                    else:
                        # tool without parameters
                        result = await tool_func()

                logger.info(f"Intermediate result: {result[:200]}")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json_dumps(result),
                    }
                )
        else:
            logger.info(f"Result: {message.content}")
            logger.info(f"Reached conclusion in {i + 1} iterations")
            return message.content

    logger.warning(f"Could not reach conclusion in {i + 1} iterations")
