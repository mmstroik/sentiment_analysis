import asyncio
from aiohttp import ClientSession

import tiktoken

from .sa_secrets.keys import GEMINI_API_KEY
from .DS_Tokenizer.deepseek_v2_tokenizer import init_ds_tokenizer

GEMINI_TOKEN_COUNT_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:countTokens"

async def calculate_token_count(config, df, log_message):
    log_message("Calculating token counts for each mention...")
    
    # Find and drop rows where 'Full Text' is not a string or is empty
    invalid_rows = df[
        ~df["Full Text"].apply(lambda x: isinstance(x, str) and x.strip() != "")
    ].index
    df.drop(invalid_rows, inplace=True)
    
    full_user_prompt = f'{config.user_prompt} ""\n{config.user_prompt2}'
    
    # Centralize system prompt creation
    if config.customization_option == "Multi-Company":
        longest_company_name = df["AnalyzedCompany"].max()
        system_with_prompt = config.system_prompt.format(
            toward_company=f" toward {longest_company_name}"
        ) + full_user_prompt
    else:
        system_with_prompt = config.system_prompt + full_user_prompt

    if config.model_name.startswith('gemini'):
        # gemini token counting
        async with ClientSession() as session:
            prompt_token_count = await get_gemini_token_count(
                config, system_with_prompt, session
            )

            tasks = [
                get_gemini_token_count(config, tweet, session)
                for tweet in df["Full Text"]
            ]
            
            token_counts = await asyncio.gather(*tasks)
            df["Token Count"] = [count + prompt_token_count + 2 for count in token_counts]

    elif config.model_name.startswith('gpt'):
        # openai token counting
        gpt_tokenizer = tiktoken.encoding_for_model(config.model_name)
        prompt_token_count = len(gpt_tokenizer.encode(system_with_prompt))

        df["Token Count"] = df["Full Text"].apply(
            lambda tweet: len(gpt_tokenizer.encode(tweet, allowed_special={"<|endoftext|>"}))
            + prompt_token_count
            + 2
        )
    elif config.model_name.startswith('deepseek'):
        # deepseek token counting (for when we add a deepseek model)
        ds_tokenizer = init_ds_tokenizer()
        prompt_token_count = len(ds_tokenizer.encode(system_with_prompt))

        df["Token Count"] = df["Full Text"].apply(
            lambda tweet: len(ds_tokenizer.encode(tweet))
            + prompt_token_count
            + 2
        )
    else:
        raise ValueError(f"Unsupported model: {config.model_name}")


async def get_gemini_token_count(config, text, session):
    url = GEMINI_TOKEN_COUNT_API_ENDPOINT.format(model=config.model_name)
    params = {"key": GEMINI_API_KEY}
    
    payload = {
        "contents": [{
            "parts": [{"text": text}]
        }]
    }
    
    async with session.post(url, json=payload, params=params) as response:
        if response.status == 200:
            result = await response.json()
            return result["totalTokens"]
        raise Exception(f"Failed to get token count from Gemini API. Status code: {response.status}")
