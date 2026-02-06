#!/usr/bin/env python3
"""
Simulateur de streaming NBA Box Score
Lit les données historiques et écrit des fichiers JSON pour Spark Streaming
"""
import json
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NBABoxScoreSimulator:
    """Simulateur de Box Score NBA en temps réel"""
    
    def __init__(self, data_dir: str = "data/raw", output_dir: str = "data/streaming/input"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.run_dir = None
        os.makedirs(output_dir, exist_ok=True)
        
    def load_random_game(self, season: str = "2023_24") -> Optional[Dict]:
        """Charge un match aléatoire depuis les données historiques"""
        season_dir = os.path.join(self.data_dir, season)
        games_file = os.path.join(season_dir, "games_regular_season.json")
        
        if not os.path.exists(games_file):
            logger.error(f"Fichier non trouvé: {games_file}")
            return None
            
        try:
            with open(games_file, 'r') as f:
                data = json.load(f)
                games = data.get('data', [])
                if games:
                    # Prendre un match aléatoire
                    game = random.choice(games)
                    logger.info(f"🎮 Match sélectionné: {game.get('MATCHUP', 'N/A')} - {game.get('GAME_DATE', 'N/A')}")
                    return game
        except Exception as e:
            logger.error(f"Erreur lecture fichier: {e}")
            return None
            
    def generate_box_score_evolution(self, game: Dict) -> List[Dict]:
        """Génère l'évolution du box score pendant le match"""
        events = []
        
        # Données finales du match
        final_score = game.get('PTS', 0)
        final_fgm = game.get('FGM', 0)
        final_fga = game.get('FGA', 1)
        final_fg3m = game.get('FG3M', 0)
        final_fg3a = game.get('FG3A', 1)
        final_ftm = game.get('FTM', 0)
        final_fta = game.get('FTA', 1)
        final_reb = game.get('REB', 0)
        final_ast = game.get('AST', 0)
        final_stl = game.get('STL', 0)
        final_blk = game.get('BLK', 0)
        
        game_id = game.get('GAME_ID', 'UNKNOWN')
        team_id = game.get('TEAM_ID', 0)
        team_abbr = game.get('TEAM_ABBREVIATION', 'UNK')
        matchup = game.get('MATCHUP', 'vs.')
        game_date = game.get('GAME_DATE', '2024-01-01')
        
        # Simuler 48 minutes de match + temps morts = ~2h30 réelles
        # On compresse : 48min de match = 10 minutes réelles
        # Box score toutes les 30 secondes = 20 box scores par match
        num_updates = 20
        
        # Générer des runs de scoring réalistes (le score ne peut que monter)
        target_scores = [0]  # Commencer à 0
        current_score = 0
        
        for i in range(1, num_updates):
            # Progression vers le score final
            progress = i / num_updates
            
            # Calculer le score attendu à ce moment (interpolation monotone)
            expected_score = int(final_score * progress)
            
            # Ajouter du bruit réaliste mais garantir la croissance
            # Variation aléatoire entre -5 et +15 points par update
            variation = random.randint(-5, 15)
            new_score = max(current_score + 1, expected_score + variation)  # +1 minimum pour garantir croissance
            new_score = min(new_score, final_score)  # Ne pas dépasser le score final
            
            target_scores.append(new_score)
            current_score = new_score
        
        target_scores.append(final_score)  # Score final garanti
        
        for i in range(num_updates + 1):  # +1 pour l'état final
            progress = i / num_updates
            
            # Utiliser le score pré-calculé qui garantit la croissance
            current_score = target_scores[i]
            # Facteur proportionnel au score actuel
            factor = current_score / final_score if final_score > 0 else 0
            
            # Calculer temps restant
            minutes_remaining = int(48 * (1 - progress))
            seconds_remaining = int((48 * (1 - progress) - minutes_remaining) * 60)
            time_remaining = f"{minutes_remaining}:{seconds_remaining:02d}"
            
            # Déterminer la période (1-4)
            if progress < 0.25:
                period = 1
            elif progress < 0.5:
                period = 2
            elif progress < 0.75:
                period = 3
            else:
                period = 4
            
            box_score = {
                "game_id": game_id,
                "team_id": team_id,
                "team_abbr": team_abbr,
                "matchup": matchup,
                "game_date": game_date,
                "timestamp": datetime.now().isoformat(),
                "period": period,
                "time_remaining": time_remaining,
                "progress_pct": round(progress * 100, 1),
                "is_final": i == num_updates,
                "stats": {
                    "score": current_score,  # Score garanti croissant
                    "fgm": int(final_fgm * factor),
                    "fga": max(int(final_fga * factor), 1),
                    "fg_pct": round(final_fgm / final_fga * 100, 1) if final_fga > 0 else 0,
                    "fg3m": int(final_fg3m * factor),
                    "fg3a": max(int(final_fg3a * factor), 1),
                    "fg3_pct": round(final_fg3m / final_fg3a * 100, 1) if final_fg3a > 0 else 0,
                    "ftm": int(final_ftm * factor),
                    "fta": max(int(final_fta * factor), 1),
                    "ft_pct": round(final_ftm / final_fta * 100, 1) if final_fta > 0 else 0,
                    "reb": int(final_reb * factor),
                    "ast": int(final_ast * factor),
                    "stl": int(final_stl * factor),
                    "blk": int(final_blk * factor)
                }
            }
            
            events.append(box_score)
            
        return events
        
    def write_event_to_file(self, event: Dict, index: int):
        """Écrit un événement dans un fichier JSON"""
        filename = f"{self.run_dir}/boxscore_{index:04d}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(event, f)
            return True
        except Exception as e:
            logger.error(f"❌ Erreur écriture fichier {filename}: {e}")
            return False
        
    def emit_events(self, events: List[Dict], interval: int = 30):
        """Émet les événements en écrivant des fichiers"""
        logger.info(f"📤 Émission de {len(events)} box scores (intervalle: {interval}s)")
        logger.info(f"📁 Dossier de sortie: {self.run_dir}")
        logger.info("✨ Nouveau dossier créé - pas de conflit avec les anciennes exécutions")
        
        for i, event in enumerate(events):
            try:
                # Écrire dans un fichier
                if self.write_event_to_file(event, i):
                    logger.info(f"📊 Box score {i+1}/{len(events)} écrit - "
                              f"P{event['period']} {event['time_remaining']} - "
                              f"Score: {event['stats']['score']} pts")
                
                # Attendre l'intervalle sauf pour le dernier
                if i < len(events) - 1:
                    time.sleep(interval)
                    
            except Exception as e:
                logger.error(f"❌ Erreur événement {i}: {e}")
                break
                
    def close(self):
        """Cleanup"""
        logger.info("🔌 Simulateur arrêté")
        
    def run(self, season: str = '2023_24'):
        """Exécute le simulateur"""
        try:
            # Charger un match
            game = self.load_random_game(season)
            if not game:
                logger.error("Impossible de charger un match")
                return
                
            # Générer les événements
            events = self.generate_box_score_evolution(game)
            
            # Créer un sous-dossier unique avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_dir = f"{self.output_dir}/run_{timestamp}"
            os.makedirs(self.run_dir, exist_ok=True)
            
            logger.info(f"🚀 Démarrage du simulateur de streaming")
            logger.info(f"📁 Les box scores seront écrits dans: {self.run_dir}")
            logger.info(f"⏱️  Durée estimée: {len(events) * 30} secondes ({len(events) * 0.5} minutes)")
            
            # Émettre les événements
            self.emit_events(events, interval=30)
            
            # Créer fichier de signal pour indiquer la fin
            complete_file = f"{self.run_dir}/COMPLETE"
            with open(complete_file, 'w') as f:
                f.write(f"Streaming completed at {datetime.now().isoformat()}\n")
                f.write(f"Total events: {len(events)}\n")
            logger.info(f"✅ Fichier de complétion créé: {complete_file}")
            
            logger.info("✅ Streaming terminé avec succès")
            logger.info(f"📊 {len(events)} box scores générés dans {self.run_dir}")
            
        except KeyboardInterrupt:
            logger.info("⏹️  Interrompu par l'utilisateur")
        finally:
            self.close()


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulateur de streaming NBA Box Score')
    parser.add_argument('--output-dir', type=str, default='data/streaming/input', 
                       help='Dossier de sortie (défaut: data/streaming/input)')
    parser.add_argument('--season', type=str, default='2023_24', 
                       help='Saison à utiliser (défaut: 2023_24)')
    
    args = parser.parse_args()
    
    simulator = NBABoxScoreSimulator(output_dir=args.output_dir)
    simulator.run(season=args.season)


if __name__ == "__main__":
    main()
