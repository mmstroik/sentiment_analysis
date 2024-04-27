import requests
import json


API_TOKEN = "***REMOVED***"
URL = "https://api.brandwatch.com/projects/***REMOVED***/data/mentions"


def update_bw_sentiment(df, log_callback):
    cleaned_sentiment_dicts = prepare_data_for_bw(df)
    data = json.dumps(cleaned_sentiment_dicts)
    bw_request(data, log_callback)


def prepare_data_for_bw(df):
    df_bw = df.copy()
    df_bw["Sentiment"] = df_bw[
        "Sentiment"
    ].str.lower()  # Convert sent values to lowercase
    sentiment_dicts = (
        df_bw[["Query Id", "Resource Id", "Sentiment"]]
        .rename(
            columns={
                "Query Id": "queryId",
                "Resource Id": "resourceId",
                "Sentiment": "sentiment",
            }
        )
        .to_dict("records")
    )
    return sentiment_dicts


def bw_request(data, log_callback):
    headers = {}
    headers["Authorization"] = "Bearer {}".format(API_TOKEN)
    headers["Content-type"] = "application/json"

    response = requests.patch(URL, data=data, headers=headers)
    try:
        response.json()
    except ValueError as e:
        # handles non-json responses
        if "Expecting value: line 1 column 1 (char 0)" in str(e):
            error_message = "ERROR: There was an error with this request: \n{}".format(
                response.text
            )
            log_callback(error_message)
        else:
            error_message = "ERROR: An unexpected ValueError occurred: {}".format(e)
            log_callback(error_message)
    else:
        if "errors" in response.json() and response.json()["errors"]:
            error_message = "ERROR: There was an error with this request: \n{}".format(
                response.json()["errors"]
            )
            log_callback(error_message)
        else:
            success_message = "Successfully updated {} mentions.".format(
                len(response.json())
            )
            log_callback(success_message)
