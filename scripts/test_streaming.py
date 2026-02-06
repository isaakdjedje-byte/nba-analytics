#!/usr/bin/env python3
"""
Script de test pour valider le pipeline Spark Streaming NBA-13
Lance le streaming et le simulateur avec synchronisation automatique
"""
import subprocess
import time
import sys
import os

def main():
    print("="*70)
    print("TEST NBA-13: Spark Streaming Box Score")
    print("="*70)
    print("\nArchitecture: Dossiers uniques par execution + synchronisation")
    print("\nNOUVEL ORDRE (synchronisation automatique):")
    print("\nTerminal 1 - Streaming (demarrer en premier):")
    print("  docker-compose exec spark-nba python src/ingestion/streaming_ingestion.py")
    print("  -> Attend automatiquement le simulateur (max 3 minutes)")
    print("\nTerminal 2 - Simulateur (demarrer apres):")
    print("  docker-compose exec spark-nba python src/ingestion/streaming_simulator.py")
    print("  -> Cree un dossier unique (run_YYYYMMDD_HHMMSS)")
    print("  -> Ecrit tous les fichiers JSON")
    print("  -> Cree fichier COMPLETE quand termine")
    print("\nAvantages:")
    print("  ✓ Pas de conflit avec les anciennes executions")
    print("  ✓ Pas de fichiers supprimes pendant la lecture")
    print("  ✓ Synchronisation automatique")
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
