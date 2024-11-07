import os
from datetime import datetime
import requests
import json
import time
import pandas as pd
from requests.exceptions import ChunkedEncodingError, RequestException
import sys

API_TOKEN = "***REMOVED***"
URL = "https://api.brandwatch.com/projects/***REMOVED***/data/mentions"

TRANSIENT_ERROR_CODES = [502, 503, 504, 408]
MAX_RETRIES = 5
MAX_RATE_LIMIT_WAIT_TIME = 600  # 10 minutes in seconds
BATCH_SIZE = 1360
TIMEOUT_ERROR_CODE = 100


def update_bw_sentiment(df, update_progress_gui, log_message):
    cleaned_sentiment_dicts = prepare_data_for_bw(df, log_message)
    chunks = [
        cleaned_sentiment_dicts[i : i + BATCH_SIZE]
        for i in range(0, len(cleaned_sentiment_dicts), BATCH_SIZE)
    ]
    total_sent = 0
    i = 0
    retries = 0
    rate_limit_wait_time = 60  # Start with 1 min retry time
    while i < len(chunks):
        chunk = chunks[i]
        data = json.dumps(chunk)
        log_message(f"Sending batch {i+1} of {len(chunks)} to Brandwatch...")
        result = bw_request(data, log_message)

        if result == "RATE_LIMIT_EXCEEDED":
            log_message(
                f"Rate limit exceeded, pausing for {rate_limit_wait_time/60} minutes..."
            )
            time.sleep(rate_limit_wait_time)
            rate_limit_wait_time = min(
                rate_limit_wait_time * 2, MAX_RATE_LIMIT_WAIT_TIME
            )  # Double wait time for the next retry, up to 10 minutes
            continue  # retry the same chunk

        elif result == "TIMEOUT_ERROR" or result == "TRANSIENT_ERROR":
            retries += 1
            if retries > MAX_RETRIES:
                log_message("Maximum number of retries reached. Exiting...")
                break
            wait_time = 60 * (2 ** (retries - 1))  # Exponential backoff
            log_message(
                f"{'Timeout' if result == 'TIMEOUT_ERROR' else 'Transient'} error occurred, pausing for {wait_time/60} minutes before retrying..."
            )
            time.sleep(wait_time)
            continue  # retry the same chunk

        elif not result:
            break

        total_sent += len(chunk)
        log_message(
            f"Progress: Updated {total_sent} of {len(cleaned_sentiment_dicts)} mentions in Brandwatch."
        )
        progress = (total_sent / len(cleaned_sentiment_dicts)) * 10
        update_progress_gui(progress + 85)
        i += 1


def prepare_data_for_bw(df, log_message):
    df_bw = df.copy()
    df_bw["Sentiment"] = df_bw[
        "Sentiment"
    ].str.lower()  # Convert sentiment values to lowercase for api

    # if any mentions have a sentiment value that Is NOT: "positive", "negative", or "neutral", remove them from df before upload
    df_bw = df_bw[df_bw["Sentiment"].isin(["positive", "negative", "neutral"])]
    # log removed mentions only if there are any
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

    # set 'checked' to true for updated mentions
    if "Checked" not in df_bw.columns:
        df_bw["Checked"] = "true"
    else:
        df_bw["Checked"] = df_bw["Checked"].apply(lambda x: "true")

    sentiment_dicts = create_dict_list(df_bw)

    return sentiment_dicts


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


def log_api_response(status, response_time, response_code=None, data=None, error=None, log_dir="api_response_logs"):
    # Get the application's base directory
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_dir = os.path.join(base_dir, "api_response_logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"bw_api_metrics_{datetime.now().strftime('%Y_%m')}.csv")
    
    response_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': status,  # 'success', 'rate_limit', 'timeout', 'error', etc.
        'response_time': response_time,
        'response_code': response_code,
        'batch_size': len(json.loads(data)) if data else 0,
        'error_type': type(error).__name__ if error else None,
        'error_message': str(error) if error else None
    }
    
    df = pd.DataFrame([response_data])
    if os.path.exists(log_file):
        df.to_csv(log_file, mode='a', header=False, index=False)
    else:
        df.to_csv(log_file, index=False)
    
    return response_data
def bw_request(data, log_message):
    time.sleep(0.5)
    start_time = time.time()
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-type": "application/json",
    }

    try:
        response = requests.patch(URL, data=data, headers=headers)
        response_time = time.time() - start_time

        if response.status_code == 429:
            print(f"\nRate Limit Details:")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Remaining Requests: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
            log_api_response('rate_limit', response_time, response.status_code, data)
            return "RATE_LIMIT_EXCEEDED"
            
        elif response.status_code in TRANSIENT_ERROR_CODES:
            print(f"\nTransient Error Details:")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            log_api_response('transient', response_time, response.status_code, data)
            return "TRANSIENT_ERROR"
        
        try:
            response_json = response.json()
        except ValueError:
            print(f"\nJSON Parsing Error:")
            print(f"Status Code: {response.status_code}")
            print(f"Raw Response: {response.text}")
            log_api_response('json_error', response_time, response.status_code, data)
            log_message(f"ERROR: Error updating sentiment values in Brandwatch: \n{response.text}")
            return False

        if "errors" in response_json and response_json["errors"]:
            print(f"\nAPI Error Details:")
            print(f"Status Code: {response.status_code}")
            print(f"Full Error Response: {json.dumps(response_json, indent=2)}")
            for error in response_json["errors"]:
                if error.get("code") == TIMEOUT_ERROR_CODE:
                    log_api_response('timeout', response_time, response.status_code, data)
                    return "TIMEOUT_ERROR"
            log_api_response('api_error', response_time, response.status_code, data)
            log_message(f"ERROR: Error updating sentiment values in Brandwatch: \n{response_json['errors']}")
            return False

        # Log successful response
        log_api_response('success', response_time, response.status_code, data)
        print(f"response time for successful request: {response_time} seconds")
        return True

    except (ChunkedEncodingError, RequestException) as e:
        response_time = time.time() - start_time
        log_api_response('connection_error', response_time, error=e, data=data)
        print(f"\nConnection Error Details:")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Full Exception: {str(e)}")
        print(f"response time for connection error: {response_time} seconds")
        log_message(f"Connection error: {str(e)}")
        return "TRANSIENT_ERROR"

