import asyncio
import math
import time

import pandas as pd
from aiohttp import ClientSession

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public


OPENAI_API_KEY = "***REMOVED***"
ENCODING = tiktoken.get_encoding("cl100k_base")
RATE_LIMIT_DELAY = 30  # seconds


# Asynchronously processes tweets in batches (based on token counts)
async def process_tweets_in_batches(
    df,
    update_progress_callback,
    log_callback,
    system_prompt,
    user_prompt,
    user_prompt2,
    model,
    probs_bool,
    batch_token_limit,
    batch_requests_limit,
    customization_option,
):
    calculate_token_count(df, system_prompt, user_prompt, user_prompt2, log_callback, customization_option)
    total = len(df)
    processed = 0
    async with ClientSession() as session:
        start_idx = 0
        update_progress_callback(5)

        start_time = await main_batch_processing_loop(
            df,
            update_progress_callback,
            log_callback,
            system_prompt,
            user_prompt,
            user_prompt2,
            model,
            probs_bool,
            batch_token_limit,
            batch_requests_limit,
            total,
            processed,
            session,
            start_idx,
            customization_option
        )
        
        # Reprocess errored tweets
        errored_df = df[df["Sentiment"].isin(["Error", ""])]
        if not errored_df.empty:        
            start_time = await reprocess_errors(
                df,
                update_progress_callback,
                log_callback,
                system_prompt,
                user_prompt,
                user_prompt2,
                model,
                probs_bool,
                batch_token_limit,
                batch_requests_limit,
                session,
                customization_option,
                errored_df,
            )
            # if any error still exists, notify the user how many and move on
            errored_df = df[df["Sentiment"].isin(["Error", ""])]
            if not errored_df.empty:
                log_callback(
                    f"Still error processing {len(errored_df)} mentions. Contact Milo if persistent."
                )
    return df, start_time


async def main_batch_processing_loop(
    df,
    update_progress_callback,
    log_callback,
    system_prompt,
    user_prompt,
    user_prompt2,
    model,
    probs_bool,
    batch_token_limit,
    batch_requests_limit,
    total,
    processed,
    session,
    start_idx,
    customization_option,
):
    while start_idx < len(df):
        log_callback("Calculating size of next batch...")
        batch_end_idx = calculate_batch_size(
            df, batch_token_limit, batch_requests_limit, start_idx
        )
        log_callback(
            f"Processing batch {start_idx+1}-{batch_end_idx} of {total} mentions..."
        )
        # Set batch index and send requests
        batch = df.iloc[start_idx:batch_end_idx]
        if customization_option == "Multi-Company":
            tasks = [
                call_openai_async(session, tweet, system_prompt, user_prompt, user_prompt2, model, probs_bool, customization_option, company)
                for tweet, company in zip(batch["Full Text"], batch["AnalyzedCompany"])
            ]
        else:
            tasks = [
                call_openai_async(session, tweet, system_prompt, user_prompt, user_prompt2, model, probs_bool, customization_option)
                for tweet in batch["Full Text"]
            ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        timer = asyncio.create_task(asyncio.sleep(RATE_LIMIT_DELAY))
        start_time = time.time()

        # Handle results
        for tweet_idx, result in zip(batch.index, results):
            if isinstance(result, Exception):
                log_callback(f"Error processing text at row {tweet_idx}: {result}")
            else:
                if probs_bool:
                    sentiment, logprob = result  # unpack the tuple
                    df.at[tweet_idx, "Sentiment"] = sentiment
                    prob = math.exp(logprob)
                    df.at[tweet_idx, "Probs"] = prob
                else:
                    sentiment = result 
                    df.at[tweet_idx, "Sentiment"] = sentiment


        processed += len(results)
        progress = (processed / total) * 90
        update_progress_callback(progress)
        log_callback(f"Progress: Processed {processed} of {total} mentions.")
        start_idx = batch_end_idx

        if start_idx < len(df):
            log_callback(f"Waiting {str(RATE_LIMIT_DELAY)} secs for rate limit timer...")
            await timer
    
    return start_time


async def reprocess_errors(
    df,
    update_progress_callback,
    log_callback,
    system_prompt,
    user_prompt,
    user_prompt2,
    model,
    probs_bool,
    batch_token_limit,
    batch_requests_limit,
    session,
    customization_option,
    errored_df,
):
    log_callback(
        f"Waiting for rate limit timer before reprocessing {len(errored_df)} errored mentions..."
    )
    await asyncio.sleep(RATE_LIMIT_DELAY)  # Wait for 60 seconds before starting
    await asyncio.sleep(5)

    total_errors = len(errored_df)
    processed_errors = 0
    start_idx = 0

    while start_idx < len(errored_df):
        batch_end_idx = calculate_batch_size(
            errored_df, batch_token_limit, batch_requests_limit, start_idx
        )

        # Reprocess the batch of errored tweets
        batch = errored_df.iloc[start_idx:batch_end_idx]
        if customization_option == "Multi-Company":
            tasks = [
                call_openai_async(session, tweet, system_prompt, user_prompt, user_prompt2, model, probs_bool, customization_option, company)
                for tweet, company in zip(batch["Full Text"], batch["AnalyzedCompany"])
            ]
        else:
            tasks = [
                call_openai_async(session, tweet, system_prompt, user_prompt, user_prompt2, model, probs_bool, customization_option)
                for tweet in batch["Full Text"]
            ]
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        start_time = time.time()

        # Handle results
        for tweet_idx, result in zip(batch.index, results):
            if isinstance(result, Exception):
                log_callback(f"Error processing text at row {tweet_idx}: {result}")
            else:
                if probs_bool:
                    sentiment, logprob = result  # unpack the tuple
                    df.at[tweet_idx, "Sentiment"] = sentiment
                    prob = math.exp(logprob)
                    df.at[tweet_idx, "Probs"] = prob
                else:
                    sentiment = result 
                    df.at[tweet_idx, "Sentiment"] = sentiment

        processed_errors += len(results)
        progress = (processed_errors / total_errors) * 90
        update_progress_callback(
            progress + 5
        )  # Adjust progress callback for error processing
        log_callback(
            f"Reprocessed {processed_errors} of {total_errors} errored mentions."
        )
        start_idx = batch_end_idx
    
    return start_time


# Asynchronously calls the API for each tweet in the batch
async def call_openai_async(
    session: ClientSession,
    tweet: str,
    system_prompt: str,
    user_prompt: str,
    user_prompt2: str,
    model: str,
    probs_bool: bool = False,
    customization_option: str = "Default",
    company: str = None,
    max_retries=6,
):

    if customization_option == "Multi-Company":
        toward_company = f" toward {company}" if company else ""
        system_prompt = system_prompt.format(toward_company=toward_company)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'{user_prompt} "{tweet}"\n{user_prompt2}'},
        ],
        "temperature": 0.3,
        "max_tokens": 1,
        "logprobs": probs_bool,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    retry_delay = 1
    for attempt in range(max_retries):
        try:
            async with session.post(
                "https://api.openai.com/v1/chat/completions", json=payload, headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    sentiment = result["choices"][0]["message"]["content"]
                    if probs_bool:
                        logprob = result["choices"][0]["logprobs"]["content"][0]["logprob"]
                        return sentiment.strip(), logprob
                    else:
                        return sentiment.strip()
                elif attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)  # Wait before retrying
                    retry_delay += 2
                else:
                    result = await response.text()
                    print(result)
                    return "Error"
        except Exception as e:
            print(e)
            return "Error"       


def calculate_token_count(df, system_prompt, user_prompt, user_prompt2, log_callback, customization_option):
    log_callback("Calculating token counts for each mention...")
    full_user_prompt = f'{user_prompt} ""\n{user_prompt2}'

    if customization_option == "Multi-Company":
        # Calculate token count for the longest possible prompt (with " toward Company")
        longest_company_name = df['AnalyzedCompany'].max()
        prompt_token_count = len(ENCODING.encode(system_prompt.format(toward_company=f" toward {longest_company_name}") + full_user_prompt))
    else:
        prompt_token_count = len(ENCODING.encode(system_prompt + full_user_prompt))
    
    # Find rows where 'Full Text' is not a string or is empty
    invalid_rows = df[~df['Full Text'].apply(lambda x: isinstance(x, str) and x.strip() != '')].index
    
    # Drop these rows from the DataFrame
    df.drop(invalid_rows, inplace=True)
    
    df["Token Count"] = df["Full Text"].apply(
        lambda tweet: len(ENCODING.encode(tweet)) + prompt_token_count + 2
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

