from fastapi import FastAPI
from routers.health import router as health_router
from routers.transcriptions import router as transcriptions_router

app = FastAPI(
    title="Mindvox",
    description="An AI-powered framework for personalized learning and development.",
    version="1.0.0",
    contact={
        "name": "Adalberto Tenório Batista",
        "url": "https://github.com/b-e-t-o/Mindvox.git",
        "email": "improprio.leghorn0m@icloud.com",
    },
)

app.include_router(health_router)
app.include_router(transcriptions_router)
