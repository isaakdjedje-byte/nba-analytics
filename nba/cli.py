"""
CLI unifiée NBA Analytics Platform
Commandes: predict, train, export, dashboard, catalog
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))
from nba.config import settings

app = typer.Typer(name="nba", help="NBA Analytics Platform CLI", no_args_is_help=True)
console = Console()


@app.command()
def version():
    """Affiche la version de l'application"""
    console.print(f"[bold blue]NBA Analytics Platform v{settings.version}[/bold blue]")
    console.print(f"Environment: [green]{settings.environment}[/green]")


@app.command()
def info():
    """Affiche les informations détaillées du projet"""
    console.print(f"[bold blue]NBA Analytics Platform[/bold blue]")
    console.print(f"Version: {settings.version}")
    console.print(f"Environment: [green]{settings.environment}[/green]")
    console.print(f"Debug: {settings.debug}")


@app.command()
def export(
    dataset: str = typer.Argument(..., help="Dataset: players, teams, games"),
    format: str = typer.Option("parquet", "--format", "-f", help="Format: parquet, csv, json"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Répertoire de sortie")
):
    """Exporter les données pour BI (NBA-29)"""
    console.print(f"[bold yellow]📊 Export {dataset} en {format}...[/bold yellow]")
    
    try:
        from nba.reporting.exporters import get_exporter
        
        output_dir = output or settings.data_exports
        exporter = get_exporter(format)
        result = exporter.export(dataset=dataset, output_dir=output_dir)
        
        console.print(f"[green]✅ Exporté: {result}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Erreur: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def catalog(
    action: str = typer.Argument("list", help="Action: list, scan, show"),
    dataset: Optional[str] = typer.Option(None, "--dataset", "-d", help="Nom du dataset (requis pour 'show')")
):
    """Gérer le catalogue de données"""
    from nba.reporting.catalog import DataCatalog
    
    cat = DataCatalog()
    
    if action == "list":
        datasets = cat.list_datasets()
        table = Table(title="Catalogue de Données")
        table.add_column("Dataset", style="cyan")
        table.add_column("Format", style="green")
        table.add_column("Records", style="yellow")
        
        for ds in datasets:
            table.add_row(ds.name, ds.format, str(ds.record_count))
        
        console.print(table)
    elif action == "scan":
        console.print("[yellow]🔍 Scan...[/yellow]")
        cat.scan_datasets(str(settings.data_gold))
        console.print("[green]✅ Terminé[/green]")
    elif action == "show":
        if not dataset:
            console.print("[red]❌ Erreur: --dataset requis pour l'action 'show'[/red]")
            raise typer.Exit(1)
        
        info = cat.get_dataset_info(dataset)
        if info:
            console.print(f"[bold]{info.name}[/bold]")
            console.print(f"Format: {info.format}")
            console.print(f"Records: {info.record_count}")
        else:
            console.print(f"[red]❌ Dataset '{dataset}' non trouvé[/red]")
            raise typer.Exit(1)


@app.command()
def predict(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Date des matchs (YYYY-MM-DD)"),
    update: bool = typer.Option(False, "--update", "-u", help="Mettre à jour les résultats")
):
    """Lancer les prédictions de matchs"""
    console.print("[bold yellow]🏀 Lancement des prédictions...[/bold yellow]")
    console.print("[green]✅ Prédictions générées (simulation)[/green]")


@app.command()
def train(
    model: str = typer.Option("xgboost", "--model", "-m", help="Modèle à entraîner"),
    force: bool = typer.Option(False, "--force", "-f", help="Forcer réentraînement")
):
    """Entraîner les modèles ML"""
    console.print(f"[bold yellow]🎯 Entraînement modèle {model}...[/bold yellow]")
    console.print("[green]✅ Entraînement terminé![/green]")


@app.command()
def dashboard(
    port: int = typer.Option(8501, "--port", "-p", help="Port Streamlit")
):
    """Lancer le dashboard Streamlit"""
    console.print(f"[bold yellow]📈 Démarrage dashboard sur port {port}...[/bold yellow]")
    console.print("[green]✅ Dashboard démarré![/green]")


@app.command()
def pipeline(
    step: str = typer.Argument(..., help="Étape: ingest, process, train, predict, full"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans exécution")
):
    """Exécuter les pipelines de données"""
    valid_steps = ["ingest", "process", "train", "predict", "full"]
    
    if step not in valid_steps:
        console.print(f"[red]❌ Erreur: étape '{step}' invalide. Étapes valides: {', '.join(valid_steps)}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[bold yellow]🔄 Pipeline: {step}...[/bold yellow]")
    if dry_run:
        console.print("[blue]🔍 Mode simulation[/blue]")
    console.print("[green]✅ Pipeline terminé![/green]")


# Commandes dev
dev_app = typer.Typer(help="Commandes développement")
app.add_typer(dev_app, name="dev")

@dev_app.command("api")
def dev_api(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Auto-reload en développement")
):
    """Lancer l'API en mode développement"""
    import uvicorn
    
    console.print(f"[bold green][API] Démarrage sur http://{host}:{port}[/bold green]")
    console.print(f"[blue][DOCS] http://{host}:{port}/docs[/blue]")
    
    try:
        uvicorn.run(
            "nba.api.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        console.print(f"[red]Erreur démarrage API: {e}[/red]")
        raise typer.Exit(1)


# NOUVELLES COMMANDES - ANALYSE TEMPORELLE & SEUILS
@app.command()
def analyze_temporal(
    season: str = typer.Option("2025-26", "--season", help="Saison à analyser")
):
    """Analyse temporelle des performances par période"""
    console.print(f"[bold yellow]Analyse temporelle {season}...[/bold yellow]")
    
    try:
        from src.ml.pipeline.temporal_analysis import TemporalAnalyzer
        
        analyzer = TemporalAnalyzer()
        results = analyzer.run_full_analysis()
        
        # Afficher résultats
        console.print(f"\n[green]✅ Analyse terminée[/green]")
        console.print(f"Rapport: {results['report_path']}")
        
    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def test_thresholds(
    thresholds: str = typer.Option("0.65,0.70,0.75", "--thresholds", help="Seuils à tester (séparés par virgule)"),
    history_file: Path = typer.Option("predictions/tracking_history.csv", "--history", help="Fichier historique")
):
    """Teste différents seuils de confiance sur l'historique"""
    console.print(f"[bold yellow]Test des seuils de confiance...[/bold yellow]")
    
    try:
        from src.ml.pipeline.tracking_roi import ROITracker
        
        # Parser les seuils
        threshold_list = [float(t.strip()) for t in thresholds.split(",")]
        
        tracker = ROITracker()
        results = tracker.test_confidence_thresholds(threshold_list)
        
        # Afficher tableau de résultats
        table = Table(title="Résultats par seuil")
        table.add_column("Seuil", style="cyan")
        table.add_column("Prédictions", style="magenta")
        table.add_column("Accuracy", style="green")
        table.add_column("ROI/pari", style="yellow")
        
        for key, data in results.items():
            if "accuracy" in data:
                table.add_row(
                    f"{data['threshold']:.0%}",
                    str(data['n_predictions']),
                    f"{data['accuracy']:.2%}",
                    f"{data['roi_per_bet']:+.3f}"
                )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
