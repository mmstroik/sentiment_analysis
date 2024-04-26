import requests
import json


API_TOKEN = "***REMOVED***"
URL = "https://api.brandwatch.com/projects/***REMOVED***/data/mentions"


def update_bw_sentiment(df):
    updated_sentiment_dicts = prepare_data_for_bw(df)
    data = json.dumps(updated_sentiment_dicts)
    response = bw_request(data)
    return response


def prepare_data_for_bw(df):
    df_copy = df.copy()
    df_copy["Sentiment"] = df_copy[
        "Sentiment"
    ].str.lower()  # Convert sentiment values to lowercase
    sentiment_list = (
        df_copy[["Query Id", "Resource Id", "Sentiment"]]
        .rename(
            columns={
                "Query Id": "queryId",
                "Resource Id": "resourceId",
                "Sentiment": "sentiment",
            }
        )
        .to_dict("records")
    )

    return sentiment_list


def bw_request(data):
    headers = {}
    headers["Authorization"] = "Bearer {}".format(API_TOKEN)
    headers["Content-type"] = "application/json"

    response = requests.patch(URL, data=data, headers=headers)
    return response.json()
