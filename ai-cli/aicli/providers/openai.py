"""OpenAI provider implementation."""

from __future__ import annotations

from collections.abc import Mapping

import httpx

from aicli.core.settings import Settings
from aicli.providers.base import BaseProvider
from aicli.providers.exceptions import (
    ProviderAuthenticationError,
    ProviderRequestError,
)


class OpenAIProvider(BaseProvider):
    """OpenAI Responses API provider."""

    def __init__(
        self,
        *,
        model: str,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(model=model, settings=settings)
        self._client = client

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        normalized_prompt = self._validate_prompt(prompt)
        api_key = self._require_api_key(self.settings.openai_api_key, "OPENAI_API_KEY")

        payload: dict[str, object] = {
            "model": self.model,
            "input": self._build_messages(normalized_prompt, system_prompt),
            "temperature": temperature,
        }

        client = self._client or httpx.AsyncClient(timeout=self.settings.provider_timeout_seconds)
        should_close_client = self._client is None

        try:
            response = await client.post(
                f"{self.settings.openai_base_url.rstrip('/')}/responses",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code in {401, 403}:
                msg = f"OpenAI authentication failed with status {status_code}."
                raise ProviderAuthenticationError(msg) from exc
            msg = f"OpenAI request failed with status {status_code}: {exc.response.text}"
            raise ProviderRequestError(msg) from exc
        except httpx.HTTPError as exc:
            msg = f"OpenAI request failed: {exc}"
            raise ProviderRequestError(msg) from exc
        finally:
            if should_close_client:
                await client.aclose()

        payload_data: object = response.json()
        if not isinstance(payload_data, Mapping):
            msg = "OpenAI response was not a JSON object."
            raise ProviderRequestError(msg)
        return self._extract_response_text(payload_data)

    def _build_messages(
        self,
        prompt: str,
        system_prompt: str | None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _extract_response_text(self, payload: Mapping[str, object]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = payload.get("output")
        if isinstance(output, list):
            parts: list[str] = []
            for item in output:
                if not isinstance(item, Mapping):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for content_item in content:
                    if not isinstance(content_item, Mapping):
                        continue
                    text = content_item.get("text")
                    if isinstance(text, str):
                        parts.append(text)

            response_text = "".join(parts).strip()
            if response_text:
                return response_text

        msg = "OpenAI response did not include text output."
        raise ProviderRequestError(msg)
