#!/usr/bin/env python3
"""
Harmonise les features entre historique et 2025-26
Ajoute les features manquantes avec des valeurs par defaut
"""

import pandas as pd
import numpy as np
from pathlib import Path

def harmonize_features():
    """Harmonise les features entre les deux datasets"""
    
    print("="*70)
    print("HARMONISATION DES FEATURES")
    print("="*70)
    
    # Charger les deux datasets
    hist_path = Path('data/gold/ml_features/features_all.parquet')
    live_path = Path('data/gold/ml_features/features_2025-26_v3.parquet')
    
    if not hist_path.exists():
        print(f"Historique non trouve: {hist_path}")
        return
    if not live_path.exists():
        print(f"2025-26 non trouve: {live_path}")
        return
    
    df_hist = pd.read_parquet(hist_path)
    df_live = pd.read_parquet(live_path)
    
    print(f"\nHistorique: {len(df_hist)} matchs, {len(df_hist.columns)} features")
    print(f"2025-26: {len(df_live)} matchs, {len(df_live.columns)} features")
    
    # Features dans chaque dataset
    hist_features = set(df_hist.columns)
    live_features = set(df_live.columns)
    
    # Features a ajouter a l'historique
    missing_in_hist = live_features - hist_features
    if missing_in_hist:
        print(f"\nFeatures manquantes dans HISTORIQUE ({len(missing_in_hist)}):")
        for f in sorted(missing_in_hist):
            print(f"  + {f}")
            # Ajouter avec valeur 0 ou mediane
            if df_live[f].dtype in ['float64', 'int64']:
                df_hist[f] = 0.0
            else:
                df_hist[f] = df_live[f].iloc[0] if len(df_live) > 0 else None
    
    # Features a ajouter a 2025-26
    missing_in_live = hist_features - live_features
    if missing_in_live:
        print(f"\nFeatures manquantes dans 2025-26 ({len(missing_in_live)}):")
        for f in sorted(missing_in_live):
            print(f"  + {f}")
            if df_hist[f].dtype in ['float64', 'int64']:
                df_live[f] = 0.0
            else:
                df_live[f] = df_hist[f].iloc[0] if len(df_hist) > 0 else None
    
    # S'assurer que les deux ont les memes colonnes dans le meme ordre
    common_features = sorted(list(hist_features | live_features))
    
    # Reordonner
    df_hist = df_hist[common_features]
    df_live = df_live[common_features]
    
    print(f"\nHarmonisation terminee:")
    print(f"  Historique: {len(df_hist.columns)} features")
    print(f"  2025-26: {len(df_live.columns)} features")
    
    # Sauvegarder
    df_hist.to_parquet(hist_path)
    df_live.to_parquet(live_path)
    
    print(f"\nDatasets sauvegardes")
    
    return df_hist, df_live

if __name__ == "__main__":
    harmonize_features()
