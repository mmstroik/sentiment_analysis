import requests
import json
import pandas as pd
import logging


API_TOKEN = "1536f504-8ec2-4bbf-bee6-4ee58e3c5308"
URL = "https://api.brandwatch.com/projects/1998281989/data/mentions"

TEST_FILE = "1499apitest.xlsx"

logger = logging.getLogger(__name__)


def update_bw_sentiment(df):
    updated_sentiment_dicts = prepare_data_for_bw(df)
    data = json.dumps(updated_sentiment_dicts)
    response = bw_request(data)
    if "errors" in response:
        raise KeyError("patch failed", response)

    logger.info("{} mentions updated".format(len(response)))


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
    try:
        response.json()
    except ValueError as e:
        # handles non-json responses (e.g. HTTP 404, 500, 502, 503, 504)
        if "Expecting value: line 1 column 1 (char 0)" in str(e):
            logger.error(
                "There was an error with this request: \n{}\n{}\n{}".format(
                    response.url, data, response.text
                )
            )
            raise RuntimeError(response.text)
        else:
            raise
    else:
        if "errors" in response.json() and response.json()["errors"]:
            logger.error(
                "There was an error with this request: \n{}\n{}\n{}".format(
                    response.url, data, response.json()["errors"]
                )
            )
            logger.error(response)
            raise RuntimeError(response.json())

    logger.debug(response.url)
    return response.json()

df = pd.read_excel(TEST_FILE)
update_bw_sentiment(df)