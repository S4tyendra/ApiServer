from fastapi.responses import JSONResponse
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from functions.apiwrapper import api_key_auth, tokenconsuption

router = APIRouter()

genai.configure(api_key="AIzaSyDhHXRkHjTYBUV9crg_EZ8E-XbuNyl1YQU")

# Set up the model
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

model = genai.GenerativeModel(
    model_name="gemini-1.0-pro",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

class PromptData(BaseModel):
    new_prompt: str
    history: list = []

@router.post("/generate", dependencies=[Depends(api_key_auth)] )
async def generate(data: PromptData, request:Request):
    
    api_key = request.headers.get("X-API-KEY")
    try:
        new_prompt = data.new_prompt
        history = data.history
        if len(history) == 1:
            history = []
        convo = model.start_chat(history=history)
        convo.send_message(new_prompt)
        response_text = convo.last.text

        # Return the response as JSON
        return JSONResponse({"response": response_text})
    except Exception as e:
        print(e)
        if api_key:
            print("Returning tokens")
            await tokenconsuption(api_key, 2)
        return HTTPException(status_code=400, detail="Error occurred!")
    
    
