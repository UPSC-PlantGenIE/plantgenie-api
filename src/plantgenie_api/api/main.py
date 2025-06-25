from fastapi import FastAPI

from plantgenie_api.api.v1.blast.routes import router as blast_router

app = FastAPI(root_path="/api")
app.include_router(blast_router)
