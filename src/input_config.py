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
    max_tokens: int = 1
    model_name: str = field(init=False)
    batch_token_limit: int = field(init=False)
    batch_requests_limit: int = field(init=False)
    use_dual_models: bool = False
    second_gpt_model: Optional[str] = None
    model_split_percentage: int = 50

    # Class-level constants
    MODEL_NAME_MAPPING = {
        "GPT-3.5": "gpt-3.5-turbo",
        "GPT-4o mini": "gpt-4o-mini",
        "GPT-4o": "gpt-4o",
    }
    
    MODEL_LIMITS = {
        "gpt-3.5-turbo": {"token_limit": 5000000, "requests_limit": 5000},
        "gpt-4o": {"token_limit": 1000000, "requests_limit": 5000},
        "gpt-4o-mini": {"token_limit": 5000000, "requests_limit": 5000},
    }

    def __post_init__(self):
        # Initialize first model
        self._update_model_config(self.gpt_model)
        
    def _update_model_config(self, model_choice: str):
        """Update model configuration based on selected model."""
        self.model_name = self.MODEL_NAME_MAPPING[model_choice]
        limits = self.MODEL_LIMITS[self.model_name]
        self.batch_token_limit = limits["token_limit"]
        self.batch_requests_limit = limits["requests_limit"]

    def prepare_second_model(self):
        """Configure for second model when doing dual analysis."""
        if self.use_dual_models and self.second_gpt_model:
            self._update_model_config(self.second_gpt_model.strip())


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
