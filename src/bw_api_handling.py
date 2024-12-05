import asyncio
import json
import time
from typing import List
from enum import Enum

import aiohttp
import pandas as pd

from . import metrics
from .secrets.keys import BW_API_KEY, PROJECT_ID

URL = f"https://api.brandwatch.com/projects/{PROJECT_ID}/data/mentions"

TRANSIENT_ERROR_CODES = [502, 503, 504, 408]
MAX_RETRIES = 5
MAX_RATE_LIMIT_WAIT_TIME = 600  # 10 minutes in seconds
BATCH_SIZE = 1360
TIMEOUT_ERROR_CODE = 100

MAX_CONCURRENT_REQUESTS = 5


class BWError(Enum):
    SUCCESS = "SUCCESS"
    RATE_LIMIT = "RATE_LIMIT"  # 429 - needs backoff
    TRANSIENT = "TRANSIENT"    # 502, 503, 504, 408 - can retry immediately
    TIMEOUT = "TIMEOUT"        # API timeout - can retry immediately
    PERMANENT = "PERMANENT"    # Other API errors - don't retry
    DUPLICATE_TAG = "DUPLICATE_TAG"  # Duplicate tag error - retry without tags


def update_bw_sentiment(df: pd.DataFrame, update_progress_gui, log_message) -> None:
    asyncio.run(async_update_bw_sentiment(df, update_progress_gui, log_message))


async def async_update_bw_sentiment(
    df: pd.DataFrame, update_progress_gui, log_message
) -> None:
    cleaned_sentiment_dicts = prepare_data_for_bw(df, log_message)
    chunks = [
        json.dumps(cleaned_sentiment_dicts[i : i + BATCH_SIZE])
        for i in range(0, len(cleaned_sentiment_dicts), BATCH_SIZE)
    ]

    total_sent = 0
    chunk_index = 0
    backoff_time = 60  # Start with 1 minute backoff

    async with aiohttp.ClientSession() as session:
        while chunk_index < len(chunks):
            remaining_chunks = len(chunks) - chunk_index
            chunk_group_size = min(MAX_CONCURRENT_REQUESTS, remaining_chunks)
            current_chunks = chunks[chunk_index : chunk_index + chunk_group_size]

            log_message(
                f"Sending batches {chunk_index + 1} to {chunk_index + chunk_group_size} of {len(chunks)} to Brandwatch..."
            )

            try:
                processed_count, failed_chunks, needs_backoff = await process_chunk_group(
                    current_chunks, session, log_message
                )

                num_successes = len(current_chunks) - len(failed_chunks)
                
                if failed_chunks:
                    if needs_backoff:
                        # Rate limit hit - implement exponential backoff
                        backoff_time = min(backoff_time * 2, MAX_RATE_LIMIT_WAIT_TIME)
                        log_message(f"Rate limit reached. Backing off for {backoff_time/60:.1f} minutes...")
                        await asyncio.sleep(backoff_time)
                    elif processed_count == 0:
                        # All chunks failed with transient errors - small delay and retry
                        log_message("All requests failed. Retrying after short delay...")
                        await asyncio.sleep(5)
                    
                    # Replace remaining chunks with failed ones
                    chunks[chunk_index + num_successes : chunk_index + chunk_group_size] = failed_chunks
                    
                    if processed_count > 0:
                        # If we had some successes, reset backoff
                        backoff_time = 60
                        total_sent += processed_count
                        log_message(
                            f"Progress: Updated {total_sent} of {len(cleaned_sentiment_dicts)} mentions in Brandwatch."
                        )
                        progress = (total_sent / len(cleaned_sentiment_dicts)) * 30  # 30% range for BW
                        update_progress_gui(65 + progress)

                    # Only advance by number of successful chunks
                    chunk_index += num_successes

                else:
                    # All chunks succeeded
                    total_sent += processed_count
                    backoff_time = 60  # Reset backoff time
                    log_message(
                        f"Progress: Updated {total_sent} of {len(cleaned_sentiment_dicts)} mentions in Brandwatch."
                    )
                    progress = (total_sent / len(cleaned_sentiment_dicts)) * 30  # 30% range for BW
                    update_progress_gui(65 + progress)
                    chunk_index += chunk_group_size

            except Exception as e:
                log_message(f"Unexpected error processing chunk group: {str(e)}")
                break


async def process_chunk_group(
    chunks: List[str],
    session: aiohttp.ClientSession,
    log_message
) -> tuple[int, List[str], bool]:
    """Process a group of chunks in parallel
    Returns: (successful_count, failed_chunks, needs_backoff)"""
    tasks = [
        async_bw_request(session, chunk) for chunk in chunks
    ]
    results = await asyncio.gather(*tasks)

    successful_count = 0
    failed_chunks = []
    needs_backoff = False

    for chunk, (error_type, count) in zip(chunks, results):
        if error_type == BWError.SUCCESS:
            successful_count += count
        elif error_type == BWError.RATE_LIMIT:
            needs_backoff = True
            failed_chunks.append(chunk)
        elif error_type in (BWError.TRANSIENT, BWError.TIMEOUT):
            failed_chunks.append(chunk)
        elif error_type == BWError.DUPLICATE_TAG:
            # Log message and retry without tags
            log_message("Duplicate tag error detected. Retrying chunk without tags...")
            chunk_data = json.loads(chunk)
            for item in chunk_data:
                item.pop("addTag", None)  # Remove addTag field
            failed_chunks.append(json.dumps(chunk_data))
        # PERMANENT errors are dropped

    return successful_count, failed_chunks, needs_backoff


async def async_bw_request(
    session: aiohttp.ClientSession, data: str
) -> tuple[BWError, int]:
    await asyncio.sleep(0.5)
    start_time = time.time()
    headers = {
        "Authorization": f"Bearer {BW_API_KEY}",
        "Content-type": "application/json",
    }

    try:
        async with session.patch(URL, data=data, headers=headers) as response:
            http_response_time = time.time() - start_time
            print(f"HTTP response time: {http_response_time:.2f}s")
            
            # Handle HTTP-level errors first
            if response.status == 429:
                metrics.log_api_response("rate_limit", http_response_time, http_response_time, response.status, data)
                return BWError.RATE_LIMIT, 0
            
            if response.status in TRANSIENT_ERROR_CODES:
                metrics.log_api_response("transient", http_response_time, http_response_time, response.status, data)
                return BWError.TRANSIENT, 0

            # Try to parse response
            try:
                response_json = await response.json()
            except json.JSONDecodeError as e:
                total_response_time = time.time() - start_time
                print(f"Failed to parse response. Total response time: {total_response_time:.2f}s")
                metrics.log_api_response("read_error", http_response_time, total_response_time, response.status, data=data, error=e)
                return BWError.TRANSIENT, 0
            total_response_time = time.time() - start_time
            
            # Handle API-level errors
            if "errors" in response_json and response_json["errors"]:
                for error in response_json["errors"]:
                    if error.get("code") == TIMEOUT_ERROR_CODE:
                        metrics.log_api_response("timeout", http_response_time, total_response_time, response.status, data)
                        return BWError.TIMEOUT, 0
                    
                    # Check for duplicate tag error
                    if error.get("code") == 201 and "Tag with that name already exists" in error.get("message", ""):
                        metrics.log_api_response("duplicate_tag", http_response_time, total_response_time, response.status, data)
                        return BWError.DUPLICATE_TAG, 0

                metrics.log_api_response("api_error", http_response_time, total_response_time, response.status, data, error=response_json["errors"])
                return BWError.PERMANENT, 0
            print(f"Total response time: {total_response_time:.2f}s")
            metrics.log_api_response("success", http_response_time, total_response_time, response.status, data=data)
            return BWError.SUCCESS, len(json.loads(data))

    except Exception as e:
        total_response_time = time.time() - start_time
        print(f"Failed to send request. Total response time: {total_response_time:.2f}s")
        metrics.log_api_response("connection_error", http_response_time=0, total_response_time=total_response_time, data=data, error=e)
        return BWError.TRANSIENT, 0


def prepare_data_for_bw(df, log_message):
    df_bw = df.copy()
    df_bw["Sentiment"] = df_bw["Sentiment"].str.lower()

    # remove invalid sentiment values
    df_bw = df_bw[df_bw["Sentiment"].isin(["positive", "negative", "neutral"])]
    if len(df) != len(df_bw):
        removed_mentions = len(df) - len(df_bw)
        log_message(
            f"Removed {removed_mentions} mentions with invalid sentiment values before uploading to Brandwatch."
        )

    if "BW_Tags" in df_bw.columns:
        log_message(
            "Adding sentiment tags to company mentions before uploading to Brandwatch..."
        )
        df_bw["addTag"] = df_bw["BW_Tags"].apply(
            lambda x: x.split(",") if pd.notna(x) and x else []
        )
        df_bw = df_bw.drop(columns=["BW_Tags"])

    if "Date" in df_bw.columns:
        df_bw["Date"] = (
            pd.to_datetime(df_bw["Date"]).dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+0000"
        )

    df_bw["Checked"] = "true"

    return create_dict_list(df_bw)


def create_dict_list(df_bw):
    base_columns = ["Query Id", "Resource Id", "Sentiment", "Checked"]

    if "Date" in df_bw.columns:
        base_columns.append("Date")

    sentiment_dicts = (
        df_bw[base_columns]
        .rename(
            columns={
                "Query Id": "queryId",
                "Resource Id": "resourceId",
                "Sentiment": "sentiment",
                "Date": "date",
                "Checked": "checked",
            }
        )
        .to_dict("records")
    )

    # Add 'addTag' to dictionaries where it exists and is not empty
    if "addTag" in df_bw.columns:
        for i, row in df_bw.iterrows():
            if row["addTag"]:
                sentiment_dicts[i]["addTag"] = row["addTag"]

    return sentiment_dicts
