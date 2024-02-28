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
    get_pf_data_new = {
        "name": "get_pf_data_new",
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
        """,
    }

    get_current_datetime = {
        "name": "get_current_datetime",
        "parameters": {"type": "object", "properties": {}},
        "description": """
            This function returns the current date time. ALWAYS call this function is a user requests information for a relative date like 'recently', or 'this month'
        """,
    }

    instructions = """
        "Hello, Climate Change Assistant. You help people understand how climate change will affect their life in the future."
        "You will use the get_pf_data_new function to call the Probable Futures API to get data that describes predicted climate change indicators for a specific location in the future."
        "Once you have the data, you will call the get_pf_data_story function to turn it into images and word."
    """

    tools = [
        {
            "type": "function",
            "function": get_pf_data_new,
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
            name="Climate Change Assistant 4.0",
            instructions=instructions,
            tools=tools,
            model=model,
            # file_ids=[file.id]
        )
    except Exception:
        print("Creating assistant ...")
        assistant = await client.beta.assistants.create(
            name="Climate Change Assistant 4.0",
            instructions=instructions,
            tools=tools,
            model=model,
            # file_ids=[file.id]
        )
        print(assistant)
        print("Now save the DI in your .env file")
        # SAVE IT IN .env


asyncio.run(create())
