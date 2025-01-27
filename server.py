from typing import Any
from mcp.server.fastmcp import FastMCP
import httpx
import os
import json


# load_dotenv()

DEEPSEEK_API_KEY = "enter your api key"
DEEPSEEK_API_BASE = "https://api.deepseek.com"

mcp = FastMCP("deepseek-reasoner-claude")


async def get_deepseek_reasoning(query: str) -> str:
    """
    Get reasoning from the DeepSeek API.

    Args:
        query (str): The input query to process.

    Returns:
        str: The reasoning output from the API.
    """
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        }

        payload_body = {
            "model": "deepseek-reasoner",
            "messages": [{"role": "user", "content": query}],
            "streaming": True,
            "max_tokens": 2048,
        }

        async with client.stream(
            "POST",
            f"{DEEPSEEK_API_BASE}/chat/completions",
            headers=headers,
            json=payload_body,
        ) as response:
            reasoning_data = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "DONE":
                        continue
                    try:
                        chunk_data = json.loads(data)
                        if content := chunk_data.get("choices", [{}])[0].get("delta", {}).get("reasoning_content", ""):
                            reasoning_data.append(content)
                    except json.JSONDecodeError:
                        continue

            return " ".join(reasoning_data)


@mcp.tool()
async def reason(query: dict) -> str:
    """
    Process a query using DeepSeek's R1 reasoning engine and prepare it for integration with Claude.

    DeepSeek R1 leverages advanced reasoning capabilities that naturally evolved from large-scale 
    reinforcement learning, enabling sophisticated reasoning behaviors. The output is enclosed 
    within `<ant_thinking>` tags to align with Claude's thought processing framework.

    Args:
        query (dict): Contains the following keys:
            - context (str): Optional background information for the query.
            - question (str): The specific question to be analyzed.

    Returns:
        str: The reasoning output from DeepSeek, formatted with `<ant_thinking>` tags for seamless use with Claude.
    """
    try:
        # Format the query from the input
        context = query.get("context", "")
        question = query.get("question", "")
        full_query = f"{context}\n{question}" if context else question

        reasoning = await get_deepseek_reasoning(full_query)

        return f"<ant_thinking>\n{reasoning}\n</ant_thinking>\n\nNow we should provide our final answer based on the above thinking."
    except Exception as e:
        return f"<reasoning_error>\nError: {str(e)}\n</reasoning_error>\n\nExplain the error."


if __name__ == "__main__":
    mcp.run(transport="stdio")
