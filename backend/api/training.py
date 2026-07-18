"""API routes for training results and model management."""
import glob
import json
import os
from datetime import datetime

from fastapi import APIRouter

from core.config import settings

router = APIRouter(tags=["training"])

DATA_DIR = settings.data_dir
RESULTS_DIR = os.path.join(DATA_DIR, "results")
MODELS_DIR = os.path.join(DATA_DIR, "models")


@router.get("/training/results")
async def list_training_results(limit: int = 20):
    """List all training result files, newest first."""
    if not os.path.isdir(RESULTS_DIR):
        return {"results": [], "total": 0}

    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")), key=os.path.getmtime, reverse=True)
    files = files[:limit]

    results = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                data["filename"] = os.path.basename(f)
                results.append(data)
        except Exception:
            continue

    return {"results": results, "total": len(results)}


@router.get("/training/results/{filename}")
async def get_training_result(filename: str):
    """Get a specific training result by filename."""
    filepath = os.path.join(RESULTS_DIR, filename)
    if not os.path.isfile(filepath):
        return {"error": "Result not found"}

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/training/models")
async def list_trained_models():
    """List all saved model files."""
    if not os.path.isdir(MODELS_DIR):
        return {"models": [], "total": 0}

    models = []
    for f in os.listdir(MODELS_DIR):
        filepath = os.path.join(MODELS_DIR, f)
        if os.path.isfile(filepath):
            stat = os.stat(filepath)
            models.append({
                "filename": f,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    models.sort(key=lambda x: x["modified"], reverse=True)
    return {"models": models, "total": len(models)}


@router.get("/training/comparisons")
async def list_comparisons():
    """List all comparison CSV files."""
    if not os.path.isdir(RESULTS_DIR):
        return {"comparisons": [], "total": 0}

    csvs = sorted(glob.glob(os.path.join(RESULTS_DIR, "comparison_*.csv")), key=os.path.getmtime, reverse=True)
    comparisons = []
    for f in csvs:
        comparisons.append({
            "filename": os.path.basename(f),
            "modified": datetime.fromtimestamp(os.path.getmtime(f)).isoformat(),
        })

    return {"comparisons": comparisons, "total": len(comparisons)}


@router.get("/training/status")
async def training_status():
    """Get overall training status: dataset, models, last results."""
    dataset_path = settings.parquet_path
    dataset_exists = os.path.isfile(dataset_path)
    dataset_size = os.path.getsize(dataset_path) / (1024 * 1024) if dataset_exists else 0

    model_files = []
    if os.path.isdir(MODELS_DIR):
        model_files = [f for f in os.listdir(MODELS_DIR) if os.path.isfile(os.path.join(MODELS_DIR, f))]

    result_files = []
    if os.path.isdir(RESULTS_DIR):
        result_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]

    csv_files = []
    if os.path.isdir(RESULTS_DIR):
        csv_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".csv")]

    last_result = None
    if result_files:
        json_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")), key=os.path.getmtime, reverse=True)
        if json_files:
            try:
                with open(json_files[0], "r", encoding="utf-8") as f:
                    last_result = json.load(f)
            except Exception:
                pass

    return {
        "dataset": {
            "exists": dataset_exists,
            "size_mb": round(dataset_size, 1),
            "path": dataset_path,
        },
        "models": {
            "count": len(model_files),
            "files": model_files,
        },
        "results": {
            "count": len(result_files),
            "csv_count": len(csv_files),
            "last": last_result,
        },
    }
