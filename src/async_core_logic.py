import asyncio
import math
import time
import logging
from logging.handlers import QueueHandler
import queue

import pandas as pd
from aiohttp import ClientSession

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public

from .secrets.keys import OPENAI_API_KEY

RATE_LIMIT_DELAY = 30  # seconds

log_queue = queue.Queue(-1)  # No limit on size
queue_handler = QueueHandler(log_queue)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(queue_handler)


# Asynchronously processes tweets in batches (based on token counts)
async def process_tweets_in_batches(
    config,
    df,
    update_progress_gui,
    log_message,
):
    calculate_token_count(config, df, log_message)
    total = len(df)
    processed = 0
    async with ClientSession() as session:
        start_idx = 0
        update_progress_gui(5)
        start_time = await main_batch_processing_loop(
            config,
            df,
            update_progress_gui,
            log_message,
            total,
            processed,
            session,
            start_idx,
        )

        # Reprocess errored tweets
        errored_df = df[df["Sentiment"].isin(["Error", ""])]
        if not errored_df.empty:
            start_time = await reprocess_errors(
                config,
                df,
                update_progress_gui,
                log_message,
                session,
                errored_df,
            )
            # if any error still exists, notify the user how many and move on
            errored_df = df[df["Sentiment"].isin(["Error", ""])]
            if not errored_df.empty:
                log_message(
                    f"Still error processing {len(errored_df)} mentions. Contact Milo if persistent."
                )
    return df, start_time


async def main_batch_processing_loop(
    config,
    df,
    update_progress_gui,
    log_message,
    total,
    processed,
    session,
    start_idx,
):
    while start_idx < len(df):
        log_message("Calculating size of next batch...")
        batch_end_idx = calculate_batch_size(
            df, config.batch_token_limit, config.batch_requests_limit, start_idx
        )
        log_message(
            f"Processing batch {start_idx+1}-{batch_end_idx} of {total} mentions..."
        )
        # Set batch index and send requests
        batch = df.iloc[start_idx:batch_end_idx]
        if config.customization_option == "Multi-Company":
            tasks = [
                call_openai_async(config, session, tweet, company)
                for tweet, company in zip(batch["Full Text"], batch["AnalyzedCompany"])
            ]
        else:
            tasks = [
                call_openai_async(config, session, tweet)
                for tweet in batch["Full Text"]
            ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        timer = asyncio.create_task(asyncio.sleep(RATE_LIMIT_DELAY))
        start_time = time.time()

        # Handle results
        handle_batch_results(config, df, log_message, batch, results)

        processed += len(results)
        progress = (processed / total) * 80
        update_progress_gui(progress + 5)
        log_message(f"Progress: Processed {processed} of {total} mentions.")
        start_idx = batch_end_idx

        if start_idx < len(df):
            log_message(
                f"Waiting {str(RATE_LIMIT_DELAY)} secs for rate limit timer..."
            )
            await timer

    return start_time


async def reprocess_errors(
    config,
    df,
    update_progress_gui,
    log_message,
    session,
    errored_df,
):
    log_message(
        f"Waiting for rate limit timer before reprocessing {len(errored_df)} errored mentions..."
    )

    await asyncio.sleep(RATE_LIMIT_DELAY)  # Wait for 60 seconds before starting
    await asyncio.sleep(5)
    
    if len(errored_df) == 1:
        errored_index = errored_df.index[0] + 2
        log_message(f"Reprocessing single errored mention at output row {errored_index}")
        
    total_errors = len(errored_df)
    processed_errors = 0
    start_idx = 0

    while start_idx < len(errored_df):
        batch_end_idx = calculate_batch_size(
            errored_df, config.batch_token_limit, config.batch_requests_limit, start_idx
        )

        # Reprocess the batch of errored tweets
        batch = errored_df.iloc[start_idx:batch_end_idx]
        if config.customization_option == "Multi-Company":
            tasks = [
                call_openai_async(config, session, tweet, company)
                for tweet, company in zip(batch["Full Text"], batch["AnalyzedCompany"])
            ]
        else:
            tasks = [
                call_openai_async(config, session, tweet)
                for tweet in batch["Full Text"]
            ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        start_time = time.time()

        handle_batch_results(config, df, log_message, batch, results)

        processed_errors += len(results)
        progress = (processed_errors / total_errors) * 80
        update_progress_gui(
            progress + 5
        )  # Adjust progress callback for error processing
        log_message(
            f"Reprocessed {processed_errors} of {total_errors} errored mentions."
        )
        start_idx = batch_end_idx

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
        "temperature": 0.3,
        "max_tokens": 1,
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
                        logprob = result["choices"][0]["logprobs"]["content"][0]["logprob"]
                        return sentiment.strip(), logprob
                    else:
                        return sentiment.strip()
                elif attempt < max_retries - 1:
                    logger.warning(f"Retry attempt {attempt + 1} for tweet: {tweet[:50]}...")
                    await asyncio.sleep(retry_delay)  # Wait before retrying
                    retry_delay += 2
                else:
                    result = await response.text()
                    logger.error(f"Failed after {max_retries} attempts for tweet: {tweet[:50]}... Error: {result}")
                    return "Error"
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Retry attempt {attempt + 1} for tweet: {tweet[:50]}... Exception: {str(e)}")
                await asyncio.sleep(retry_delay)  # Wait before retrying
                retry_delay += 2
            else:
                logger.error(f"Failed after {max_retries} attempts for tweet: {tweet[:50]}... Exception: {str(e)}")
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
    # Calculate and log the total input tokens
    total_input_tokens = df["Token Count"].sum()
    log_message(f"Total input tokens: {total_input_tokens}")


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
