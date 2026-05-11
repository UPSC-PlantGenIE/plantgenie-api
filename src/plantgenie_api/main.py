from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from plantgenie_api.api.v1.routes import v1_router
from plantgenie_api.api.v2.routes import router as v2_router
from plantgenie_api.dependencies import lifespan

app = FastAPI(
    root_path="/api",
    title="UPSC PlantGenIE API",
    version="0.0.1",
    description="Backend for the PlantGenIE React Frontend",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Allow all origins (change this to specific origins in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router=v1_router)
app.include_router(router=v2_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the PlantGenIE API!"}
