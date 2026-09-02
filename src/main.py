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
    # user_question = "In how many regions do we operate?"
    # user_question = "In how many countries do we operate?"
    # user_question = "Which country has brought maximum revenue?"
    # user_question = (
    #     "What are the top 5 nations by total revenue? explain the query as well"
    # )
    user_question = "How many total customers vs active customers do we have?"
    # user_question = "Create a new region South-east Asia"
    # user_question = "Show me parts with a supply cost over 900 from European suppliers"
    response = await run_agent(user_question)
    logger.info("-" * 50)
    logger.info(f"USER QUESTION: {user_question}")
    logger.info(f"AGENT RESPONSE: {response}")
    logger.info("=" * 50)

    # qry = "SELECT * FROM orders Join customers ON orders.custkey = customers.custkey limit 10"
    # qry = "select * from orders where (Delete FROM orders) is True"
    # qry = """
    # WITH customer AS (
    #     DELETE FROM orders WHERE id = 1 RETURNING *
    # )
    # SELECT * FROM customer
    # """  # disguised delete query via cte, validator failed to catch
    # qry = "SElect * from orders; delete from orders"
    # qry = "SElect * from orders; select * from orders"
    # qry = "select * from (update orders set o_orderkeys = '1')"
    # validation_result = await validate_query(ValidateQueryParams(sql=qry))
    # logger.info(f"Validation result for query '{qry}': {validation_result}")

    # shutdown
    await Database.disconnect()
    logger.debug("Shutting down")


if __name__ == "__main__":
    asyncio.run(main())
