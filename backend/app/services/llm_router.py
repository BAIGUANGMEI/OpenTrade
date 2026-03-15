from __future__ import annotations

import json

import httpx
from openai import APIError, AsyncOpenAI

from app.core.security import cipher
from app.models.model_config import ModelConfig


class LlmRouter:
    async def run_completion(self, config: ModelConfig, messages: list[dict]) -> str:
        provider = (config.provider or "openai").lower()
        api_key = cipher.decrypt(config.api_key_encrypted)
        if not api_key:
            raise ValueError(f"Missing API key for model '{config.name}'")

        timeout = httpx.Timeout(config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if provider == "anthropic":
                return await self._call_anthropic(client, config, api_key, messages)
        return await self._call_openai_compatible(config, api_key, messages)

    async def _call_openai_compatible(
        self,
        config: ModelConfig,
        api_key: str,
        messages: list[dict],
    ) -> str:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=str(config.base_url).rstrip("/"),
            timeout=config.timeout_seconds,
        )
        try:
            response = await client.chat.completions.create(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                response_format={"type": "json_object"},
                messages=messages,
            )
        except APIError as exc:
            raise RuntimeError(f"OpenAI-compatible provider error: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("OpenAI-compatible provider returned empty content")
        return content

    async def _call_anthropic(
        self,
        client: httpx.AsyncClient,
        config: ModelConfig,
        api_key: str,
        messages: list[dict],
    ) -> str:
        system_message = next((item["content"] for item in messages if item["role"] == "system"), "")
        user_message = next((item["content"] for item in messages if item["role"] == "user"), "")
        payload = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "system": system_message,
            "messages": [{"role": "user", "content": user_message}],
        }
        url = str(config.base_url).rstrip("/")
        response = await client.post(
            url,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        text_chunks = [item.get("text", "") for item in data.get("content", []) if item.get("type") == "text"]
        return "\n".join(text_chunks)

    @staticmethod
    def parse_json_response(raw_response: str) -> dict:
        content = raw_response.strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        return json.loads(content)


llm_router = LlmRouter()
