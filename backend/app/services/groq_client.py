import asyncio
import logging
from typing import Any
from groq import AsyncGroq, APITimeoutError, APIConnectionError
from app.config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    def __init__(self):
        self._client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=settings.groq_timeout,
        )
        self.model = settings.groq_model

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str | dict = "auto",
        response_format: dict | None = None,
        temperature: float = 0.1,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        if response_format:
            kwargs["response_format"] = response_format

        try:
            logger.debug("Calling Groq API model=%s", self.model)
            response = await asyncio.wait_for(
                self._client.chat.completions.create(**kwargs),
                timeout=settings.groq_timeout,
            )
            logger.debug("Groq response received finish_reason=%s", response.choices[0].finish_reason)
            return response
        except asyncio.TimeoutError:
            logger.warning("Groq API timed out after %ds", settings.groq_timeout)
            raise
        except APITimeoutError:
            logger.warning("Groq APITimeoutError")
            raise
        except APIConnectionError as e:
            logger.error("Groq connection error: %s", e)
            raise
        except Exception as e:
            logger.error("Groq unexpected error: %s", e)
            raise

    async def chat_json(
        self,
        messages: list[dict],
        temperature: float = 0.1,
    ) -> Any:
        return await self.chat(
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
        )


groq_client = GroqClient()
