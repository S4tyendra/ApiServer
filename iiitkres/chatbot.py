import traceback
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from functions.apiwrapper import api_key_auth, refund_tokens, get_user

API_TOKEN = "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"
router = APIRouter()

class PromptData(BaseModel):
    history: list = []

def _generate_response(history):
    client = Groq(api_key=API_TOKEN)
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an AI tutor. You are helping a student. The student is asking you a question. You are answering the student's question, Don't answer any other questions that are unrelated to study. such as personal questions, etc.",
            },
            *history,
        ],
        temperature=0.5,
        max_tokens=8000,
        top_p=1,
        stream=True,
        stop=None,
    )

    for chunk in completion:
        try:
            content = chunk.choices[0].delta.content or ""
            print(content, end="")
            yield content
        except Exception:
            traceback.print_exc()

@router.post("/generate", dependencies=[Depends(lambda: api_key_auth(accept=["iiitk-android","iiitk-win-lin"], tokens=-1))])
async def generate(data: PromptData, request: Request):
    user = await get_user(request, accept=["iiitk-android","iiitk-win-lin"])
    try:
        return StreamingResponse(_generate_response(data.history))
    except Exception as e:
        await refund_tokens(user.get('email'), 1)
        raise HTTPException(status_code=400, detail=str(e))