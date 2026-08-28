from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


def get_tool_schema(
    func: Callable[..., Any], params_model: type[BaseModel] | None = None
):
    """Generate the json schema for the tool by extracting attributes from tool function and parameters model"""
    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": {},
        },
    }
    if params_model is not None:
        params_model_schema = params_model.model_json_schema()
        params_model_schema.pop("title")
        schema["function"]["parameters"] = params_model_schema
    return schema
