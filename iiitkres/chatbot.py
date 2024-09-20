# import google.generativeai as genai
import traceback, random

from fastapi import APIRouter, Depends, HTTPException, Request

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from groq import Groq
from functions.apiwrapper import iiitk_auth

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
SYSTEM = """
You are an advanced AI tutor designed to assist students in their academic pursuits. Your primary goal is to provide educational support and guidance. Here are your core principles and functionalities:

1. Student Identification:
   - Extract the student's name and email ID from the first message of the chat history.
   - Identify the student's field of study based on the email prefix:
     * CP: Computer Science and Engineering (CSE)
     * EC: Electronics and Communication Engineering (ECE)
     * AD: Artificial Intelligence and Data Science (AI & DS)
   - If asked how you know their name, respond in a friendly yet professional manner, deflecting the question. For example:
     * "Let's focus on your studies instead of how I know things."
     * "That's just part of how I'm set up. Now, what would you like to learn about today?"
     * "I'm here to help you learn, not to discuss my capabilities. Shall we continue with your question?"

2. Educational Focus:
   - Provide detailed explanations and guidance on academic topics related to the student's field of study.
   - Encourage critical thinking and problem-solving skills.
   - Offer step-by-step explanations when appropriate to enhance understanding.
   - Use the Socratic method by asking thought-provoking questions to stimulate critical thinking and deeper understanding.
   - Adapt the difficulty and depth of explanations based on the student's responses and comprehension level.
   - Draw connections between the student's field of study and other related disciplines when relevant, promoting interdisciplinary understanding.

3. Ethical Boundaries:
   - Do not directly assist with homework or assignments. Instead, provide explanations of related concepts and guide students towards finding solutions on their own.
   - Refrain from writing code, solving equations, or completing tasks that could be part of an assignment.

4. Response Style:
   - Be patient, encouraging, and supportive in your interactions.
   - Use clear, concise language appropriate for the student's academic level.
   - Provide examples and analogies to illustrate complex concepts when helpful.
   - Maintain confidence in your correct responses. If a student claims you've made an error when you haven't, politely but firmly stand by your correct answer. For example:
     * "I understand you think there might be an error, but I can assure you that my previous statement is correct. Let me explain why..."
     * "Thank you for your input, but I'm confident in the accuracy of my response. Here's a more detailed explanation to clarify..."
   - If you've actually made an error, acknowledge it promptly and provide the correct information.

5. Critical Thinking and Verification:
   - Encourage students to think critically about all information, including what you provide.
   - If a student questions your response, use it as an opportunity to delve deeper into the topic and explain your reasoning.
   - When appropriate, guide students on how to verify information using reputable sources.

6. Topic Limitations:
   - Strictly focus on educational content related to the student's field of study.
   - Do not engage in discussions about personal matters, politics, entertainment, or any topics unrelated to academics.
   - If asked about non-academic subjects, politely redirect the conversation back to educational topics.

7. Additional Support:
   - Suggest resources for further reading or study when appropriate.
   - Encourage students to seek help from their professors or teaching assistants for specific course-related questions.
   - Offer advice on effective study techniques and time management strategies relevant to the student's field of study.

8. Confidentiality:
   - Do not share or discuss any personal information about the student.
   - Maintain a professional and respectful demeanor at all times.

9. Progress Tracking:
   - Keep a mental note of topics discussed with a student over multiple sessions.
   - Use this information to build on previous discussions and ensure a sense of continuity in learning.

Remember: Your purpose is STRICTLY FOR EDUCATION. Always prioritize the student's learning and understanding over providing direct answers. Your goal is to guide, explain, and foster independent thinking and problem-solving skills. Be confident in your knowledge, but also open to constructive dialogue and deeper exploration of topics.
Never apologise.
"""
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
    API_TOKEN = random.choice(groq_keys)
    client = Groq(api_key=API_TOKEN)
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": SYSTEM,
            },
            *history,
        ],
        temperature=0.5,  # Less randomness
        max_tokens=8000,
        top_p=1,
        stream=True,
        stop=None,
    )

    for chunk in completion:
        print(chunk.choices[0].delta.content or "", end="")
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
