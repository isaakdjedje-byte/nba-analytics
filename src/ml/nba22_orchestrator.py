#!/usr/bin/env python3
"""
NBA-22: Orchestrateur Principal

Point d'entrée unique pour l'entraînement et la prédiction des modèles ML.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ml.nba22_train import NBA22Trainer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_command(args):
    """Commande: entraîner les modèles."""
    logger.info("🚀 Démarrage entraînement NBA-22")
    
    trainer = NBA22Trainer(features_path=args.features)
    results = trainer.run(save=not args.no_save)
    
    # Afficher résumé
    print("\n" + "="*70)
    print("RÉSUMÉ NBA-22")
    print("="*70)
    print(f"✅ Random Forest:  {results['results']['rf']['accuracy']:.3f} accuracy")
    print(f"✅ Gradient Boost: {results['results']['gbt']['accuracy']:.3f} accuracy")
    print(f"🏆 Meilleur modèle: {results['best_model']['name'].upper()}")
    print(f"📁 Résultats sauvegardés: {results['output_dir']}")
    print("="*70)
    
    return results


def predict_command(args):
    """Commande: faire une prédiction sur un match."""
    import joblib
    import pandas as pd
    
    logger.info(f"🎯 Prédiction avec modèle: {args.model}")
    
    # Charger le modèle
    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(f"Modèle non trouvé: {model_path}")
        sys.exit(1)
    
    model = joblib.load(model_path)
    
    # Charger les features si fournies
    if args.features:
        df = pd.read_parquet(args.features)
        X = df.select_dtypes(include=['float64', 'int64']).drop(columns=['target'], errors='ignore')
        
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)[:, 1]
        
        results = pd.DataFrame({
            'prediction': predictions,
            'probability_home_win': probabilities,
            'probability_away_win': 1 - probabilities
        })
        
        if args.output:
            results.to_csv(args.output, index=False)
            logger.info(f"Prédictions sauvegardées: {args.output}")
        else:
            print(results.head(10))
    else:
        logger.info("Mode interactif - utiliser --features pour prédire sur un fichier")


def evaluate_command(args):
    """Commande: évaluer un modèle sauvegardé."""
    import joblib
    import pandas as pd
    from sklearn.metrics import accuracy_score, classification_report
    
    logger.info(f"📊 Évaluation modèle: {args.model}")
    
    model = joblib.load(args.model)
    df = pd.read_parquet(args.features)
    
    # Split temporel comme pendant l'entraînement
    test_mask = df['season'].isin(['2023-24', '2024-25'])
    
    exclude_cols = [
        'game_id', 'season', 'game_date', 'season_type',
        'home_team_id', 'home_team_name', 'home_team_abbr',
        'away_team_id', 'away_team_name', 'away_team_abbr',
        'home_wl', 'away_wl', 'target', 'point_diff'
    ]
    
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X_test = df.loc[test_mask, feature_cols]
    y_test = df.loc[test_mask, 'target']
    
    y_pred = model.predict(X_test)
    
    print("\n" + "="*70)
    print("RAPPORT D'ÉVALUATION")
    print("="*70)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Away Win', 'Home Win']))


def compare_command(args):
    """Commande: comparer plusieurs expérimentations."""
    experiments_dir = Path("models/experiments")
    
    if not experiments_dir.exists():
        logger.error(f"Dossier non trouvé: {experiments_dir}")
        sys.exit(1)
    
    results = []
    for exp_dir in sorted(experiments_dir.glob("nba22_*")):
        metrics_file = exp_dir / "metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                data = json.load(f)
                results.append({
                    'experiment': exp_dir.name,
                    'timestamp': data['timestamp'],
                    'best_model': data['best_model']['name'],
                    'accuracy': data['best_model']['accuracy'],
                    'n_features': data['n_features']
                })
    
    if not results:
        print("Aucune expérimentation trouvée")
        return
    
    print("\n" + "="*70)
    print("COMPARAISON DES EXPÉRIMENTATIONS")
    print("="*70)
    
    for r in results:
        print(f"\n{r['experiment']}")
        print(f"  Meilleur: {r['best_model'].upper()}")
        print(f"  Accuracy: {r['accuracy']:.3f}")
        print(f"  Features: {r['n_features']}")
    
    # Meilleure expérimentation
    best = max(results, key=lambda x: x['accuracy'])
    print(f"\n🏆 MEILLEURE EXPÉRIMENTATION: {best['experiment']}")


def deploy_command(args):
    """Commande: déployer un modèle en production."""
    import shutil
    from datetime import datetime
    
    logger.info(f"🚀 Déploiement modèle: {args.model}")
    
    source = Path(args.model)
    if not source.exists():
        logger.error(f"Modèle source non trouvé: {source}")
        sys.exit(1)
    
    # Créer dossier production avec version
    version = args.version or datetime.now().strftime("v%Y%m%d_%H%M%S")
    prod_dir = Path("models/production") / f"classification_{version}"
    prod_dir.mkdir(parents=True, exist_ok=True)
    
    # Copier modèle
    if source.is_file():
        shutil.copy2(source, prod_dir / "model.joblib")
    else:
        shutil.copytree(source, prod_dir / "model")
    
    # Créer manifest
    manifest = {
        'version': version,
        'source': str(source),
        'deployed_at': datetime.now().isoformat(),
        'algorithm': 'rf' if 'rf' in source.name else 'gbt'
    }
    
    with open(prod_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"✅ Modèle déployé: {prod_dir}")
    print(f"\nVersion: {version}")
    print(f"Chemin: {prod_dir}")


def main():
    """Point d'entrée principal avec argparse."""
    parser = argparse.ArgumentParser(
        description='NBA-22: Orchestrateur ML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Entraîner les modèles
  python -m src.ml.nba22_orchestrator train
  
  # Prédire avec un modèle
  python -m src.ml.nba22_orchestrator predict --model models/experiments/.../model_rf.joblib --features data.parquet
  
  # Comparer les expérimentations
  python -m src.ml.nba22_orchestrator compare
  
  # Déployer en production
  python -m src.ml.nba22_orchestrator deploy --model models/experiments/.../model_rf.joblib --version v1.0.0
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commande à exécuter')
    
    # Commande train
    train_parser = subparsers.add_parser('train', help='Entraîner les modèles')
    train_parser.add_argument(
        '--features',
        default='data/gold/ml_features/features_all.parquet',
        help='Chemin vers les features (parquet)'
    )
    train_parser.add_argument(
        '--no-save',
        action='store_true',
        help='Ne pas sauvegarder les modèles'
    )
    
    # Commande predict
    predict_parser = subparsers.add_parser('predict', help='Faire une prédiction')
    predict_parser.add_argument('--model', required=True, help='Chemin du modèle')
    predict_parser.add_argument('--features', help='Chemin des features à prédire')
    predict_parser.add_argument('--output', help='Fichier de sortie (CSV)')
    
    # Commande evaluate
    eval_parser = subparsers.add_parser('evaluate', help='Évaluer un modèle')
    eval_parser.add_argument('--model', required=True, help='Chemin du modèle')
    eval_parser.add_argument(
        '--features',
        default='data/gold/ml_features/features_all.parquet',
        help='Chemin vers les features'
    )
    
    # Commande compare
    subparsers.add_parser('compare', help='Comparer les expérimentations')
    
    # Commande deploy
    deploy_parser = subparsers.add_parser('deploy', help='Déployer en production')
    deploy_parser.add_argument('--model', required=True, help='Chemin du modèle')
    deploy_parser.add_argument('--version', help='Version (ex: v1.0.0)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Exécuter la commande
    commands = {
        'train': train_command,
        'predict': predict_command,
        'evaluate': evaluate_command,
        'compare': compare_command,
        'deploy': deploy_command
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
