from fastapi import FastAPI

from .api.routes_runs import router as routes_runs
from .api.routes import router as prompts_router
from app.db.database import SessionLocal

app = FastAPI()

# include runs routes
app.include_router(routes_runs, prefix="/runs", tags=["Runs"])

# include prompts routes
app.include_router(prompts_router, prefix="/prompts", tags=["Prompts"])


@app.get("/")
def root():
    return {"message": "EdgeProbe backend is running"}


from app.services.llm_service import get_model_response

@app.get("/test-llm")
def test_llm():
    response = get_model_response("Explain gravity in one sentence")
    return {"response": response}