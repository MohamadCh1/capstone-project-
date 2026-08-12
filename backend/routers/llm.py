from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from llama_cpp import Llama
from backend.utils import BASE_DIR
import os
from fastapi.responses import JSONResponse

MODEL_PATH = os.path.join(BASE_DIR,"..","models","diabetes_gguf")
router = APIRouter()
templates = Jinja2Templates(directory="templates")
llm = Llama(model_path=MODEL_PATH, verbose = False)

@router.get("/ask-ai")
async def ask_ai_page(request: Request):
    user = request.session.get("user")
    if not user:
        return templates.TemplateResponse("patient_login.html", {"request": request, "error": "Please log in to access the AI assistant."})
    return templates.TemplateResponse("ask_ai.html", {
        "request": request
    })

@router.post("/api/ask-ai")
async def ask_ai(message: str = Form(...)):
    prompt = f"""
    You are a medical AI assistant specialized in diabetes.
    Answer clearly, simply, and safely Just On the Diabetes Related Questions.
    You should not provide any information that is not related to diabetes. If the question is not related to diabetes, politely decline to answer and suggest asking a diabetes-related question instead but in a good beautiful way.
    reply to Hi and Hello with a nice greeting but also ask if they have any diabetes-related questions
    Diabetes Related question include lab test related to diabetes and diabetes symtomps 
    User: {message}
    AI:
    """

    output = llm(
        prompt,
        max_tokens=300,
        temperature=0.7,
        stop=["User:"]
    )

    ai_text = output["choices"][0]["text"].strip()

    return JSONResponse({
        "reply": ai_text
    })