#!/usr/bin/env python3
"""
TEST DEEP LEARNING - NBA-22
Architecture simple MLP pour comparer avec Random Forest
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import numpy as np
import json
import time
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
device = torch.device('cpu')  # Pas de GPU disponible
logger.info(f"Utilisation de: {device}")


class NBANeuralNetwork(nn.Module):
    """
    Réseau de neurones simple pour prédiction NBA
    Architecture: 24 -> 64 -> 32 -> 1
    """
    def __init__(self, input_dim, dropout_rate=0.3):
        super(NBANeuralNetwork, self).__init__()
        
        self.layer1 = nn.Linear(input_dim, 64)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout_rate)
        
        self.layer2 = nn.Linear(64, 32)
        self.bn2 = nn.BatchNorm1d(32)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout_rate)
        
        self.output = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.layer1(x)
        x = self.bn1(x)
        x = self.relu1(x)
        x = self.dropout1(x)
        
        x = self.layer2(x)
        x = self.bn2(x)
        x = self.relu2(x)
        x = self.dropout2(x)
        
        x = self.output(x)
        x = self.sigmoid(x)
        return x


def load_data():
    """Charge les données NBA."""
    logger.info("Chargement des données...")
    
    df = pd.read_parquet("data/gold/ml_features/features_all.parquet")
    
    # Split temporel (même que RF)
    train_mask = ~df['season'].isin(['2023-24', '2024-25'])
    test_mask = df['season'].isin(['2023-24', '2024-25'])
    
    # Features (mêmes exclusions que RF - pas de data leakage)
    exclude_cols = [
        'game_id', 'season', 'game_date', 'season_type',
        'home_team_id', 'home_team_name', 'home_team_abbr',
        'away_team_id', 'away_team_name', 'away_team_abbr',
        'home_wl', 'away_wl', 'target',
        'point_diff', 'home_score', 'away_score',
        'home_reb', 'home_ast', 'home_stl', 'home_blk', 'home_tov', 'home_pf',
        'away_reb', 'away_ast', 'away_stl', 'away_blk', 'away_tov', 'away_pf',
        'home_ts_pct', 'home_efg_pct', 'home_game_score', 'home_fatigue_eff',
        'away_ts_pct', 'away_efg_pct', 'away_game_score', 'away_fatigue_eff',
        'ts_pct_diff'
    ]
    
    feature_cols = [c for c in df.columns if c not in exclude_cols]
    
    X_train = df.loc[train_mask, feature_cols].values
    y_train = df.loc[train_mask, 'target'].values
    X_test = df.loc[test_mask, feature_cols].values
    y_test = df.loc[test_mask, 'target'].values
    
    # Standardisation (important pour les réseaux de neurones)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    logger.info(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    logger.info(f"Features: {len(feature_cols)}")
    
    return X_train, y_train, X_test, y_test, feature_cols


def train_model(X_train, y_train, X_test, y_test, input_dim, epochs=100, batch_size=64):
    """Entraîne le réseau de neurones."""
    
    # Créer les datasets PyTorch
    train_dataset = TensorDataset(
        torch.FloatTensor(X_train),
        torch.FloatTensor(y_train).unsqueeze(1)
    )
    test_dataset = TensorDataset(
        torch.FloatTensor(X_test),
        torch.FloatTensor(y_test).unsqueeze(1)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialiser le modèle
    model = NBANeuralNetwork(input_dim).to(device)
    
    # Loss et optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=5, factor=0.5)
    
    # Early stopping
    best_auc = 0
    patience = 10
    patience_counter = 0
    
    logger.info(f"Début de l'entraînement (max {epochs} epochs)...")
    start_time = time.time()
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        # Évaluation
        model.eval()
        val_preds = []
        val_labels = []
        
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                batch_X = batch_X.to(device)
                outputs = model(batch_X)
                val_preds.extend(outputs.cpu().numpy())
                val_labels.extend(batch_y.numpy())
        
        val_preds = np.array(val_preds).flatten()
        val_labels = np.array(val_labels).flatten()
        val_auc = roc_auc_score(val_labels, val_preds)
        
        # Early stopping
        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            # Sauvegarder le meilleur modèle
            torch.save(model.state_dict(), 'models/best_nn_model.pth')
        else:
            patience_counter += 1
        
        if patience_counter >= patience:
            logger.info(f"Early stopping à l'epoch {epoch+1}")
            break
        
        scheduler.step(val_auc)
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {train_loss/len(train_loader):.4f} - Val AUC: {val_auc:.4f}")
    
    training_time = time.time() - start_time
    logger.info(f"Entraînement terminé en {training_time:.1f} secondes")
    
    # Charger le meilleur modèle
    model.load_state_dict(torch.load('models/best_nn_model.pth'))
    
    return model, training_time


def evaluate_model(model, X_test, y_test):
    """Évalue le modèle sur le test set."""
    model.eval()
    
    test_dataset = TensorDataset(torch.FloatTensor(X_test), torch.FloatTensor(y_test))
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)
    
    all_preds = []
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            batch_X = batch_X.to(device)
            outputs = model(batch_X)
            all_probs.extend(outputs.cpu().numpy().flatten())
            all_preds.extend((outputs.cpu().numpy() > 0.5).astype(int).flatten())
            all_labels.extend(batch_y.numpy())
    
    y_pred = np.array(all_preds)
    y_proba = np.array(all_probs)
    y_true = np.array(all_labels)
    
    # Calculer les métriques
    metrics = {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'precision': float(precision_score(y_true, y_pred, zero_division=0)),
        'recall': float(recall_score(y_true, y_pred, zero_division=0)),
        'f1': float(f1_score(y_true, y_pred, zero_division=0)),
        'auc': float(roc_auc_score(y_true, y_proba))
    }
    
    return metrics, y_pred, y_proba


def compare_with_rf(nn_metrics):
    """Compare avec les résultats Random Forest."""
    # Charger les résultats RF
    exp_dir = sorted(Path("models/experiments").glob("nba22_*"))[-1]
    with open(exp_dir / "metrics.json") as f:
        rf_results = json.load(f)
    
    rf_metrics = rf_results['models']['rf']
    
    logger.info("\n" + "="*70)
    logger.info("COMPARAISON NEURAL NETWORK vs RANDOM FOREST")
    logger.info("="*70)
    logger.info(f"{'Métrique':<15} {'Neural Net':>12} {'Random Forest':>15} {'Différence':>12}")
    logger.info("-"*70)
    
    for metric in ['accuracy', 'precision', 'recall', 'f1', 'auc']:
        nn_val = nn_metrics[metric]
        rf_val = rf_metrics[metric]
        diff = nn_val - rf_val
        diff_str = f"{diff:+.3f}"
        logger.info(f"{metric.capitalize():<15} {nn_val:>12.3f} {rf_val:>15.3f} {diff_str:>12}")
    
    logger.info("="*70)
    
    # Décision
    if nn_metrics['accuracy'] > rf_metrics['accuracy'] + 0.01:
        logger.info("✅ VERDICT: Neural Network MEILLEUR que Random Forest")
        logger.info("   Action: Intégrer le DL dans le stacking")
        return True
    elif nn_metrics['accuracy'] < rf_metrics['accuracy'] - 0.01:
        logger.info("❌ VERDICT: Neural Network MOINS BON que Random Forest")
        logger.info("   Action: Abandonner le DL, focus sur RF/XGB")
        return False
    else:
        logger.info("⚠️ VERDICT: Neural Network ÉQUIVALENT à Random Forest")
        logger.info("   Action: Optionnel - peut être utilisé pour la diversité")
        return None


def main():
    """Fonction principale."""
    logger.info("="*70)
    logger.info("TEST DEEP LEARNING - NBA-22")
    logger.info("="*70)
    
    # 1. Charger les données
    X_train, y_train, X_test, y_test, feature_cols = load_data()
    
    # 2. Créer le dossier models s'il n'existe pas
    Path("models").mkdir(exist_ok=True)
    
    # 3. Entraîner le modèle
    model, training_time = train_model(
        X_train, y_train, X_test, y_test,
        input_dim=len(feature_cols),
        epochs=100,
        batch_size=64
    )
    
    # 4. Évaluer
    metrics, y_pred, y_proba = evaluate_model(model, X_test, y_test)
    
    logger.info("\nRésultats Neural Network:")
    logger.info(f"  Accuracy:  {metrics['accuracy']:.3f}")
    logger.info(f"  Precision: {metrics['precision']:.3f}")
    logger.info(f"  Recall:    {metrics['recall']:.3f}")
    logger.info(f"  F1-Score:  {metrics['f1']:.3f}")
    logger.info(f"  AUC:       {metrics['auc']:.3f}")
    logger.info(f"  Temps d'entraînement: {training_time:.1f}s")
    
    # 5. Comparer avec RF
    is_better = compare_with_rf(metrics)
    
    # 6. Sauvegarder les résultats
    results = {
        'model': 'NeuralNetwork',
        'architecture': '24->64->32->1',
        'metrics': metrics,
        'training_time_seconds': training_time,
        'is_better_than_rf': is_better,
        'feature_count': len(feature_cols)
    }
    
    with open('models/nn_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("\nRésultats sauvegardés dans models/nn_test_results.json")
    
    return is_better


if __name__ == "__main__":
    main()
