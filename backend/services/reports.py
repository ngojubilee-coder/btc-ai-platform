"""Report generation service — PDF and HTML reports."""
from datetime import datetime, timezone


def generate_html_report(title: str, content: str, metadata: dict = None) -> str:
    """Generate an HTML report from markdown content."""
    timestamp = datetime.now(timezone.utc).isoformat()
    meta_html = ""
    if metadata:
        meta_html = "<table class='meta'>"
        for k, v in metadata.items():
            meta_html += f"<tr><td><b>{k}</b></td><td>{v}</td></tr>"
        meta_html += "</table>"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #0f172a; color: #e2e8f0; }}
        h1 {{ color: #38bdf8; border-bottom: 2px solid #1e293b; padding-bottom: 10px; }}
        h2 {{ color: #818cf8; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #334155; padding: 8px 12px; text-align: left; }}
        th {{ background: #1e293b; color: #38bdf8; }}
        tr:nth-child(even) {{ background: #1e293b; }}
        .meta td {{ border: none; padding: 4px 12px; }}
        code {{ background: #1e293b; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }}
        pre {{ background: #1e293b; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #334155; color: #64748b; font-size: 0.85em; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {meta_html}
    <div class="content">
        {content}
    </div>
    <div class="footer">
        <p>Généré le {timestamp} par BTC AI Platform</p>
    </div>
</body>
</html>"""
    return html


def generate_model_comparison_report(runs: list[dict]) -> str:
    """Generate an HTML report comparing model runs."""
    rows = ""
    for run in runs:
        metrics = run.get("metrics", {})
        rows += f"""
        <tr>
            <td>{run.get('model_name', 'N/A')}</td>
            <td>{run.get('version', 'N/A')}</td>
            <td>{run.get('model_type', 'N/A')}</td>
            <td>{metrics.get('accuracy', 'N/A')}</td>
            <td>{metrics.get('precision', 'N/A')}</td>
            <td>{metrics.get('recall', 'N/A')}</td>
            <td>{metrics.get('f1', 'N/A')}</td>
            <td>{run.get('train_loss', 'N/A')}</td>
            <td>{run.get('val_loss', 'N/A')}</td>
            <td>{run.get('status', 'N/A')}</td>
        </tr>"""

    content = f"""
    <h2>Comparaison des modèles</h2>
    <table>
        <tr>
            <th>Modèle</th><th>Version</th><th>Type</th>
            <th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th>
            <th>Train Loss</th><th>Val Loss</th><th>Status</th>
        </tr>
        {rows}
    </table>"""

    return generate_html_report(
        "Rapport de comparaison des modèles",
        content,
        {"Date": datetime.now(timezone.utc).isoformat(), "Nombre de modèles": str(len(runs))}
    )
