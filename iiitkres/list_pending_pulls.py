from fastapi import APIRouter, Depends, Form
from starlette.responses import Response

from functions.apiwrapper import iiitk_auth

router = APIRouter()

import requests


def get_pull_requests(user_name: str):
    data = []
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/NOTES-res"
    TOKEN = "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"
    headers = {"Authorization": f"token {TOKEN}"}

    response = requests.get(
        f"{BASE_URL}/repos/{REPO}/pulls",
        headers=headers,
    )
    if response.status_code == 200:
        pull_requests = response.json()
        for pr in pull_requests:
            name = pr['head']['ref'].split('-')[0]
            if str(name).lower() == str(user_name).lower():
                branch_name = pr['head']['ref']
                description = pr['title']
                data.append(
                    {"Branch Name": branch_name,
                     "Description": description})
    return data


@router.get("/list_pending_pulls", dependencies=[Depends(iiitk_auth)])
async def list_pending_pulls(user_id: str):
    return get_pull_requests(user_id)


"""
At the command line, only need to run once to install the package via pip:

$ pip install google-generativeai
"""


def generate_ai_content(prompt):
    import google.generativeai as genai

    genai.configure(api_key="AIzaSyDhHXRkHjTYBUV9crg_EZ8E-XbuNyl1YQU")

    # Set up the model
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

    model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)

    convo = model.start_chat(history=[])

    convo.send_message(prompt)
    return convo.last.text


@router.post("/generate_ai_content")
async def _generate_ai_content(
        data: str = Form(...)
):
    # rawData = generate_ai_content(prompt)
    return Response(content="rawData", media_type="text/plain")
