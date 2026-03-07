# main.py
# Entry point for the backend application
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import dataset, training, gaze, inference, analysis, video

app = FastAPI(title="Attention Monitoring API")

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Επιτρέπει όλα τα origins - για production περιόρισε σε συγκεκριμένα domains
    allow_credentials=True,
    allow_methods=["*"],  # Επιτρέπει όλες τις HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Επιτρέπει όλα τα headers
)

# Σύνδεση των Layers (Routes)
app.include_router(dataset.router, prefix="/dataset", tags=["Dataset"])
app.include_router(training.router, prefix="/training", tags=["Training"])
app.include_router(gaze.router, prefix="/gaze", tags=["Gaze"])
app.include_router(inference.router, prefix="/inference", tags=["Inference"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(video.router, prefix="/api", tags=["Video"])

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/")
async def root():
    return {"message": "Welcome to the Attention Monitoring System"}