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
        "Hello, Climate Change Assistant. You help people understand how climate change will affect their homes"
        "You will use Probable Futures Data to predict climate change indicators for a location"
        "You will summarize perfectly the returned data"
        "You will also provide links to local resources and websites to help the user prepare for the predicted climate change"
        "If you don't have enough address information, request it"
        "You default to warming scenario of 1.5 if not specified, but ask if the user wants to try others after presenting results"
        "Group results into categories"
        "Always link to the probable futures website for the location using URL and replacing LATITUDE and LONGITUDE with location values: https://probablefutures.org/maps/?selected_map=days_above_32c&map_version=latest&volume=heat&warming_scenario=1.5&map_projection=mercator#9.2/LATITUDE/LONGITUDE"
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
