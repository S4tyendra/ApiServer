from fastapi import APIRouter, Form
from pydantic import BaseModel
from starlette.responses import HTMLResponse, Response

router = APIRouter()

import requests


def get_pull_requests(user_name: str):
    data = []
    BASE_URL = "https://api.github.com"
    REPO = "S4tyendra/4thsemnotes"
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


@router.get("/list_pending_pulls")
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
    prompt = f"""
You're a friendly and helpful assistant tasked with creating comprehensive notes on various topics. Your notes should be concise, detailed, and easy to understand. Use Markdown to organize content effectively. Maintain a friendly tone throughout the notes and provide plenty of examples for each topic. Ensure clarity by breaking down each subtopic and providing clear explanations and examples.

---

    {data}


---

Hello, note maker! Let's dive into the details. Remember to keep your explanations concise yet informative. Utilize Markdown to structure the content effectively.I already shared you my basic notes above. Here's a breakdown of what's expected:

1. **Introduction**
       - Brief overview of the topic.
       - Importance and relevance.

2. **Main Content**
       - Subtopics explained in detail.
       - Use examples to clarify concepts.
       - Provide step-by-step explanations where necessary.

3. **Examples**
       - Showcase real-life scenarios.
       - Illustrate concepts with practical examples.

4. **Conclusion**
       - Summarize key points.
       - Reinforce understanding.

Remember to maintain a friendly and approachable tone throughout the notes. Let's get started!

    """
    rawData = generate_ai_content(prompt)
    return Response(content=rawData, media_type="text/plain")

