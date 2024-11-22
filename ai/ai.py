import ast
import traceback
from datetime import datetime

import anthropic
import icecream
from anthropic.types import ToolChoiceAutoParam
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Request
import asyncio, json, os

from pycparser.ply.ctokens import tokens
from pytz import timezone
from starlette.websockets import WebSocketState

from functions.add_to_logs import add_to_logs
from functions.apiwrapper import get_user, get_ws_user
from functions.db import get_database

router = APIRouter()

from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from anthropic import AnthropicBedrock



PROJECT_ID = "claude-433203"
REGION = "europe-west1"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
tools = [
        {
          "name": "get_weather",
          "description": "Get the current weather in a given location",
          "input_schema": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
              }
            },
            "required": ["location"]
          }
        }
      ]


# Add your tool implementation functions here
def calculator(operation, operand1, operand2):
    if operation == "add":
        return operand1 + operand2
    elif operation == "subtract":
        return operand1 - operand2
    elif operation == "multiply":
        return operand1 * operand2
    elif operation == "divide":
        if operand2 == 0:
            raise ValueError("Cannot divide by zero.")
        return operand1 / operand2
    else:
        raise ValueError(f"Unsupported operation: {operation}")


# Function to handle tool calls
async def handle_tool_call(tool_call):
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    if function_name == "calculator":
        result = calculator(**function_args)
        return json.dumps({"result": result})

    # Add more tool handlers as needed

    return json.dumps({"error": f"Unknown function: {function_name}"})
def get_anthropic_client():
   

    return AnthropicBedrock(
    # Authenticate by either providing the keys below or use the default AWS credential providers, such as
    # using ~/.aws/credentials or the "AWS_SECRET_ACCESS_KEY" and "AWS_ACCESS_KEY_ID" environment variables.
    aws_access_key="AKIA3FLD4F7FPLAOONWM",
    aws_secret_key="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",
    # Temporary credentials can be used with aws_session_token.
    # Read more at https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html.
    # aws_region changes the aws region to which the request is made. By default, we read AWS_REGION,
    # and if that's not present, we default to us-east-1. Note that we do not read ~/.aws/config for the region.
    aws_region="us-west-2",
)

g_system_prompt = """You're a friendly AI who keeps things short and sweet. When someone asks for help:

- Keep responses brief but helpful
- Use casual language, but stay professional
- Add occasional emojis for personality (1-2 max)
- Be helpful but encourage learning
- For code requests, guide rather than giving full solutions
- Keep explanations under 2-3 sentences when possible

Tone examples:
"Looks like you're missing a semicolon there! 👀"
"Hmm, what have you tried so far?"
"That's a cool project idea! Start with..."
"The error's coming from line 42 - any guess why?"

For coding help:
- Point to documentation
- Share small snippets, not full solutions
- Encourage problem-solving

Keep it natural but professional - no excessive slang or memes."""

@router.websocket("/chat")
async def websocket_chat_endpoint(websocket: WebSocket, token):
    user = await get_ws_user(websocket, accept=["ai"], token=token)
    input_tokens = 0
    output_tokens = 0
    err = False
    if user:
        await websocket.accept()
        print("WebSocket connection accepted")
        try:
            while True:  # Main connection loop
                try:
                    # await websocket.accept()
                    # Receive the message data from client
                    data = await websocket.receive_text()

                    # Check for stop command
                    if data.lower() == "stop":
                        print("Stop command received")
                        break  # Exit the main loop instead of closing immediately

                    # Parse the incoming data
                    request_data = json.loads(data)
                    messages = request_data.get("messages", [])
                    temperature = request_data.get("temperature", 0.7)
                    system_prompt = request_data.get("prompt", "")

                    # Initialize Anthropic client
                    client = get_anthropic_client()

                    # Create streaming response
                    try:
                        with client.messages.stream(
                            max_tokens=8192,
                            messages=messages,
                            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
                            temperature=temperature,
                            system=f"{g_system_prompt}\n\nAlso, user instructions are: {system_prompt}"
                        ) as stream:
                            for event in stream:
                                if hasattr(event, 'type'):
                                    # Convert the event to a dict for JSON serialization
                                    event_dict = {
                                        "type": event.type
                                    }

                                    # Handle different event types
                                    if event.type == "message_start":
                                        event_dict["message"] = event.message.model_dump()
                                        input_tokens += int(event.message.usage.input_tokens)
                                        output_tokens += int(event.message.usage.output_tokens)
                                    elif event.type == "content_block_delta":
                                        event_dict["index"] = event.index
                                        event_dict["delta"] = {
                                            "type": event.delta.type,
                                            "text": event.delta.text if hasattr(event.delta, 'text') else None
                                        }
                                    elif event.type == "content_block_start":
                                        event_dict["index"] = event.index
                                        event_dict["content_block"] = event.content_block.model_dump()
                                    elif event.type == "content_block_stop":
                                        event_dict["index"] = event.index
                                    elif event.type == "message_delta":
                                        output_tokens += int(event.usage.output_tokens)
                                        event_dict["delta"] = event.delta.model_dump()
                                        if hasattr(event, 'usage'):
                                            event_dict["usage"] = event.usage.model_dump()

                                    await websocket.send_json({
                                        "event": event.type,
                                        "data": event_dict
                                    })

                                    # Check for stop command (with a very short timeout)
                                    try:
                                        stop_check = await asyncio.wait_for(
                                            websocket.receive_text(),
                                            timeout=0.0001
                                        )
                                        if stop_check.lower() == "stop":
                                            print("Stop command received during stream")
                                            break  # Break the stream loop
                                    except asyncio.TimeoutError:
                                        pass
                            try:
                                if stop_check.lower() == "stop":
                                    break  # Exit the main loop if stop was received
                            except UnboundLocalError:
                                continue
                    except anthropic.APIStatusError as e:
                        await websocket.send_json(ast.literal_eval(str(e.message)))
                        await websocket.close()
                        err = True

                except WebSocketDisconnect:
                    print("WebSocket disconnected")
                    break
                except json.JSONDecodeError:
                    print("Invalid JSON received")
                    await websocket.send_json({
                        "event": "error",
                        "data": {
                            "type": "error",
                            "error": {
                                "type": "invalid_json",
                                "message": "Invalid JSON received"
                            }
                        }
                    })
                except Exception as e:
                    print(f"Error in processing request: {str(e)}")
                    error_message = {
                        "event": "error",
                        "data": {
                            "type": "error",
                            "error": {
                                "type": "stream_error",
                                "message": str(e)
                            }
                        }
                    }
                    await websocket.send_json(error_message)
                    traceback.print_exc()

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            traceback.print_exc()
        finally:
            # Log the total token usage at the end
            await add_to_logs(
                session=token,
                email=user["email"],
                message=f"AI usage: Input tokens: {input_tokens}, Output tokens: {output_tokens}" if not err else "AI usage: Error, Overloaded",
                app="ai",
                timestamp=datetime.now(tz=timezone('Asia/Kolkata')).timestamp(),
                cost=0
            )
            try:
                if not websocket.client_state == WebSocketState.DISCONNECTED:
                    await websocket.close()
            except RuntimeError:
                pass
            print("WebSocket connection closed")


# @router.websocket("/chat")
# async def websocket_chat_endpoint(websocket: WebSocket, token):
#     user = await get_ws_user(websocket, accept=["ai"], token=token)
#     input_tokens = 0
#     output_tokens = 0
#     err = False
#     if user:
#         await websocket.accept()
#         print("WebSocket connection accepted")
#         try:
#             while True:  # Main connection loop
#                 try:
#                     # Receive the message data from client
#                     data = await websocket.receive_text()
#
#                     # Check for stop command
#                     if data.lower() == "stop":
#                         print("Stop command received")
#                         break
#
#                     # Parse the incoming data
#                     request_data = json.loads(data)
#                     messages = request_data.get("messages", [])
#                     temperature = request_data.get("temperature", 0.7)
#                     system_prompt = request_data.get("prompt", "")
#                     icecream.ic(messages, temperature, system_prompt)
#
#                     # Initialize Anthropic client
#                     client = get_anthropic_client()
#
#                     # Create streaming response
#                     try:
#                         with client.messages.stream(
#                             max_tokens=8192,
#                             messages=messages,
#                             model="claude-3-5-sonnet@20240620",
#                             temperature=temperature,
#                             system=system_prompt,
#                             tools=tools,
#                         ) as stream:
#                             for event in stream:
#                                 if hasattr(event, 'type'):
#                                     # Convert the event to a dict for JSON serialization
#                                     event_dict = {
#                                         "type": event.type
#                                     }
#
#                                     # Handle different event types
#                                     if event.type == "message_start":
#                                         event_dict["message"] = event.message.model_dump()
#                                         input_tokens += int(event.message.usage.input_tokens)
#                                         output_tokens += int(event.message.usage.output_tokens)
#                                     elif event.type == "content_block_delta":
#                                         event_dict["index"] = event.index
#                                         event_dict["delta"] = {
#                                             "type": event.delta.type,
#                                             "text": event.delta.text if hasattr(event.delta, 'text') else None
#                                         }
#                                     elif event.type == "content_block_start":
#                                         event_dict["index"] = event.index
#                                         event_dict["content_block"] = event.content_block.model_dump()
#                                     elif event.type == "content_block_stop":
#                                         event_dict["index"] = event.index
#                                     elif event.type == "message_delta":
#                                         output_tokens += int(event.usage.output_tokens)
#                                         event_dict["delta"] = event.delta.model_dump()
#                                         if hasattr(event, 'usage'):
#                                             event_dict["usage"] = event.usage.model_dump()
#                                     elif event.type == "tool_use":
#                                         # Handle tool use event
#                                         tool_call = event.tool_use
#                                         tool_result = await handle_tool_call(tool_call)
#                                         event_dict["tool_use"] = {
#                                             "id": tool_call.id,
#                                             "name": tool_call.function.name,
#                                             "arguments": tool_call.function.arguments,
#                                             "result": tool_result
#                                         }
#
#                                     await websocket.send_json({
#                                         "event": event.type,
#                                         "data": event_dict
#                                     })
#
#                                     # Check for stop command (with a very short timeout)
#                                     try:
#                                         stop_check = await asyncio.wait_for(
#                                             websocket.receive_text(),
#                                             timeout=0.0001
#                                         )
#                                         if stop_check.lower() == "stop":
#                                             print("Stop command received during stream")
#                                             break  # Break the stream loop
#                                     except asyncio.TimeoutError:
#                                         pass
#                             try:
#                                 if stop_check.lower() == "stop":
#                                     break  # Exit the main loop if stop was received
#                             except UnboundLocalError:
#                                 continue
#                     except anthropic.APIStatusError as e:
#                         await websocket.send_json(ast.literal_eval(str(e.message)))
#                         await websocket.close()
#                         err = True
#
#                 except WebSocketDisconnect:
#                     print("WebSocket disconnected")
#                     break
#                 except json.JSONDecodeError:
#                     print("Invalid JSON received")
#                     await websocket.send_json({
#                         "event": "error",
#                         "data": {
#                             "type": "error",
#                             "error": {
#                                 "type": "invalid_json",
#                                 "message": "Invalid JSON received"
#                             }
#                         }
#                     })
#                 except Exception as e:
#                     print(f"Error in processing request: {str(e)}")
#                     error_message = {
#                         "event": "error",
#                         "data": {
#                             "type": "error",
#                             "error": {
#                                 "type": "stream_error",
#                                 "message": str(e)
#                             }
#                         }
#                     }
#                     await websocket.send_json(error_message)
#                     traceback.print_exc()
#
#         except Exception as e:
#             print(f"Unexpected error: {str(e)}")
#             traceback.print_exc()
#         finally:
#             # Log the total token usage at the end
#             await add_to_logs(
#                 session=token,
#                 email=user["email"],
#                 message=f"AI usage: Input tokens: {input_tokens}, Output tokens: {output_tokens}" if not err else "AI usage: Error, Overloaded",
#                 app="ai",
#                 timestamp=datetime.now(tz=timezone('Asia/Kolkata')).timestamp(),
#                 cost=0
#             )
#             try:
#                 if not websocket.client_state == WebSocketState.DISCONNECTED:
#                     await websocket.close()
#             except RuntimeError:
#                 pass
#             print("WebSocket connection closed")