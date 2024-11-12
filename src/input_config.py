from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SentimentAnalysisConfig:
    input_file: str
    output_file: str
    customization_option: str
    company_entry: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    user_prompt2: Optional[str] = None
    gpt_model: str = "GPT-4o mini"
    update_brandwatch: bool = False
    output_probabilities: bool = False
    company_column: Optional[str] = None
    multi_company_entry: Optional[str] = None
    separate_company_analysis: bool = False
    temperature: float = 0.3
    model_name: str = field(init=False)
    batch_token_limit: int = field(init=False)
    batch_requests_limit: int = field(init=False)


class ConfigManager:
    def __init__(self):
        self.sentiment_config: Optional[SentimentAnalysisConfig] = None

    def update_sentiment_config(self, **kwargs):
        self.sentiment_config = SentimentAnalysisConfig(**kwargs)
        self._select_model()
        self._set_prompts()

    def _select_model(self):
        if self.sentiment_config is None:
            return

        model_name_mapping = {
            "GPT-3.5": "gpt-3.5-turbo",
            "GPT-4o mini": "gpt-4o-mini",
            "GPT-4o": "gpt-4o",
        }
        model_limits = {
            "gpt-3.5-turbo": {"token_limit": 5000000, "requests_limit": 5000},
            "gpt-4o": {"token_limit": 1000000, "requests_limit": 5000},
            "gpt-4o-mini": {"token_limit": 5000000, "requests_limit": 5000},
        }
        self.sentiment_config.model_name = model_name_mapping[
            self.sentiment_config.gpt_model
        ]
        self.sentiment_config.batch_token_limit = model_limits[
            self.sentiment_config.model_name
        ]["token_limit"]
        self.sentiment_config.batch_requests_limit = model_limits[
            self.sentiment_config.model_name
        ]["requests_limit"]

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
