# Veritas — Deepfake Defence

An explainable, browser-based image-forensics dashboard. Upload a JPEG, PNG, or WebP image to inspect compression artifacts, metadata signals, texture variation, and lighting consistency.

> This is a heuristic forensic tool, not a trained deepfake classifier. Its results indicate signals that merit review; they do not prove that an image is authentic or manipulated.

## Features

- Drag-and-drop image upload dashboard with dark glassmorphism UI.
- Error Level Analysis (ELA) heatmap generated from JPEG recompression differences.
- EXIF metadata inspection and common editing-software signature checks.
- Texture, illumination, and compression concern metrics.
- Interactive original-versus-ELA comparison slider.
- JSON API for analyses and session-scoped result retrieval.

## Quick start

Prerequisites: Python 3.10 or newer.

```powershell
pip install -r requirements.txt
python main.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

To run with automatic reload while developing:

```powershell
uvicorn main:app --reload
```

## Use

1. Open the dashboard.
2. Drop in, or choose, a JPEG, PNG, or WebP image.
3. Review the concern score, individual forensic indicators, audit log, and ELA heatmap.
4. Drag across the comparison image to contrast the original with the heatmap.

The concern score is an aggregate of heuristic indicators. Higher values should prompt closer human review; they are not a probability that an image is fake.

## API

### `POST /api/analyze`

Accepts multipart form data with a `file` field. Supported media types are `image/jpeg`, `image/png`, and `image/webp`.

```powershell
curl.exe -F "file=@example.jpg" http://127.0.0.1:8000/api/analyze
```

The response includes the job ID, concern score, verdict, metrics, forensic alerts, uploaded-image URL, and ELA heatmap URL.

### `GET /api/results/{job_id}`

Returns the analysis from the active server session. Results are held in memory, so restarting the server clears this history.

## Project layout

```text
.
├── main.py                 # FastAPI app and endpoints
├── detector.py             # ELA, metadata, and image-statistical analysis
├── static/
│   ├── index.html          # Dashboard structure
│   ├── styles.css          # Dashboard styling
│   └── app.js              # Upload flow and result rendering
├── tests/test_detector.py  # Detector smoke test
└── requirements.txt
```

Uploaded images and generated heatmaps are written to `uploads/` and `results/`. Both are ignored by Git.

## Tests

```powershell
python -m pytest tests/test_detector.py -q
```

## Limitations and responsible use

- ELA is most meaningful for JPEG content. PNG and WebP uploads are converted through the analysis flow, so results should be interpreted carefully.
- Missing EXIF data is common and is not evidence of manipulation.
- Editing-software metadata may be absent even in edited files, and present in benign workflows.
- The application currently analyzes still images only. Video deepfake detection would require explicit frame extraction and a validated temporal/model-based pipeline.
- Do not use the score as the sole basis for moderation, identity verification, legal, employment, or other high-impact decisions.
