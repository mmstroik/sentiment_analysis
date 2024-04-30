import requests
import json
import time
import pandas as pd


API_TOKEN = "***REMOVED***"
URL = "https://api.brandwatch.com/projects/***REMOVED***/data/mentions"


def update_bw_sentiment(df, log_callback):
    cleaned_sentiment_dicts = prepare_data_for_bw(df)
    chunks = [
        cleaned_sentiment_dicts[i : i + 1360]
        for i in range(0, len(cleaned_sentiment_dicts), 1360)
    ]
    total_sent = 0
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        data = json.dumps(chunk)
        log_callback(f"Sending batch {i+1} of {len(chunks)} to Brandwatch...")
        result = bw_request(data, log_callback)
        if result == "RATE_LIMIT_EXCEEDED":
            log_callback("Rate limit exceeded, pausing for 10 minutes...")
            time.sleep(600)
            continue
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
    if "Date" in df_bw.columns:
        sentiment_dicts = (
            df_bw[["Query Id", "Resource Id", "Sentiment", "Date", "Checked"]]
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
    else:
        sentiment_dicts = (
            df_bw[["Query Id", "Resource Id", "Sentiment", "Checked"]]
            .rename(
                columns={
                    "Query Id": "queryId",
                    "Resource Id": "resourceId",
                    "Sentiment": "sentiment",
                    "Checked": "checked",
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

    if response.status_code == 429:
        return "RATE_LIMIT_EXCEEDED"

    return True
