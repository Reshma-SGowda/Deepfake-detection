from pathlib import Path
from PIL import Image
from detector import analyze_image


def test_analysis_creates_heatmap(tmp_path: Path):
    image_path = tmp_path / "sample.jpg"
    Image.new("RGB", (80, 80), "navy").save(image_path)
    result = analyze_image(image_path, tmp_path / "results")
    assert 0 <= result["score"] <= 100
    assert (tmp_path / "results" / result["heatmap_file"]).exists()
    assert set(result["metrics"]) == {"ela", "texture", "lighting", "metadata"}
