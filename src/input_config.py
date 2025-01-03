from dataclasses import dataclass, field
from typing import Optional
import os
import aiohttp
import asyncio

from .sa_secrets.keys import OPENAI_ADMIN_KEY


@dataclass
class SentimentAnalysisConfig:
    input_file: str
    output_file: str
    customization_option: str
    company_entry: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    user_prompt2: Optional[str] = None
    model_display_name: str = "GPT-4o mini"
    update_brandwatch: bool = False
    output_probabilities: bool = False
    company_column: Optional[str] = None
    multi_company_entry: Optional[str] = None
    separate_company_analysis: bool = False
    temperature: float = 0.3
    max_tokens: int = 1
    model_name: str = field(init=False)
    batch_token_limit: int = field(init=False)
    batch_requests_limit: int = field(init=False)
    use_dual_models: bool = False
    second_model_display_name: Optional[str] = None
    model_split_percentage: int = 50

    # Class-level constants
    MODEL_NAME_MAPPING = {
        "GPT-3.5": "gpt-3.5-turbo",
        "GPT-4o mini": "gpt-4o-mini",
        "GPT-4o": "gpt-4o",
        "Gemini 1.5 Flash": "gemini-1.5-flash",
        "Gemini 1.5 Pro": "gemini-1.5-pro",
        "DeepSeek-V3": "deepseek-chat",
    }

    MODEL_LIMITS = {}  # Will be populated during initialization

    # Default fallback limits (in case API call fails)
    DEFAULT_LIMITS = {
        "gpt-3.5-turbo": {"token_limit": 5000000, "requests_limit": 5000},
        "gpt-4o": {"token_limit": 1000000, "requests_limit": 5000},
        "gpt-4o-mini": {"token_limit": 5000000, "requests_limit": 5000},
        "gemini-1.5-flash": {"token_limit": 2000000, "requests_limit": 1000},
        "gemini-1.5-pro": {"token_limit": 2000000, "requests_limit": 500},
        "deepseek-chat": {"token_limit": 10000000, "requests_limit": 10000},
    }

    def __post_init__(self):
        # Initialize MODEL_LIMITS if empty
        if not self.MODEL_LIMITS:
            # Try to fetch dynamic limits
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            raw_limits = loop.run_until_complete(self.fetch_openai_rate_limits())
            loop.close()

            # Update MODEL_LIMITS with fetched values or defaults
            self.MODEL_LIMITS = self.DEFAULT_LIMITS.copy()
            if raw_limits:
                # Update only OpenAI models we use with fetched limits
                for model_display, model_api in self.MODEL_NAME_MAPPING.items():
                    if model_api in raw_limits:
                        self.MODEL_LIMITS[model_api] = {
                            "token_limit": raw_limits[model_api][
                                "max_tokens_per_1_minute"
                            ]
                            // 2,
                            "requests_limit": raw_limits[model_api][
                                "max_requests_per_1_minute"
                            ]
                            // 2,
                        }

        # Initialize first model
        self._update_model_config(self.model_display_name)

    def _update_model_config(self, model_choice: str):
        """Update model configuration based on selected model."""
        self.model_name = self.MODEL_NAME_MAPPING[model_choice]
        limits = self.MODEL_LIMITS[self.model_name]
        self.batch_token_limit = limits["token_limit"]
        self.batch_requests_limit = limits["requests_limit"]

    def prepare_second_model(self):
        """Configure for second model when doing dual analysis."""
        if self.use_dual_models and self.second_model_display_name:
            self._update_model_config(self.second_model_display_name.strip())

    @staticmethod
    async def fetch_openai_rate_limits():
        """Fetch current rate limits from OpenAI API."""
        api_key = OPENAI_ADMIN_KEY
        if not api_key:
            return None

        async with aiohttp.ClientSession() as session:
            url = "https://api.openai.com/v1/organization/rate_limits"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {item["model"]: item for item in data["data"]}
            except Exception as e:
                print(f"Error fetching rate limits: {e}")
                return None


class ConfigManager:
    def __init__(self):
        self.sentiment_config: Optional[SentimentAnalysisConfig] = None

    def update_sentiment_config(self, **kwargs):
        self.sentiment_config = SentimentAnalysisConfig(**kwargs)
        self._set_prompts()

    def _set_prompts(self):
        if self.sentiment_config.customization_option == "Default":
            self.sentiment_config.system_prompt = "Classify the sentiment of the following Text in one word from this list [Positive, Neutral, Negative]."
            self.sentiment_config.user_prompt = "Text:"
            self.sentiment_config.user_prompt2 = "Sentiment:"
        elif self.sentiment_config.customization_option == "Company":
            company = self.sentiment_config.company_entry
            self.sentiment_config.system_prompt = f"Classify the sentiment of the following Text toward {company} in one word from this list [Positive, Neutral, Negative]."
            self.sentiment_config.user_prompt = "Text:"
            self.sentiment_config.user_prompt2 = "Sentiment:"
        elif self.sentiment_config.customization_option == "Multi-Company":
            # Placeholder for company name (uses .format to replace bracketed text via string matching)
            self.sentiment_config.system_prompt = "Classify the sentiment of the following Text{toward_company} in one word from this list [Positive, Neutral, Negative]."
            self.sentiment_config.user_prompt = "Text:"
            self.sentiment_config.user_prompt2 = "Sentiment:"
        elif self.sentiment_config.customization_option == "Custom":
            self.sentiment_config.system_prompt = (
                self.sentiment_config.system_prompt.strip()
            )
            self.sentiment_config.user_prompt = (
                self.sentiment_config.user_prompt.strip()
            )
            self.sentiment_config.user_prompt2 = (
                self.sentiment_config.user_prompt2.strip()
            )
