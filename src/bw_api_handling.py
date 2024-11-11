import asyncio
import json
import time
from typing import List

import aiohttp
import pandas as pd

from . import metrics
from .secrets.keys import BW_API_KEY

URL = "https://api.brandwatch.com/projects/***REMOVED***/data/mentions"

TRANSIENT_ERROR_CODES = [502, 503, 504, 408]
MAX_RETRIES = 5
MAX_RATE_LIMIT_WAIT_TIME = 600  # 10 minutes in seconds
BATCH_SIZE = 1360
TIMEOUT_ERROR_CODE = 100

MAX_CONCURRENT_REQUESTS = 5


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
    retries = 0
    chunk_index = 0
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async with aiohttp.ClientSession() as session:
        while chunk_index < len(chunks):
            remaining_chunks = len(chunks) - chunk_index
            chunk_group_size = min(MAX_CONCURRENT_REQUESTS, remaining_chunks)
            current_chunks = chunks[chunk_index:chunk_index + chunk_group_size]

            log_message(f"Sending batches {chunk_index + 1} to {chunk_index + chunk_group_size} of {len(chunks)} to Brandwatch...")

            try:
                processed_count, new_failed_chunks = await process_chunk_group(
                    current_chunks, session, log_message, semaphore
                )

                if new_failed_chunks:
                    if processed_count == 0:
                        # All chunks in this group failed
                        retries += 1
                        if retries > MAX_RETRIES:
                            log_message("Maximum number of retries reached. Exiting...")
                            break

                        wait_time = 60 * (2 ** (retries - 1))
                        log_message(f"Pausing for {wait_time/60} minutes before retrying...")
                        await asyncio.sleep(wait_time)
                        # Don't advance chunk_index - we'll retry the same chunks
                    else:
                        # Some chunks succeeded, some failed
                        # Replace the current chunk group with just the failed chunks
                        chunks[chunk_index:chunk_index + chunk_group_size] = new_failed_chunks
                        chunk_group_size = len(new_failed_chunks)
                        retries = 0  # Reset retries since we had partial success

                if processed_count > 0:
                    total_sent += processed_count
                    log_message(f"Progress: Updated {total_sent} of {len(cleaned_sentiment_dicts)} mentions in Brandwatch.")
                    progress = (total_sent / len(cleaned_sentiment_dicts)) * 10
                    update_progress_gui(progress + 85)
                    chunk_index += chunk_group_size

            except Exception as e:
                log_message(f"Unexpected error processing chunk group: {str(e)}")
                break


async def process_chunk_group(chunks: List[str], session: aiohttp.ClientSession, 
                            log_message, semaphore: asyncio.Semaphore) -> tuple[int, List[str]]:
    """Process a group of chunks in parallel
    Returns: (successful_count, failed_chunks)"""
    tasks = [async_bw_request(session, chunk, log_message, semaphore) 
             for chunk in chunks]
    results = await asyncio.gather(*tasks)
    
    successful_count = 0
    failed_chunks = []
    
    for chunk, (result_type, count) in zip(chunks, results):
        if result_type == "SUCCESS":
            successful_count += count
        else:
            failed_chunks.append(chunk)
            
    return successful_count, failed_chunks


async def async_bw_request(
    session: aiohttp.ClientSession, data: str, log_message, semaphore: asyncio.Semaphore
) -> tuple:
    """
    Async version of the bw_request function that handles a single batch
    Returns a tuple of (result_type, batch_size)
    """
    await asyncio.sleep(0.5)  # Maintain the original rate limiting
    start_time = time.time()
    headers = {
        "Authorization": f"Bearer {BW_API_KEY}",
        "Content-type": "application/json",
    }

    try:
        async with semaphore:  # Control concurrent requests
            async with session.patch(URL, data=data, headers=headers) as response:
                response_time = time.time() - start_time

                if response.status == 429:
                    metrics.log_api_response(
                        "rate_limit", response_time, response.status, data
                    )
                    return "RATE_LIMIT_EXCEEDED", 0

                elif response.status in TRANSIENT_ERROR_CODES:
                    metrics.log_api_response(
                        "transient", response_time, response.status, data
                    )
                    return "TRANSIENT_ERROR", 0

                try:
                    response_json = await response.json()
                except ValueError:
                    metrics.log_api_response(
                        "json_error", response_time, response.status, data
                    )
                    log_message(
                        f"ERROR: Error updating sentiment values in Brandwatch: \n{await response.text()}"
                    )
                    return "JSON_ERROR", 0

                if "errors" in response_json and response_json["errors"]:
                    for error in response_json["errors"]:
                        if error.get("code") == TIMEOUT_ERROR_CODE:
                            metrics.log_api_response(
                                "timeout", response_time, response.status, data
                            )
                            return "TIMEOUT_ERROR", 0

                    metrics.log_api_response(
                        "api_error",
                        response_time,
                        response.status,
                        data,
                        error=response_json["errors"],
                    )
                    log_message(
                        f"ERROR: Error updating sentiment values in Brandwatch: \n{response_json['errors']}"
                    )
                    return "API_ERROR", 0

                metrics.log_api_response(
                    "success", response_time, response.status, data
                )
                return "SUCCESS", len(json.loads(data))

    except Exception as e:
        response_time = time.time() - start_time
        metrics.log_api_response("connection_error", response_time, error=e, data=data)
        log_message(f"Connection error: {str(e)}")
        return "TRANSIENT_ERROR", 0


def prepare_data_for_bw(df, log_message):
    df_bw = df.copy()
    df_bw["Sentiment"] = df_bw[
        "Sentiment"
    ].str.lower()

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
