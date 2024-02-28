import os
import json
import pandas as pd

import requests
from openai import OpenAI
from datetime import date
from datetime import datetime

from dotenv import load_dotenv
import sys

import io
import base64
import urllib
from PIL import Image

from diffusers import AutoPipelineForText2Image  # , AutoPipelineForImage2Image
import torch

import prompts as pr

pf_api_url = os.getenv("PF_API_URL")
pf_token_audience = os.getenv("PF_TOKEN_AUDIENCE")
pf_token_url = os.getenv("PF_TOKEN_URL")

load_dotenv()
client = OpenAI()

# pipeline_text2image = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.float16, variant="fp16")
# pipeline_text2image = pipeline_text2image.to("cuda")

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


def json_to_dataframe(json_data, address, country):
    # Extract the relevant part of the JSON data
    json_data = json.loads(json_data)
    data = json_data['data']['getDatasetStatistics']['datasetStatisticsResponses']
    # Convert to a DataFrame
    df = pd.DataFrame(data)
    # Normalize the 'info' column if needed
    if not df['info'].apply(lambda x: x == {}).all():
        info_df = pd.json_normalize(df['info'])
        df = df.drop(columns=['info']).join(info_df)
    df['address'] = address
    df['country'] = country
    df = df[['address', 'country', 'name', 'midValue', 'unit']]
    df = df[df['name'].str.contains('Change')]
    df = df[~(df['midValue'] == '0.0')]
    df.reset_index(drop=True, inplace=True)
    return df

def story_splitter(parsed_output):
    temperature_output = parsed_output[parsed_output.name.str.contains("nights|balance|dry hot")]
    water_output = parsed_output[parsed_output.name.str.contains("annual|wettest|frequency")]
    land_output = parsed_output[parsed_output.name.str.contains("drought|wildfire")]

    return temperature_output, water_output, land_output


def summary_completion(content):
    completion = client.chat.completions.create(
        model="gpt-4-0125-preview",  # gpt-4 #gpt-3.5-turbo-16k
        messages=[
            {"role": "system", "content": pr.summary_system_prompt},
            {"role": "user", "content": content}
        ],
        stream=True
    )

    return completion  # .choices[0].message.content


def story_completion(story_system_prompt, content):
    completion = client.chat.completions.create(
        model="gpt-4-0125-preview",  # gpt-4 #gpt-3.5-turbo-16k
        messages=[
            {"role": "system", "content": story_system_prompt},
            {"role": "user", "content": str(content.to_json())}
        ],
        stream=True
    )

    return completion  # .choices[0].message.content

# need GPU to run this part; uncomment lines 31 & 32
# def get_image_response_SDXL(prompt):
#     print('starting SDXL')
#     image = pipeline_text2image(prompt=prompt, guidance_scale=0.0, num_inference_steps=1).images[0]
#     buffer = io.BytesIO()
#     image.save(buffer, format='PNG')
#     image_bytes = buffer.getvalue()
#     return image_bytes


# dall-e-3 image completion version
def get_image_response(storyboard_prompt, prompt):
    print(storyboard_prompt + ' ' + '\nSTORY CHUNK:' + '\n' + prompt)
    response = client.images.generate(
        model="dall-e-3",
        prompt=storyboard_prompt + '\n---------' + '\nSTORY CHUNK:' + '\n' + prompt,  # "a white siamese cat"
        size="1024x1024",
        quality="standard",
        n=1,
    )

    return response.data[0].url

def get_pf_data_new(address, country, warming_scenario="2.0"):
    variables = {}

    location = f"""
        country: "{country}"
        address: "{address}"
    """

    query = ("""
            mutation {
                getDatasetStatistics(input: { """ + location + """ \
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
    """)
    print(query)

    access_token = get_pf_token()
    url = pf_api_url + "/graphql"
    headers = {"Authorization": "Bearer " + access_token}
    response = requests.post(
        url, json={"query": query, "variables": variables}, headers=headers
    )

    response = str(response.json()).replace("'", '"')

    parsed_output = json_to_dataframe(response, address=address, country=country)
    print("got output of pf_data_new")

    summary = summary_completion(str(address) + " " + str(country))

    return summary, parsed_output


def summarizer(content):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",  # gpt-4 # gpt-4-0125-preview
        messages=[
            {"role": "system", "content": pr.summarizer_prompt},
            {"role": "user", "content": content}
        ],
        stream=False
    )
    print(str(completion.choices[0].message.content) + " centered, ominous, eerie, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration")
    return str(completion.choices[0].message.content) + " centered, ominous, eerie, highly detailed, digital painting, artstation, concept art, smooth, sharp focus, illustration"
