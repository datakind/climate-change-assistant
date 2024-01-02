import os
import json
from typing import Dict

from openai import AsyncOpenAI
from openai.types.beta import Thread
from openai.types.beta.threads import (
    MessageContentImageFile,
    MessageContentText,
    ThreadMessage,
)
import chainlit as cl
from typing import Optional
from chainlit.context import context

import assistant_tools as at

api_key = os.environ.get("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=api_key)
assistant_id = os.environ.get("ASSISTANT_ID")


class DictToObject:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)


async def process_thread_message(
    message_references: Dict[str, cl.Message], thread_message: ThreadMessage
):
    for idx, content_message in enumerate(thread_message.content):
        id = thread_message.id + str(idx)
        if isinstance(content_message, MessageContentText):
            if id in message_references:
                msg = message_references[id]
                msg.content = content_message.text.value
                await msg.update()
            else:
                message_references[id] = cl.Message(
                    author=thread_message.role, content=content_message.text.value
                )
                await message_references[id].send()
        elif isinstance(content_message, MessageContentImageFile):
            image_id = content_message.image_file.file_id
            response = await client.files.with_raw_response.retrieve_content(image_id)
            elements = [
                cl.Image(
                    name=image_id,
                    content=response.content,
                    display="inline",
                    size="large",
                ),
            ]

            if id not in message_references:
                message_references[id] = cl.Message(
                    author=thread_message.role,
                    content="",
                    elements=elements,
                )
                await message_references[id].send()
        else:
            print("unknown message type", type(content_message))


@cl.on_chat_start
async def start_chat():
    thread = await client.beta.threads.create()
    cl.user_session.set("thread", thread)
    await cl.Message(
        author="assistant",
        content="Hi! I'm your climate change assistant to help you prepare. "
                "What location are you interested in?"
    ).send()


@cl.on_message
async def run_conversation(message_from_ui: cl.Message):
    thread = cl.user_session.get("thread")  # type: Thread
    # Add the message to the thread
    await client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=message_from_ui.content
    )

    # Send empty message to display the loader
    loader_msg = cl.Message(author="assistant", content="")
    await loader_msg.send()

    # Create the run
    run = await client.beta.threads.runs.create(
        thread_id=thread.id, assistant_id=assistant_id
    )

    message_references = {}  # type: Dict[str, cl.Message]

    # Periodically check for updates
    while True:
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        )

        # Fetch the run steps
        run_steps = await client.beta.threads.runs.steps.list(
            thread_id=thread.id, run_id=run.id, order="asc"
        )

        for step in run_steps.data:
            # Fetch step details
            run_step = await client.beta.threads.runs.steps.retrieve(
                thread_id=thread.id, run_id=run.id, step_id=step.id
            )
            step_details = run_step.step_details
            # Update step content in the Chainlit UI
            if step_details.type == "message_creation":
                thread_message = await client.beta.threads.messages.retrieve(
                    message_id=step_details.message_creation.message_id,
                    thread_id=thread.id,
                )
                await process_thread_message(message_references, thread_message)

            if step_details.type == "tool_calls":
                for tool_call in step_details.tool_calls:
                    # IF tool call is a disctionary, convert to object
                    if isinstance(tool_call, dict):
                        print(tool_call)
                        tool_call = DictToObject(tool_call)
                        if tool_call.type == "function":
                            function = DictToObject(tool_call.function)
                            tool_call.function = function
                        if tool_call.type == "code_interpreter":
                            code_interpretor = DictToObject(tool_call.code_interpretor)
                            tool_call.code_interpretor = code_interpretor

                    print(step_details)
                    print(tool_call)
                    if tool_call.type == "code_interpreter":
                        if tool_call.id not in message_references:
                            message_references[tool_call.id] = cl.Message(
                                author=tool_call.type,
                                content=tool_call.code_interpreter.input
                                or "# Generating code...",
                                language="python",
                                parent_id=context.session.root_message.id,
                            )
                            await message_references[tool_call.id].send()
                        else:
                            message_references[tool_call.id].content = (
                                tool_call.code_interpreter.input
                                or "# Generating code..."
                            )
                            await message_references[tool_call.id].update()

                        tool_output_id = tool_call.id + "output"

                        if tool_output_id not in message_references:
                            message_references[tool_output_id] = cl.Message(
                                author=f"{tool_call.type}_result",
                                content=str(tool_call.code_interpreter.outputs) or "",
                                language="json",
                                parent_id=context.session.root_message.id,
                            )
                            await message_references[tool_output_id].send()
                        else:
                            message_references[tool_output_id].content = (
                                str(tool_call.code_interpreter.outputs) or ""
                            )
                            await message_references[tool_output_id].update()
                    elif tool_call.type == "retrieval":
                        if tool_call.id not in message_references:
                            message_references[tool_call.id] = cl.Message(
                                author=tool_call.type,
                                content="Retrieving information",
                                parent_id=context.session.root_message.id,
                            )
                            await message_references[tool_call.id].send()
                    # Note that this assumes some arguments due to some bug with early assistants
                    # and chainlit so be careful for functions that don't have mandatory parameters
                    elif (
                        tool_call.type == "function"
                        and len(tool_call.function.arguments) > 0
                    ):
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        if tool_call.id not in message_references:
                            message_references[tool_call.id] = cl.Message(
                                author=function_name,
                                content=function_args,
                                language="json",
                                parent_id=context.session.root_message.id,
                            )
                            await message_references[tool_call.id].send()

                            function_mappings = {
                                "get_pf_data": at.get_pf_data,
                                "get_current_datetime": at.get_current_datetime,
                            }

                            # Not sure why, but sometimes this is returned rather than name
                            function_name = function_name.replace("_schema", "")

                            print(f"FUNCTION NAME: {function_name}")
                            print(function_args)

                            output = function_mappings[function_name](**function_args)

                            await client.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread.id,
                                run_id=run.id,
                                tool_outputs=[
                                    {
                                        "tool_call_id": tool_call.id,
                                        "output": output,
                                    },
                                ],
                            )

        await cl.sleep(1)  # Refresh every second

        print(f"RUN STATUS: {run.status}")
        if run.status in ["cancelled", "failed", "completed", "expired"]:
            break


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_app_user: cl.AppUser
) -> Optional[cl.AppUser]:
    return default_app_user
