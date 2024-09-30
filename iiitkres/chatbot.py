import traceback
from multiprocessing.connection import default_family

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from functions.apiwrapper import  refund_tokens, get_user, api_key_header
import random

groq_keys = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

router = APIRouter()


class PromptData(BaseModel):
    history: list = []


def _generate_response(history):
    client = Groq(api_key=random.choice(groq_keys))
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


@router.post("/generate")
async def generate(data: PromptData, request: Request):
    user = await get_user(request, accept=["iiitk-android", "iiitk-win-lin"], tokens=-1)
    try:
        return StreamingResponse(_generate_response(data.history))
    except Exception as e:
        await refund_tokens(user.get('email'), 1)
        raise HTTPException(status_code=400, detail=str(e))
