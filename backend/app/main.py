from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.llm_service import get_model_response

from .api.routes import router as prompts_router
from .api.routes_runs import router as routes_runs

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend's origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include runs routes
app.include_router(routes_runs, prefix="/runs", tags=["Runs"])

# include prompts routes
app.include_router(prompts_router, prefix="/prompts", tags=["Prompts"])


@app.get("/")
def root():
    return {"message": "EdgeProbe backend is running"}


@app.get("/test-llm")
def test_llm():
    response = get_model_response("Explain gravity in one sentence")
    return {"response": response}