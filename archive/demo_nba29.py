"""
Démonstration NBA-29 - Export BI
Montre comment utiliser le nouveau système de reporting
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from nba.reporting.catalog import DataCatalog
from nba.reporting.exporters import get_exporter
from nba.config import settings
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def demo_catalog():
    """Démo du catalogue de données"""
    console.print(Panel.fit("[bold blue][STATS] Data Catalog - NBA-29[/bold blue]"))
    
    catalog = DataCatalog()
    
    # Scan les datasets
    console.print("\n[yellow][SEARCH] Scan des datasets...[/yellow]")
    count = catalog.scan_datasets(str(settings.data_gold))
    console.print(f"[green][OK] {count} datasets trouvés[/green]")
    
    # Affiche le catalogue
    datasets = catalog.list_datasets()
    
    if datasets:
        table = Table(title="Datasets enregistrés")
        table.add_column("Nom", style="cyan")
        table.add_column("Format", style="green")
        table.add_column("Records", style="yellow")
        table.add_column("Taille", style="magenta")
        
        for ds in datasets[:10]:  # Limite à 10 pour la démo
            size_mb = ds.size_bytes / (1024 * 1024) if ds.size_bytes else 0
            table.add_row(
                ds.name,
                ds.format,
                str(ds.record_count),
                f"{size_mb:.2f} MB"
            )
        
        console.print(table)
    else:
        console.print("[yellow][INFO] Aucun dataset trouvé dans data/gold/[/yellow]")


def demo_export():
    """Démo des exports"""
    console.print(Panel.fit("[bold green][EXPORT] Export BI - NBA-29[/bold green]"))
    
    # Liste les datasets disponibles
    available_datasets = ["players", "teams", "games"]
    
    console.print("\n[blue]Datasets disponibles pour export:[/blue]")
    for i, ds in enumerate(available_datasets, 1):
        console.print(f"  {i}. {ds}")
    
    # Démo export CSV
    console.print("\n[yellow][EXPORT] Export CSV (démonstration)...[/yellow]")
    try:
        exporter = get_exporter("csv")
        result = exporter.export(
            dataset="team_season_stats",
            output_dir=Path("data/exports"),
        )
        console.print(f"[green][OK] Exporté: {result}[/green]")
    except Exception as e:
        console.print(f"[red][ERROR] Erreur: {e}[/red]")
    
    # Démo export Parquet
    console.print("\n[yellow][EXPORT] Export Parquet (démonstration)...[/yellow]")
    try:
        exporter = get_exporter("parquet")
        result = exporter.export(
            dataset="team_season_stats",
            output_dir=Path("data/exports"),
            compression="snappy"
        )
        console.print(f"[green][OK] Exporté: {result}[/green]")
    except Exception as e:
        console.print(f"[red][ERROR] Erreur: {e}[/red]")


def demo_cli():
    """Démo des commandes CLI"""
    console.print(Panel.fit("[bold yellow][CLI] Commandes CLI - NBA-29[/bold yellow]"))
    
    commands = [
        ("nba catalog list", "Lister les datasets"),
        ("nba catalog scan", "Scanner et mettre à jour"),
        ("nba export players --format csv", "Exporter joueurs en CSV"),
        ("nba export teams --format parquet", "Exporter équipes en Parquet"),
        ("nba export all --output ./exports", "Tous les datasets"),
    ]
    
    table = Table(title="Commandes disponibles")
    table.add_column("Commande", style="cyan")
    table.add_column("Description", style="green")
    
    for cmd, desc in commands:
        table.add_row(cmd, desc)
    
    console.print(table)


def demo_api():
    """Démo des endpoints API"""
    console.print(Panel.fit("[bold magenta][API] API REST - NBA-29[/bold magenta]"))
    
    endpoints = [
        ("GET /", "Info API"),
        ("GET /api/v1/datasets", "Lister datasets"),
        ("GET /api/v1/datasets/{name}", "Détails dataset"),
        ("POST /api/v1/export", "Exporter données"),
        ("POST /api/v1/catalog/scan", "Scanner catalog"),
    ]
    
    table = Table(title="Endpoints API")
    table.add_column("Méthode + Path", style="cyan")
    table.add_column("Description", style="green")
    
    for endpoint, desc in endpoints:
        table.add_row(endpoint, desc)
    
    console.print(table)
    console.print(f"\n[blue]Lancer: nba dev api[/blue]")
    console.print(f"[blue]Ou: docker-compose up api[/blue]")


def main():
    """Démonstration complète NBA-29"""
    console.print("\n" + "=" * 70)
    console.print("[bold]NBA-29: Export BI & Data Catalog - Démonstration[/bold]")
    console.print("=" * 70 + "\n")
    
    try:
        demo_catalog()
        console.print("\n" + "-" * 70 + "\n")
        
        demo_export()
        console.print("\n" + "-" * 70 + "\n")
        
        demo_cli()
        console.print("\n" + "-" * 70 + "\n")
        
        demo_api()
        
    except Exception as e:
        console.print(f"\n[red][ERROR] Erreur: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
    
    console.print("\n" + "=" * 70)
    console.print("[bold green][OK] Démonstration terminée![/bold green]")
    console.print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
