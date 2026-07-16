from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from detector import analyze_image

ROOT = Path(__file__).parent
UPLOADS, RESULTS = ROOT / "uploads", ROOT / "results"
UPLOADS.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)
app = FastAPI(title="Veritas Deepfake Defence")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

ALLOWED = {"image/jpeg", "image/png", "image/webp"}
HISTORY: dict[str, dict] = {}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/results/{filename}")
def result_file(filename: str) -> FileResponse:
    path = RESULTS / Path(filename).name
    if not path.exists():
        raise HTTPException(404, "Result image not found")
    return FileResponse(path)


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Please upload a JPEG, PNG, or WebP image.")
    job_id = uuid.uuid4().hex
    suffix = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"
    destination = UPLOADS / f"{job_id}{suffix}"
    with destination.open("wb") as target:
        shutil.copyfileobj(file.file, target)
    try:
        analysis = analyze_image(destination, RESULTS)
    except Exception as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(422, "The uploaded file could not be read as an image.") from error
    payload = {"id": job_id, "original_url": f"/uploads/{destination.name}", "heatmap_url": f"/results/{analysis.pop('heatmap_file')}", **analysis}
    HISTORY[job_id] = payload
    return payload


@app.get("/api/results/{job_id}")
def get_result(job_id: str) -> dict:
    if job_id not in HISTORY:
        raise HTTPException(404, "Analysis was not found in this server session.")
    return HISTORY[job_id]


app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
