import asyncio
import math
import time

from aiohttp import ClientSession

from .token_counting import calculate_token_count
from .model_router import get_model_config

RATE_LIMIT_DELAY = 30  # seconds

# Asynchronously processes tweets in batches (based on token counts)
async def batch_processing_handler(
    config,
    df,
    update_progress_gui,
    log_message,
):
    await calculate_token_count(config, df, log_message)

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
            
        model_config = get_model_config(config.model_name)
        
        if config.customization_option == "Multi-Company":
            tasks = [
                (i, call_model_api(config, model_config, session, tweet, company))
                for i, (tweet, company) in enumerate(
                    zip(batch["Full Text"], batch["AnalyzedCompany"])
                )
            ]
        else:
            tasks = [
                (i, call_model_api(config, model_config, session, tweet))
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

async def call_model_api(config, model_config: dict, session: ClientSession, tweet: str, company: str = None, max_retries=6):
    if config.customization_option == "Multi-Company":
        toward_company = f" toward {company}" if company else ""
        system_prompt = config.system_prompt.format(toward_company=toward_company)
    else:
        system_prompt = config.system_prompt

    payload = model_config["create_payload"](config, system_prompt, tweet)
    
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            async with session.post(
                model_config["api_endpoint"],
                json=payload,
                headers=model_config["headers"],
                params=model_config["params"]
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    sentiment, logprob = model_config["parse_response"](result)
                    return (sentiment, logprob) if config.output_probabilities else sentiment
                elif attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay += 2
                else:
                    return "Error"
        except Exception as e:
            print(f"Error calling model API: {e}")
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
