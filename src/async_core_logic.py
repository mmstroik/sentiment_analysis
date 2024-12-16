import asyncio
import math
import time

import pandas as pd
from aiohttp import ClientSession

import tiktoken

from .sa_secrets.keys import OPENAI_API_KEY, GEMINI_API_KEY

RATE_LIMIT_DELAY = 30  # seconds

OPENAI_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Asynchronously processes tweets in batches (based on token counts)
async def batch_processing_handler(
    config,
    df,
    update_progress_gui,
    log_message,
):
    calculate_token_count(config, df, log_message)

    progress_scale = 60 if config.update_brandwatch else 90
    
    async with ClientSession() as session:
        update_progress_gui(5)  # initial progress for progress bar
        start_time = await process_batches(
            config,
            df,
            df,
            update_progress_gui,
            log_message,
            session,
            is_reprocessing=False,
            progress_scale=progress_scale,
        )

        # Reprocess errored tweets
        errored_df = df[df["Sentiment"].isin(["Error", ""])]
        if not errored_df.empty:
            log_message(
                f"Waiting for rate limit timer before reprocessing {len(errored_df)} errored mentions..."
            )
            await asyncio.sleep(RATE_LIMIT_DELAY + 5)
            start_time = await process_batches(
                config,
                df,
                errored_df,
                update_progress_gui,
                log_message,
                session,
                is_reprocessing=True,
                progress_scale=progress_scale,
            )

            # Check for remaining errors
            errored_df = df[df["Sentiment"].isin(["Error", ""])]
            if not errored_df.empty:
                log_message(
                    f"Still error processing {len(errored_df)} mentions. Contact Milo if persistent."
                )
    return df, start_time


async def process_batches(
    config,
    df,
    working_df,
    update_progress_gui,
    log_message,
    session,
    is_reprocessing=False,
    progress_scale=60,
):
    total = len(working_df)
    processed = 0
    start_idx = 0

    while start_idx < len(working_df):
        batch_end_idx = calculate_batch_size(
            working_df, config.batch_token_limit, config.batch_requests_limit, start_idx
        )
        
        # Different message based on processing type
        if is_reprocessing:
            log_message(
                f"Reprocessing batch {start_idx+1}-{batch_end_idx} of {total} errored mentions..."
            )
        else:
            log_message(
                f"Processing batch {start_idx+1}-{batch_end_idx} of {total} mentions..."
            )

        batch = working_df.iloc[start_idx:batch_end_idx]

        if config.model_name.startswith('gemini'):
            async_func = call_gemini_async
        else:
            async_func = call_openai_async

        if config.customization_option == "Multi-Company":
            tasks = [
                (i, async_func(config, session, tweet, company))
                for i, (tweet, company) in enumerate(zip(batch["Full Text"], batch["AnalyzedCompany"]))
            ]
        else:
            tasks = [
                (i, async_func(config, session, tweet))
                for i, tweet in enumerate(batch["Full Text"])
            ]

        # Create tasks and track their futures
        futures_map = {}
        batch_results = [None] * len(tasks)
        
        for idx, coro in tasks:
            future = asyncio.create_task(coro)
            futures_map[future] = idx
            
        # Process results as they complete
        pending = set(futures_map.keys())
        while pending:
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            
            for future in done:
                idx = futures_map[future]
                try:
                    result = await future
                    batch_results[idx] = result
                except Exception as e:
                    batch_results[idx] = e
                
                processed += 1
                progress = (processed / total) * progress_scale 
                update_progress_gui(progress + 5)  # +5 from initial setup

        timer = asyncio.create_task(asyncio.sleep(RATE_LIMIT_DELAY))
        start_time = time.time()

        handle_batch_results(config, df, log_message, batch, batch_results)

        # Different progress message based on processing type
        if is_reprocessing:
            log_message(f"Reprocessed {processed} of {total} errored mentions.")
        else:
            log_message(f"Progress: Processed {processed} of {total} mentions.")

        start_idx = batch_end_idx

        if start_idx < len(working_df):
            log_message(f"Waiting {str(RATE_LIMIT_DELAY)} secs for rate limit timer...")
            await timer

    return start_time


# Asynchronously calls the API for each tweet in the batch
async def call_openai_async(
    config,
    session: ClientSession,
    tweet: str,
    company: str = None,
    max_retries=6,
):
    if config.customization_option == "Multi-Company":
        toward_company = f" toward {company}" if company else ""
        system_prompt = config.system_prompt.format(toward_company=toward_company)
    else:
        system_prompt = config.system_prompt

    payload = {
        "model": config.model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f'{config.user_prompt} "{tweet}"\n{config.user_prompt2}',
            },
        ],
        "temperature": config.temperature,
        "max_completion_tokens": config.max_tokens,
        "logprobs": config.output_probabilities,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    retry_delay = 1
    for attempt in range(max_retries):
        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    sentiment = result["choices"][0]["message"]["content"]
                    if config.output_probabilities:
                        logprob = result["choices"][0]["logprobs"]["content"][0][
                            "logprob"
                        ]
                        return sentiment.strip(), logprob
                    else:
                        return sentiment.strip()
                elif attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)  # Wait before retrying
                    retry_delay += 2
                else:
                    result = await response.text()
                    return "Error"
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)  # Wait before retrying
                retry_delay += 2
            else:
                return "Error"

async def call_gemini_async(
    config,
    session: ClientSession,
    tweet: str,
    company: str = None,
    max_retries=6,
):
    if config.customization_option == "Multi-Company":
        toward_company = f" toward {company}" if company else ""
        system_prompt = config.system_prompt.format(toward_company=toward_company)
    else:
        system_prompt = config.system_prompt

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [{
            "parts": [{"text": f'{config.user_prompt} "{tweet}"\n{config.user_prompt2}'}]
        }],
        "generationConfig": {
            "temperature": config.temperature,
            "maxOutputTokens": config.max_tokens,
            "responseLogprobs": config.output_probabilities,
        }
    }

    url = GEMINI_API_ENDPOINT.format(model=config.model_name)
    headers = {
        "Content-Type": "application/json",
    }

    params = {"key": GEMINI_API_KEY}

    retry_delay = 1
    for attempt in range(max_retries):
        try:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                params=params,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    sentiment = result["candidates"][0]["content"]["parts"][0]["text"]
                    
                    if config.output_probabilities:
                        # Get first token's logprob from logprobsResult
                        logprob = result["candidates"][0]["logprobsResult"]["chosenCandidates"][0]["logProbability"]
                        return sentiment.strip(), logprob
                    else:
                        return sentiment.strip()
                elif attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay += 2
                else:
                    result = await response.text()
                    return "Error"
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay += 2
            else:
                return "Error"

def handle_batch_results(config, df, log_message, batch, results):
    for tweet_idx, result in zip(batch.index, results):
        if isinstance(result, Exception):
            log_message(f"Error processing text at row {tweet_idx}: {result}")
        else:
            if config.output_probabilities:
                sentiment, logprob = result  # unpack the tuple
                df.at[tweet_idx, "Sentiment"] = sentiment
                prob = math.exp(logprob)
                df.at[tweet_idx, "Probs"] = prob
            else:
                sentiment = result
                df.at[tweet_idx, "Sentiment"] = sentiment


def calculate_token_count(config, df, log_message):
    log_message("Calculating token counts for each mention...")
    full_user_prompt = f'{config.user_prompt} ""\n{config.user_prompt2}'
    ENCODING = tiktoken.encoding_for_model(config.model_name)
    if config.customization_option == "Multi-Company":
        # Calculate token count for the longest possible prompt (with " toward Company")
        longest_company_name = df["AnalyzedCompany"].max()
        prompt_token_count = len(
            ENCODING.encode(
                config.system_prompt.format(
                    toward_company=f" toward {longest_company_name}"
                )
                + full_user_prompt
            )
        )
    else:
        prompt_token_count = len(
            ENCODING.encode(config.system_prompt + full_user_prompt)
        )

    # Find rows where 'Full Text' is not a string or is empty
    invalid_rows = df[
        ~df["Full Text"].apply(lambda x: isinstance(x, str) and x.strip() != "")
    ].index

    # Drop these rows from the DataFrame
    df.drop(invalid_rows, inplace=True)

    df["Token Count"] = df["Full Text"].apply(
        lambda tweet: len(ENCODING.encode(tweet, allowed_special={"<|endoftext|>"}))
        + prompt_token_count
        + 2
    )


def calculate_batch_size(df, batch_token_limit, batch_requests_limit, start_idx):
    batch_token_count = 0
    batch_end_idx = start_idx
    while (
        batch_end_idx < len(df) and (batch_end_idx - start_idx) < batch_requests_limit
    ):
        tweet_token_count = df.iloc[batch_end_idx]["Token Count"]
        if batch_token_count + tweet_token_count <= batch_token_limit:
            batch_token_count += tweet_token_count
            batch_end_idx += 1
        else:
            break
    return batch_end_idx
