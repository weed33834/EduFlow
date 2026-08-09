from openai import AsyncOpenAI
from core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

async def chat_completion(messages: list[dict], system_prompt: str = "", temperature: float = None) -> str:
    if not client:
        return "AI service not configured. Please set OPENAI_API_KEY."
    
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)
    
    resp = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=temperature or settings.LLM_TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
    )
    return resp.choices[0].message.content

async def stream_chat(messages: list[dict], system_prompt: str = ""):
    if not client:
        yield "AI service not configured."
        return
    
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)
    
    stream = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=full_messages,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
        stream=True,
    )
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content