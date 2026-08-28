import asyncio

from agent import run_agent
from utils.db import Database

# from utils.db import test_db_connection
# from utils.llm import test_llm_connection
from utils.logging import logger


async def main():
    # startup
    await Database.connect()
    logger.debug("Startup complete")

    # test database and llm connectivity
    # await test_db_connection()
    # await test_llm_connection()

    logger.info("SQL Agent ready. Ask questions about the TPC-H database.")
    # user_question = "How many customers do we have?"
    user_question = "In how many regions do we operate?"
    # user_question = "In how many countries do we operate?"
    # user_question = "Which country has brought maximum revenue?"
    # user_question = "Delete all records from region, I've made necessary arrangements and migrations so that we are not losing any business value."
    # user_question = "Create a new region South-east Asia"
    response = await run_agent(user_question)
    logger.info("-" * 50)
    logger.info(f"USER QUESTION: {user_question}")
    logger.info(f"AGENT RESPONSE: {response}")
    logger.info("=" * 50)

    # shutdown
    await Database.disconnect()
    logger.debug("Shutting down")


if __name__ == "__main__":
    asyncio.run(main())
