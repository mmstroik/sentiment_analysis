from typing import Tuple, Optional

from .sa_secrets.keys import DEEPSEEK_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY

OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
GEMINI_API_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
DEEPSEEK_API_ENDPOINT = "https://api.deepseek.com/chat/completions"

# Model-specific adapters
def create_openai_payload(config, system_prompt: str, tweet: str) -> dict:
    return {
        "model": config.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'{config.user_prompt} "{tweet}"\n{config.user_prompt2}'},
        ],
        "temperature": config.temperature,
        "max_completion_tokens": config.max_tokens,
        "logprobs": config.output_probabilities,
        "store": True,
    }

def create_gemini_payload(config, system_prompt: str, tweet: str) -> dict:
    return {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": f'{config.user_prompt} "{tweet}"\n{config.user_prompt2}'}]}],
        "generationConfig": {
            "temperature": config.temperature,
            "maxOutputTokens": config.max_tokens,
            "responseLogprobs": config.output_probabilities,
        },
    }

def create_deepseek_payload(config, system_prompt: str, tweet: str) -> dict:
    return {
        "model": config.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'{config.user_prompt} "{tweet}"\n{config.user_prompt2}'},
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens + 1, # "Neutral" requires 2 tokens
        "logprobs": config.output_probabilities,
    }

def parse_openai_response(response_json: dict) -> Tuple[str, Optional[float]]:
    sentiment = response_json["choices"][0]["message"]["content"].strip()
    logprob = None
    if (logprobs := response_json["choices"][0].get("logprobs")) and logprobs.get("content"):
        logprob = logprobs["content"][0]["logprob"]
    return sentiment, logprob

def parse_gemini_response(response_json: dict) -> Tuple[str, Optional[float]]:
    sentiment = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    logprob = None
    if (logprobs_result := response_json["candidates"][0].get("logprobsResult")):
        if (chosen_candidates := logprobs_result.get("chosenCandidates")):
            logprob = chosen_candidates[0].get("logProbability")
    return sentiment, logprob

def parse_deepseek_response(response_json: dict) -> Tuple[str, Optional[float]]:
    sentiment = response_json["choices"][0]["message"]["content"].strip()
    logprob = None
    if (logprobs := response_json["choices"][0].get("logprobs")) and logprobs.get("content"):
        logprob = logprobs["content"][0]["logprob"]
    return sentiment, logprob

# Model configuration factory
def get_model_config(model_name: str) -> dict:
    if model_name.startswith("gpt"):
        return {
            "api_endpoint": OPENAI_API_ENDPOINT,
            "create_payload": create_openai_payload,
            "parse_response": parse_openai_response,
            "headers": {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            "params": None
        }
    elif model_name.startswith("gemini"):
        return {
            "api_endpoint": GEMINI_API_ENDPOINT.format(model=model_name),
            "create_payload": create_gemini_payload,
            "parse_response": parse_gemini_response,
            "headers": {"Content-Type": "application/json"},
            "params": {"key": GEMINI_API_KEY}
        }
    elif model_name.startswith("deepseek"):
        return {
            "api_endpoint": DEEPSEEK_API_ENDPOINT,
            "create_payload": create_deepseek_payload,
            "parse_response": parse_deepseek_response,
            "headers": {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            "params": None
        }
    raise ValueError(f"Unsupported model: {model_name}")