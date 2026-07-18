"""Models API routes — list, compare, get details, reports."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from db.supabase_client import get_supabase, save_report, get_reports
from db import duckdb_service

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/")
async def list_models(limit: int = 50):
    try:
        limit = max(1, min(int(limit), 500))
        sb = get_supabase()
        res = sb.table("model_runs").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare/{id1}/{id2}")
async def compare_models(id1: str, id2: str):
    try:
        sb = get_supabase()
        m1 = sb.table("model_runs").select("*").eq("id", id1).execute()
        m2 = sb.table("model_runs").select("*").eq("id", id2).execute()
        if not m1.data or not m2.data:
            raise HTTPException(status_code=404, detail="One or both models not found")

        f1 = sb.table("feature_importance").select("*").eq("model_run_id", id1).order("importance", desc=True).limit(20).execute()
        f2 = sb.table("feature_importance").select("*").eq("model_run_id", id2).order("importance", desc=True).limit(20).execute()

        return {
            "model_1": m1.data[0],
            "model_2": m2.data[0],
            "features_1": f1.data,
            "features_2": f2.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports")
async def list_reports(limit: int = 20):
    try:
        return await get_reports(limit)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load reports")


@router.get("/reports/{report_id}")
async def get_report_detail(report_id: str):
    """Get a single report with its full content."""
    try:
        sb = get_supabase()
        res = sb.table("reports").select("*").eq("id", report_id).execute()
        if res.data:
            return res.data[0]
        raise HTTPException(status_code=404, detail="Report not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/download", response_class=PlainTextResponse)
async def download_report(report_id: str):
    """Download report content as markdown."""
    try:
        sb = get_supabase()
        res = sb.table("reports").select("*").eq("id", report_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Report not found")
        r = res.data[0]
        content = r.get("content", "")
        if not content:
            content = f"# {r.get('title', 'Report')}\n\n*No content available.*"
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate")
async def generate_report(body: dict):
    report_type = body.get("type", "training")
    lang = body.get("lang", "fr")
    titles_fr = {
        "training": "Rapport d'entraînement",
        "comparison": "Comparaison de modèles",
        "dataset": "Rapport de dataset",
        "market": "Analyse de marché",
    }
    titles_en = {
        "training": "Training Report",
        "comparison": "Model Comparison",
        "dataset": "Dataset Report",
        "market": "Market Analysis",
    }
    titles = titles_en if lang == "en" else titles_fr
    title = titles.get(report_type, "Report" if lang == "en" else "Rapport")
    L = lang == "en"
    content = ""

    if report_type == "dataset":
        try:
            stats = duckdb_service.get_stats()
            schema = duckdb_service.get_schema()
            n_features = len([c for c in schema.get("columns", []) if not c["name"].startswith("target_") and c["name"] != "timestamp"])
            n_targets = len([c for c in schema.get("columns", []) if c["name"].startswith("target_")])
            corrs = duckdb_service.get_correlations(top_n=10)
            content = f"""# {title}

## {"Dataset Statistics" if L else "Statistiques du Dataset"}

| {"Metric" if L else "Métrique"} | {"Value" if L else "Valeur"} |
|----------|--------|
| {"Total rows" if L else "Lignes totales"} | {stats.get("n_rows", 0):,} |
| {"Columns" if L else "Colonnes"} | {stats.get("n_columns", 0)} |
| Features | {n_features} |
| Targets | {n_targets} |
| {"File size" if L else "Taille fichier"} | {stats.get("file_size_mb", 0)} MB |
| {"Min date" if L else "Date min"} | {stats.get("min_timestamp", "N/A")} |
| {"Max date" if L else "Date max"} | {stats.get("max_timestamp", "N/A")} |

## {"Top 10 Correlations (target_return_15m)" if L else "Top 10 Corrélations (target_return_15m)"}

| Feature | {"Correlation" if L else "Corrélation"} |
|---------|------------|
"""
            for c in corrs:
                content += f"| {c['feature']} | {c['correlation']:.4f} |\n"
        except Exception as e:
            content = f"# {title}\n\n{('Error during generation' if L else 'Erreur lors de la génération')}: {e}"

    elif report_type == "training":
        try:
            sb = get_supabase()
            res = sb.table("model_runs").select("*").order("created_at", desc=True).limit(1).execute()
            if res.data:
                m = res.data[0]
                content = f"""# {title}

## {"Latest trained model" if L else "Dernier modèle entraîné"}

| {"Metric" if L else "Métrique"} | {"Value" if L else "Valeur"} |
|----------|--------|
| {"Name" if L else "Nom"} | {m.get('model_name', 'N/A')} |
| Status | {m.get('status', 'N/A')} |
| Train loss | {m.get('train_loss', 'N/A')} |
| Val loss | {m.get('val_loss', 'N/A')} |
| Accuracy | {m.get('accuracy', 'N/A')} |
| {"Created" if L else "Créé le"} | {m.get('created_at', 'N/A')} |

## {"Hyperparameters" if L else "Hyperparamètres"}

```
{m.get('hyperparams', 'N/A')}
```
"""
            else:
                content = f"# {title}\n\n{('No model found in the database.' if L else 'Aucun modèle trouvé dans la base de données.')}"
        except Exception as e:
            content = f"# {title}\n\n{('Error' if L else 'Erreur')}: {e}"

    elif report_type == "comparison":
        try:
            sb = get_supabase()
            res = sb.table("model_runs").select("*").order("created_at", desc=True).limit(2).execute()
            if res.data and len(res.data) >= 2:
                m1, m2 = res.data[0], res.data[1]
                content = f"""# {title}

## {"Comparison of the 2 latest models" if L else "Comparaison des 2 derniers modèles"}

| {"Metric" if L else "Métrique"} | {m1.get('model_name', 'Model 1')} | {m2.get('model_name', 'Model 2')} |
|----------|------|------|
| Status | {m1.get('status', 'N/A')} | {m2.get('status', 'N/A')} |
| Train loss | {m1.get('train_loss', 'N/A')} | {m2.get('train_loss', 'N/A')} |
| Val loss | {m1.get('val_loss', 'N/A')} | {m2.get('val_loss', 'N/A')} |
| Accuracy | {m1.get('accuracy', 'N/A')} | {m2.get('accuracy', 'N/A')} |
| {"Created" if L else "Créé le"} | {m1.get('created_at', 'N/A')} | {m2.get('created_at', 'N/A')} |
"""
            else:
                content = f"# {title}\n\n{('Less than 2 models available for comparison.' if L else 'Moins de 2 modèles disponibles pour la comparaison.')}"
        except Exception as e:
            content = f"# {title}\n\n{('Error' if L else 'Erreur')}: {e}"

    elif report_type == "market":
        try:
            from services.news_service import search_news_events
            news = await search_news_events(limit=20)
            content = f"""# {title}

## {"Recent news correlated with the market" if L else "Actualités récentes corrélées au marché"}

| {"Date" if L else "Date"} | {"Title" if L else "Titre"} | {"Type" if L else "Type"} | {"Source" if L else "Source"} |
|------|-------|------|--------|
"""
            for n in news:
                content += f"| {n.get('event_date', 'N/A')[:10]} | {n.get('title', 'N/A')[:60]} | {n.get('event_type', 'N/A')} | {n.get('source', 'N/A')} |\n"
            if not news:
                no_news_msg = "No news found. Click Refresh on the News page." if L else "Aucune actualité trouvée. Cliquez sur 'Actualiser' dans la page Actualités."
                content += f"\n*{no_news_msg}*\n"
        except Exception as e:
            content = f"# {title}\n\n{('Error' if L else 'Erreur')}: {e}"

    try:
        return await save_report(title, report_type, "completed", content)
    except Exception as e:
        return {"id": "local", "title": title, "report_type": report_type, "status": "completed", "content": content, "error": str(e)}


@router.get("/{model_id}")
async def get_model(model_id: str):
    try:
        sb = get_supabase()
        res = sb.table("model_runs").select("*").eq("id", model_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Model not found")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/features")
async def get_model_features(model_id: str):
    try:
        sb = get_supabase()
        res = sb.table("feature_importance").select("*").eq("model_run_id", model_id).order("importance", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}/backtests")
async def get_model_backtests(model_id: str):
    try:
        sb = get_supabase()
        res = sb.table("backtest_results").select("*").eq("model_run_id", model_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
