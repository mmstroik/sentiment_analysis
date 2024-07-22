import requests
import json
import time
import pandas as pd

API_TOKEN = "***REMOVED***"
URL = "https://api.brandwatch.com/projects/***REMOVED***/data/mentions"

TRANSIENT_ERROR_CODES = [502, 503, 504, 408]
MAX_RETRIES = 5
MAX_RATE_LIMIT_WAIT_TIME = 600  # 10 minutes in seconds


def update_bw_sentiment(df, log_callback):
    cleaned_sentiment_dicts = prepare_data_for_bw(df)
    chunks = [
        cleaned_sentiment_dicts[i : i + 1360]
        for i in range(0, len(cleaned_sentiment_dicts), 1360)
    ]
    total_sent = 0
    i = 0
    retries = 0
    rate_limit_wait_time = 60  # Start with 1 min retry time
    while i < len(chunks):
        chunk = chunks[i]
        data = json.dumps(chunk)
        log_callback(f"Sending batch {i+1} of {len(chunks)} to Brandwatch...")
        result = bw_request(data, log_callback)

        if result == "RATE_LIMIT_EXCEEDED":
            log_callback(
                f"Rate limit exceeded, pausing for {rate_limit_wait_time/60} minutes..."
            )
            time.sleep(rate_limit_wait_time)
            rate_limit_wait_time = min(
                rate_limit_wait_time * 2, MAX_RATE_LIMIT_WAIT_TIME
            )  # Double wait time for the next retry, up to 10 minutes
            continue  # retry the same chunk

        elif result == "TRANSIENT_ERROR":
            retries += 1
            if retries > MAX_RETRIES:
                log_callback("Maximum number of retries reached. Exiting...")
                break
            log_callback(
                "Transient error occurred, pausing for 1 minute before retrying..."
            )
            time.sleep(60)
            continue  # retry the same chunk

        elif not result:
            break

        total_sent += len(chunk)
        log_callback(
            f"Progress: Updated {total_sent} of {len(cleaned_sentiment_dicts)} mentions in Brandwatch."
        )
        i += 1


def prepare_data_for_bw(df):
    df_bw = df.copy()
    df_bw["Sentiment"] = df_bw[
        "Sentiment"
    ].str.lower()  # Convert sentiment values to lowercase for api
    
    # if any mentions have a sentiment value that Is NOT: "positive", "negative", or "neutral", remove them from df before upload
    df_bw = df_bw[df_bw["Sentiment"].isin(["positive", "negative", "neutral"])]

    if 'BW_Tags' in df_bw.columns:
        df_bw['addTag'] = df_bw['BW_Tags'].apply(lambda x: x.split(',') if pd.notna(x) else [])
        df_bw = df_bw.drop(columns=['BW_Tags'])

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
    
    if 'addTag' in df_bw.columns:
        base_columns.append('addTag')
    
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
                "addTag": "addTag"
            }
        )
        .to_dict("records")
    )

    return sentiment_dicts


def bw_request(data, log_callback):
    time.sleep(0.5)

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-type": "application/json",
    }

    response = requests.patch(URL, data=data, headers=headers)
    if response.status_code == 429:
        return "RATE_LIMIT_EXCEEDED"
    elif response.status_code in TRANSIENT_ERROR_CODES:
        return "TRANSIENT_ERROR"
    try:
        response_json = response.json()
    except ValueError:
        log_callback(
            f"ERROR: Error updating sentiment values in Brandwatch: \n{response.text}"
        )
        return False

    if "errors" in response_json and response_json["errors"]:
        log_callback(
            f"ERROR: Error updating sentiment values in Brandwatch: \n{response_json['errors']}"
        )
        return False

    return True
