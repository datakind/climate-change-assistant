import os
import json

import requests

from datetime import date
from datetime import datetime

from dotenv import load_dotenv
import sys

pf_api_url = "https://graphql.probablefutures.org"
pf_token_audience = "https://graphql.probablefutures.com"
pf_token_url = "https://probablefutures.us.auth0.com/oauth/token"

load_dotenv()


def convert_to_iso8601(date_str):
    try:
        # Parse the date string to a datetime object
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        # Format the datetime object to ISO 8601 format with timezone offset
        iso8601_date = date_obj.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        return iso8601_date
    except ValueError:
        # Return the original string if it's not in the expected date format
        return date_str


def get_current_datetime():
    return str(date.today())


def get_pf_token():
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    response = requests.post(
        pf_token_url,
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "audience": pf_token_audience,
            "grant_type": "client_credentials",
        },
    )
    access_token = response.json()["access_token"]
    return access_token


def get_pf_data(address, country, warming_scenario="1.5"):
    variables = {}

    location = f"""
        country: "{country}"
        address: "{address}"
    """

    query = (
        """
        mutation {
            getDatasetStatistics(input: { """
        + location
        + """ \
                    warmingScenario: \"""" + warming_scenario + """\"
                }) {
                datasetStatisticsResponses{
                    datasetId
                    midValue
                    name
                    unit
                    warmingScenario
                    latitude
                    longitude
                    info
                }
            }
        }
    """
    )
    print(query)

    access_token = get_pf_token()
    url = pf_api_url + "/graphql"
    headers = {"Authorization": "Bearer " + access_token}
    response = requests.post(
        url, json={"query": query, "variables": variables}, headers=headers
    )
    return str(response.json())
