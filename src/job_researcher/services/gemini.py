from google import genai
from google.genai import types

# Gemini pricing per 1M tokens (input, output). Thinking counts as output.
MODEL_PRICING = {
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.15, 0.60),
    "gemini-2.5-flash-lite": (0.10, 0.40),
}


class GeminiService:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.usage_by_model: dict[str, dict[str, int]] = {}
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
        model: str | None = None,
    ) -> str:
        model_name = model or self.model
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
            model=model_name,
            contents=prompt,
            config=config,
        )

        if response.usage_metadata:
            bucket = self.usage_by_model.setdefault(
                model_name, {"input": 0, "output": 0}
            )
            bucket["input"] += response.usage_metadata.prompt_token_count or 0
            bucket["output"] += response.usage_metadata.candidates_token_count or 0
        self.call_count += 1

        return response.text

    def get_usage(self) -> dict:
        total_in = sum(b["input"] for b in self.usage_by_model.values())
        total_out = sum(b["output"] for b in self.usage_by_model.values())
        return {
            "input": total_in,
            "output": total_out,
            "calls": self.call_count,
            "by_model": self.usage_by_model,
        }

    def estimated_cost(self) -> float:
        total = 0.0
        for model_name, bucket in self.usage_by_model.items():
            in_rate, out_rate = MODEL_PRICING.get(
                model_name, MODEL_PRICING["gemini-2.5-flash"]
            )
            total += (bucket["input"] / 1_000_000) * in_rate
            total += (bucket["output"] / 1_000_000) * out_rate
        return round(total, 6)

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
