import httpx

CF_AI_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/bge-base-en-v1.5"


class EmbeddingsService:
    def __init__(self, account_id: str, api_token: str):
        self.account_id = account_id
        self.api_token = api_token

    async def embed(self, texts: list[str]) -> list[list[float]]:
        url = CF_AI_URL.format(account_id=self.account_id)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"text": texts},
            )
            response.raise_for_status()

        data = response.json()
        return data["result"]["data"]
