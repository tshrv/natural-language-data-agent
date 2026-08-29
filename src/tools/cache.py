from utils.logging import logger


def tool_key_builder(func, *args, **kwargs) -> str:
    """Build a key for the tool"""
    # expect args and kwargs all being pydantic models
    args_key = ":".join([arg.model_dump_json() for arg in args])
    kwargs_key = ":".join([arg.model_dump_json() for arg in kwargs.values()])
    key = f"{func.__name__}::{args_key}::{kwargs_key}"
    logger.debug(f"Building cache key {key}")
    return key
