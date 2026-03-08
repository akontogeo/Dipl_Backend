# main.py
# Entry point for the backend application
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import dataset, training, gaze, inference, analysis, video
from app.core.config import settings

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

# ΔΙΟΡΘΩΣΗ: Χρησιμοποιούμε το settings.OUTPUTS_DIR αντί για το σκέτο "outputs"
app.mount("/outputs", StaticFiles(directory=settings.OUTPUTS_DIR), name="outputs")

# Αν έχεις και άλλους φακέλους που θέλεις να σερβίρεις (π.χ. τα αποτελέσματα του training)
app.mount("/training_results", StaticFiles(directory=settings.TRAINING_RESULTS_DIR), name="training_results")

@app.get("/")
async def root():
    return {"message": "Welcome to the Attention Monitoring System"}
