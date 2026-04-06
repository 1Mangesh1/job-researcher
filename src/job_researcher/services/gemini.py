from google import genai
from google.genai import types


class GeminiService:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        response_schema: type | None = None,
        thinking_budget: int | None = None,
        use_google_search: bool = False,
        cached_content: str | None = None,
    ) -> str:
        config_kwargs: dict = {}

        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        if thinking_budget is not None:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=thinking_budget
            )

        if use_google_search:
            config_kwargs["tools"] = [
                types.Tool(google_search=types.GoogleSearch())
            ]

        if cached_content:
            config_kwargs["cached_content"] = cached_content

        config = types.GenerateContentConfig(**config_kwargs)

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        if response.usage_metadata:
            self.total_input_tokens += response.usage_metadata.prompt_token_count or 0
            self.total_output_tokens += response.usage_metadata.candidates_token_count or 0
        self.call_count += 1

        return response.text

    def get_usage(self) -> dict:
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
            "calls": self.call_count,
        }

    def estimated_cost(self) -> float:
        # Gemini 2.5 Flash pricing (approximate):
        # Input: $0.15/1M tokens, Output: $0.60/1M tokens
        input_cost = (self.total_input_tokens / 1_000_000) * 0.15
        output_cost = (self.total_output_tokens / 1_000_000) * 0.60
        return round(input_cost + output_cost, 6)

    async def create_cache(
        self, contents: list[str], display_name: str, ttl: str = "3600s"
    ) -> str:
        cache = self.client.caches.create(
            model=self.model,
            contents=contents,
            config=types.CreateCachedContentConfig(
                display_name=display_name,
                ttl=ttl,
            ),
        )
        return cache.name
