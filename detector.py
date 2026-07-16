"""Lightweight, explainable image-forensics utilities.

These metrics flag visual manipulation signals; they do not identify a person or
replace a trained deepfake detector.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import uuid

import numpy as np
from PIL import ExifTags, Image, ImageChops, ImageFilter, ImageOps

EDITING_SIGNATURES = ("photoshop", "gimp", "lightroom", "canva", "snapseed", "affinity")


def _normalise(values: np.ndarray) -> np.ndarray:
    low, high = float(values.min()), float(values.max())
    if high - low < 1e-6:
        return np.zeros_like(values, dtype=np.uint8)
    return ((values - low) * 255.0 / (high - low)).clip(0, 255).astype(np.uint8)


def perform_ela(image_path: Path, result_dir: Path, quality: int = 90) -> tuple[Path, dict[str, float]]:
    """Create an Error Level Analysis heatmap and return its summary metrics."""
    with Image.open(image_path) as source:
        original = ImageOps.exif_transpose(source).convert("RGB")
    recompressed_path = result_dir / f"recompressed-{uuid.uuid4().hex}.jpg"
    original.save(recompressed_path, "JPEG", quality=quality, optimize=True)
    with Image.open(recompressed_path) as compressed:
        difference = ImageChops.difference(original, compressed.convert("RGB"))
    values = np.asarray(difference, dtype=np.float32).mean(axis=2)
    heat = Image.fromarray(_normalise(values), "L")
    heat = heat.filter(ImageFilter.GaussianBlur(radius=1.2))
    heatmap = ImageOps.colorize(heat, black="#060916", white="#ff3d71")
    heatmap_path = result_dir / f"ela-{uuid.uuid4().hex}.jpg"
    heatmap.save(heatmap_path, "JPEG", quality=92)
    recompressed_path.unlink(missing_ok=True)
    return heatmap_path, {"mean_error": round(float(values.mean()), 2), "peak_error": round(float(values.max()), 2)}


def analyze_metadata(image_path: Path) -> dict[str, Any]:
    with Image.open(image_path) as image:
        raw = image.getexif()
        exif = {ExifTags.TAGS.get(key, str(key)): str(value) for key, value in raw.items()}
        info = {str(key): str(value) for key, value in image.info.items() if isinstance(value, (str, int, float))}
    searchable = " ".join([*exif.values(), *info.values()]).lower()
    editors = [name.title() for name in EDITING_SIGNATURES if name in searchable]
    camera = exif.get("Model") or exif.get("Make")
    return {"camera": camera, "has_exif": bool(exif), "editing_software": editors, "fields": len(exif), "info": info}


def calculate_spoof_metrics(image_path: Path, ela: dict[str, float], metadata: dict[str, Any]) -> dict[str, int]:
    """Compute transparent image-statistical indicators on a 0-100 concern scale."""
    with Image.open(image_path) as image:
        pixels = np.asarray(ImageOps.exif_transpose(image).convert("RGB").resize((512, 512)), dtype=np.float32)
    gray = pixels.mean(axis=2)
    # Inconsistent high-frequency content often accompanies compositing/resampling.
    laplacian_proxy = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
    channel_spread = np.std(pixels.reshape(-1, 3), axis=0).mean()
    ela_score = min(100, int(ela["mean_error"] * 18 + ela["peak_error"] * 0.25))
    texture_score = min(100, int(laplacian_proxy * 1.7))
    lighting_score = min(100, int(abs(np.std(pixels[:, :, 0]) - np.std(pixels[:, :, 2])) * 2.2 + channel_spread * 0.25))
    metadata_score = 75 if metadata["editing_software"] else (42 if not metadata["has_exif"] else 12)
    return {"ela": ela_score, "texture": texture_score, "lighting": lighting_score, "metadata": metadata_score}


def analyze_image(image_path: Path, result_dir: Path) -> dict[str, Any]:
    result_dir.mkdir(parents=True, exist_ok=True)
    heatmap_path, ela = perform_ela(image_path, result_dir)
    metadata = analyze_metadata(image_path)
    metrics = calculate_spoof_metrics(image_path, ela, metadata)
    score = round(sum(metrics.values()) / len(metrics))
    verdict = "Likely manipulated" if score >= 60 else ("Review recommended" if score >= 35 else "No strong anomaly")
    alerts: list[dict[str, str]] = []
    if metrics["ela"] >= 55:
        alerts.append({"level": "warning", "text": "Elevated recompression differences detected in the ELA map."})
    if metadata["editing_software"]:
        alerts.append({"level": "warning", "text": f"Editing signature found: {', '.join(metadata['editing_software'])}."})
    elif not metadata["has_exif"]:
        alerts.append({"level": "info", "text": "No EXIF camera metadata was available."})
    if metrics["texture"] >= 55:
        alerts.append({"level": "info", "text": "Texture variation warrants a closer regional review."})
    if not alerts:
        alerts.append({"level": "success", "text": "No high-confidence forensic anomaly was found by these heuristic checks."})
    return {"score": score, "verdict": verdict, "metrics": metrics, "metadata": metadata, "ela": ela, "heatmap_file": heatmap_path.name, "alerts": alerts}
