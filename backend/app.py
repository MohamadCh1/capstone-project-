from fastapi import FastAPI, HTTPException, Request,status
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from backend.routers import doctor, test, patient,dashboard, suggestion, llm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Agentic AI Healthcare System")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
templates = Jinja2Templates(directory="templates")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    current_path = request.scope.get("path")

    if current_path.startswith("/doctor/register"):
        template_name = "doctor_register.html"
    elif current_path.startswith("/patient/register"):
        template_name = "patient_register.html"
    else:
        template_name = "dashboard.html"  

    return templates.TemplateResponse(
        template_name,
        {"request": request, "error": "Please fill in all required fields correctly."},
        status_code=400
    )

@app.get("/home")
@app.get("/")
async def home_page(request: Request):
    request.session.clear()
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    return RedirectResponse(url="/home", status_code=302)

app.include_router(test.router)
app.include_router(dashboard.router)
app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(suggestion.router)
app.include_router(llm.router)