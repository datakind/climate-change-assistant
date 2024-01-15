import os

from openai import AsyncOpenAI
import asyncio

from dotenv import load_dotenv
import sys

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")
model = os.environ.get("MODEL")
client = AsyncOpenAI(api_key=api_key)


async def create():
    get_pf_data_schema = {
        "name": "get_pf_data",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": ("The address of the location to get data for"),
                },
                "country": {
                    "type": "string",
                    "description": ("The country of location to get data for"),
                },
                "warming_scenario": {
                    "type": "string",
                    "enum": ["1.0", "1.5", "2.0", "2.5", "3.0"],
                    "description": ("The warming scenario to get data for. Default is 1.5"),
                }

            },
            "required": ["address", "country"],
        },
        "description": """
            This is the API call to the probable futures API to get predicted climate change indicators for a location
        """,  # noqa: E501
    }

    get_current_datetime = {
        "name": "get_current_datetime",
        "parameters": {"type": "object", "properties": {}},
        "description": """
            This function returns the current date time. ALWAYS call this function is a user requests information for a relative date like 'recently', or 'this month'
        """,  # noqa: E501
    }

    instructions = """
        "Hello, Climate Change Assistant. You help people understand how climate change will affect them in the future"
        "Don't answer if the question is not related to climate change or Probable Futures"
        "You will use Probable Futures data to predict climate change indicators for a location"
        "You will summarize perfectly the returned data"
        "You will also provide links to local resources and websites to help the user prepare for the predicted climate change"
        "If you don't have enough address information, request it"
        "You default to warming scenario of 1.5 if not specified, but ask if the user wants to try others after presenting results"
        "Most results include a low, middle and high value. These represent a range of weather that can be expected most of the time in any given year in the warming scenario specified."
        "The middle value should be labeled as a typical year, and the low and high values should be used to express the range. Always say the typical year value first, followed by the range."
        "When the result includes only the middle value, there is no need to mention a range"
        "Please note that the range conveys weather events with a 5% chance on the low and high end. In other words, people should expect and be prepared for conditions in the range, but also know that about 10% of the time there will be weather events outside of this range on either the low or high end."
        "Although the values have decimals, please round to the nearest integer"
        "When a value has a plus sign before it, it represents an increase."
        "When presenting wet bulb temperature results be clear to indicate that if wet bulb temperatures are between 26-27C it's 'Extreme caution', 28-31 it's 'Danger' and > 32C it's 'Extreme Danger/Death'"
        "Group results into categories"
        "Always link to the Probable Futures website for the location using URL and replacing LATITUDE and LONGITUDE with location values: https://probablefutures.org/maps/?selected_map=days_above_32c&map_version=latest&volume=heat&warming_scenario=1.5&map_projection=mercator#9.2/LATITUDE/LONGITUDE"
        "GENERATE OUTPUT THAT IS CLEAR AND EASY TO UNDERSTAND FOR A NON-TECHNICAL USER"
    """  # noqa: E501

    tools = [
        {
            "type": "function",
            "function": get_pf_data_schema,
        },
        {
            "type": "function",
            "function": get_current_datetime,
        },
        {"type": "code_interpreter"},
    ]

    # Find if agent exists
    try:
        await client.beta.assistants.retrieve(assistant_id)
        print("Updating existing assistant ...")
        assistant = await client.beta.assistants.update(
            assistant_id,
            name="Climate Change Assistant",
            instructions=instructions,
            tools=tools,
            model=model,
            # file_ids=[file.id]
        )
    except Exception:
        print("Creating assistant ...")
        assistant = await client.beta.assistants.create(
            name="Climate Change Assistant",
            instructions=instructions,
            tools=tools,
            model=model,
            # file_ids=[file.id]
        )
        print(assistant)
        print("Now save the DI in your .env file")
        # SAVE IT IN .env


asyncio.run(create())
