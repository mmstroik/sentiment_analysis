import asyncio

import pandas as pd
from aiohttp import ClientSession

import tiktoken
import tiktoken_ext
from tiktoken_ext import openai_public


OPENAI_API_KEY = "***REMOVED***"
ENCODING = tiktoken.get_encoding("cl100k_base")


# Asynchronously processes tweets in batches (based on token counts)
async def process_tweets_in_batches(
    df,
    token_buffer: int,
    update_progress_callback,
    log_callback,
    system_prompt,
    user_prompt,
    model,
    batch_token_limit,
    batch_requests_limit,
):
    log_callback("Calculating token counts for each tweet/sample...")
    calculate_token_count(df, token_buffer)

    total = len(df)
    processed = 0
    async with ClientSession() as session:
        start_idx = 0
        update_progress_callback(5)

        await main_batch_processing_loop(
            df,
            update_progress_callback,
            log_callback,
            system_prompt,
            user_prompt,
            model,
            batch_token_limit,
            batch_requests_limit,
            total,
            processed,
            session,
            start_idx,
        )

        # Reprocess errored tweets
        await reprocess_errors(
            df,
            update_progress_callback,
            log_callback,
            system_prompt,
            user_prompt,
            model,
            batch_token_limit,
            batch_requests_limit,
            session,
        )
    return df


async def main_batch_processing_loop(
    df,
    update_progress_callback,
    log_callback,
    system_prompt,
    user_prompt,
    model,
    batch_token_limit,
    batch_requests_limit,
    total,
    processed,
    session,
    start_idx,
):
    while start_idx < len(df):
        log_callback("Calculating size of next batch...")
        batch_end_idx = calculate_batch_size(
            df, batch_token_limit, batch_requests_limit, start_idx
        )
        log_callback(
            f"Processing batch {start_idx+1}-{batch_end_idx} of {total} tweets/samples..."
        )
        # Set batch and send requests
        batch = df.iloc[start_idx:batch_end_idx]
        tasks = [
            call_openai_async(session, tweet, system_prompt, user_prompt, model)
            for tweet in batch["Full Text"]
        ]
        timer = asyncio.create_task(asyncio.sleep(60))
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle results
        for tweet_idx, result in zip(batch.index, results):
            if isinstance(result, Exception):
                log_callback(f"Error processing text at row {tweet_idx}: {result}")
            else:
                df.at[tweet_idx, "Sentiment"] = result

        processed += len(results)
        progress = (processed / total) * 95
        update_progress_callback(progress)
        log_callback(f"Processed {processed} of {total} tweets/samples.")
        start_idx = batch_end_idx

        if start_idx < len(df):
            log_callback("Waiting for rate limit timer...")
            await timer


# Asynchronously reprocesses errored tweets
async def reprocess_errors(
    df,
    update_progress_callback,
    log_callback,
    system_prompt,
    user_prompt,
    model,
    batch_token_limit,
    batch_requests_limit,
    session,
):
    errored_df = df[df["Sentiment"].isin(["Error", ""])]
    if not errored_df.empty:
        log_callback(
            f"Waiting for rate limit timer before reprocessing {len(errored_df)} errored tweets..."
        )
        await asyncio.sleep(60)  # Wait for 60 seconds before starting the reprocessing

        total_errors = len(errored_df)
        processed_errors = 0
        start_idx = 0

        while start_idx < len(errored_df):
            batch_end_idx = calculate_batch_size(
                errored_df, batch_token_limit, batch_requests_limit, start_idx
            )

            # Reprocess the batch of errored tweets
            batch = errored_df.iloc[start_idx:batch_end_idx]
            tasks = [
                call_openai_async(session, tweet, system_prompt, user_prompt, model)
                for tweet in batch["Full Text"]
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results for errored tweets
            for tweet_idx, result in zip(batch.index, results):
                if isinstance(result, Exception):
                    log_callback(
                        f"Error reprocessing text at row {tweet_idx}: {result}"
                    )
                    df.at[tweet_idx, "Sentiment"] = "Final Error"
                else:
                    df.at[tweet_idx, "Sentiment"] = result

            processed_errors += len(results)
            progress = (processed_errors / total_errors) * 95
            update_progress_callback(
                progress + 5
            )  # Adjust progress callback for error processing
            log_callback(
                f"Reprocessed {processed_errors} of {total_errors} errored tweets."
            )
            start_idx = batch_end_idx


# Asynchronously calls the API to classify the sentiment of a tweet/sample
async def call_openai_async(
    session: ClientSession,
    tweet: str,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_retries=6,
):
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'{user_prompt} "{tweet}"\nSentiment:'},
        ],
        "temperature": 0,
        "max_tokens": 1,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    retry_delay = 1
    for attempt in range(max_retries):
        async with session.post(
            "https://api.openai.com/v1/chat/completions", json=payload, headers=headers
        ) as response:
            if response.status == 200:
                result = await response.json()
                sentiment = result["choices"][0]["message"]["content"]
                return sentiment.strip()
            elif attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)  # Wait before retrying
                retry_delay += 2
            else:
                result = await response.text()
                # todo
                return "Error"  # Return an error marker


def calculate_token_count(df, token_buffer):
    df["Token Count"] = df["Full Text"].apply(
        lambda tweet: len(ENCODING.encode(tweet)) + token_buffer
    )


# Calculate batch size
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
