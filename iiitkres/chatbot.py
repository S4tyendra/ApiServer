# import google.generativeai as genai
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request

from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from groq import Groq
from functions.apiwrapper import iiitk_auth, tokenconsuption
API_TOKEN = "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"
router = APIRouter()

# genai.configure(api_key="AIzaSyDhHXRkHjTYBUV9crg_EZ8E-XbuNyl1YQU")

# Set up the model
# generation_config = {
#     "temperature": 0.7,
#     "top_p": 1,
#     "top_k": 1,
#     "max_output_tokens": 2048,
# }
#
# safety_settings = [
#     {
#         "category": "HARM_CATEGORY_HARASSMENT",
#         "threshold": "BLOCK_NONE",
#     },
#     {
#         "category": "HARM_CATEGORY_HATE_SPEECH",
#         "threshold": "BLOCK_NONE",
#     },
#     {
#         "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#         "threshold": "BLOCK_NONE",
#     },
#     {
#         "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#         "threshold": "BLOCK_NONE",
#     },
# ]
#
# model = genai.GenerativeModel(
#     model_name="gemini-1.0-pro",
#     generation_config=generation_config,
#     safety_settings=safety_settings,
# )

def _generate_response(history):
    client = Groq(
        api_key=API_TOKEN
    )
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an AI tutor. You are helping a student. The student is asking you a question. You are answering the student's question, Don't answer any other questions that are unrelated to study. such as personal questions, etc.",
            },
            *history,
        ],
        temperature=1,
        max_tokens=32768,
        top_p=1,
        stream=True,
        stop=None,
    )

    for chunk in completion:
        print (chunk.choices[0].delta.content or "", end="")
        try:
            yield chunk.choices[0].delta.content or ""
        except:
            traceback.print_exc()
            pass



class PromptData(BaseModel):
    history: list = []


@router.post("/generate", dependencies=[Depends(iiitk_auth)])
async def generate(data: PromptData, request: Request):
    api_key = request.headers.get("X-API-KEY")
    try:

        history = data.history
        return StreamingResponse(_generate_response(history))

        # return JSONResponse({"response": response_text})
    except Exception as e:
        print(e)
        # if api_key:
        #     print("Returning tokens")
        #     await tokenconsuption(api_key, 2)
        return HTTPException(status_code=400, detail="Error occurred!")
