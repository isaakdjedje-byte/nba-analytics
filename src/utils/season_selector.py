#!/usr/bin/env python3
"""
Sélecteur intelligent de saison pour NBA-18
Agrège 4 méthodes : complete, max_minutes, avg_3, best_per
Poids : 35/25/20/20
"""

from typing import Dict, List, Any, Optional, Tuple
from statistics import median

from .nba_formulas import calculate_per_simplified


class SeasonSelector:
    """Sélectionne et agrège les stats selon 4 méthodes"""
    
    DEFAULT_WEIGHTS = {
        'complete': 0.35,
        'max_minutes': 0.25,
        'avg_3': 0.20,
        'best_per': 0.20
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
    
    def get_all_four_seasons(self, row_set: List[List], headers: List[str]) -> Dict[str, Any]:
        """
        Récupère les 4 saisons selon différents critères
        
        Returns:
            Dict avec 'complete', 'max_minutes', 'avg_3', 'best_per'
            Chaque clé contient {'season': str, 'stats': dict, 'available': bool}
        """
        if not row_set:
            return {key: {'available': False} for key in self.DEFAULT_WEIGHTS.keys()}
        
        return {
            'complete': self._get_last_complete(row_set, headers),
            'max_minutes': self._get_max_minutes(row_set, headers),
            'avg_3': self._get_3_season_avg(row_set, headers),
            'best_per': self._get_best_per(row_set, headers)
        }
    
    def _row_to_dict(self, row: List, headers: List[str]) -> Dict[str, Any]:
        """Convertit une row en dict"""
        return dict(zip(headers, row))
    
    def _extract_basic_stats(self, row_dict: Dict) -> Dict[str, float]:
        """Extrait les stats de base d'une row"""
        return {
            'pts': row_dict.get('PTS', 0) or 0,
            'fgm': row_dict.get('FGM', 0) or 0,
            'fga': row_dict.get('FGA', 0) or 0,
            'ftm': row_dict.get('FTM', 0) or 0,
            'fta': row_dict.get('FTA', 0) or 0,
            '3pm': row_dict.get('FG3M', 0) or 0,
            'oreb': row_dict.get('OREB', 0) or 0,
            'dreb': row_dict.get('DREB', 0) or 0,
            'reb': row_dict.get('REB', 0) or 0,
            'ast': row_dict.get('AST', 0) or 0,
            'stl': row_dict.get('STL', 0) or 0,
            'blk': row_dict.get('BLK', 0) or 0,
            'tov': row_dict.get('TOV', 0) or 0,
            'pf': row_dict.get('PF', 0) or 0,
            'minutes': row_dict.get('MIN', 0) or 1,
            'gp': row_dict.get('GP', 0) or 0
        }
    
    def _get_last_complete(self, row_set: List[List], headers: List[str]) -> Dict:
        """Dernière saison avec >= 40 matchs"""
        try:
            gp_idx = headers.index('GP')
            season_idx = headers.index('SEASON_ID')
            
            # Parcourir à l'envers (plus récent d'abord)
            for row in reversed(row_set):
                if row[gp_idx] >= 40:
                    return {
                        'available': True,
                        'season': row[season_idx],
                        'stats': self._extract_basic_stats(self._row_to_dict(row, headers)),
                        'gp': row[gp_idx]
                    }
            
            return {'available': False}
        except:
            return {'available': False}
    
    def _get_max_minutes(self, row_set: List[List], headers: List[str]) -> Dict:
        """Saison avec le maximum de minutes"""
        try:
            min_idx = headers.index('MIN')
            season_idx = headers.index('SEASON_ID')
            gp_idx = headers.index('GP')
            
            # Trouver la saison avec max minutes
            best_row = max(row_set, key=lambda x: x[min_idx] if x[min_idx] else 0)
            
            if best_row[min_idx] and best_row[min_idx] > 0:
                return {
                    'available': True,
                    'season': best_row[season_idx],
                    'stats': self._extract_basic_stats(self._row_to_dict(best_row, headers)),
                    'minutes': best_row[min_idx]
                }
            
            return {'available': False}
        except:
            return {'available': False}
    
    def _get_3_season_avg(self, row_set: List[List], headers: List[str]) -> Dict:
        """Moyenne des 3 dernières saisons"""
        try:
            last_3 = row_set[-3:] if len(row_set) >= 3 else row_set
            
            if not last_3:
                return {'available': False}
            
            season_idx = headers.index('SEASON_ID')
            seasons = [row[season_idx] for row in last_3]
            
            # Calculer moyenne de chaque stat
            avg_stats = {}
            for key in ['PTS', 'FGM', 'FGA', 'FTM', 'FTA', 'FG3M', 
                       'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'MIN', 'GP']:
                try:
                    idx = headers.index(key)
                    values = [row[idx] for row in last_3 if row[idx]]
                    avg_stats[key] = sum(values) / len(values) if values else 0
                except:
                    avg_stats[key] = 0
            
            return {
                'available': True,
                'seasons': seasons,
                'stats': self._extract_basic_stats(avg_stats)
            }
        except:
            return {'available': False}
    
    def _get_best_per(self, row_set: List[List], headers: List[str]) -> Dict:
        """Saison avec le meilleur PER"""
        try:
            season_idx = headers.index('SEASON_ID')
            
            # Calculer PER pour chaque saison
            per_list = []
            for row in row_set:
                stats = self._extract_basic_stats(self._row_to_dict(row, headers))
                per = calculate_per_simplified(stats)
                per_list.append((per, row))
            
            # Trouver meilleur PER
            best_per, best_row = max(per_list, key=lambda x: x[0])
            
            if best_per > 0:
                return {
                    'available': True,
                    'season': best_row[season_idx],
                    'stats': self._extract_basic_stats(self._row_to_dict(best_row, headers)),
                    'per_value': best_per
                }
            
            return {'available': False}
        except:
            return {'available': False}
    
    def aggregate_metrics(self, seasons_dict: Dict[str, Any], 
                         raw_weights: Dict[str, float] = None) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Agrège les métriques avec gestion des poids dynamiques
        
        Returns:
            (aggregated_stats, metadata)
        """
        weights = raw_weights or self.weights.copy()
        
        # Vérifier quelles méthodes sont disponibles
        available_methods = {
            key: data for key, data in seasons_dict.items() 
            if data.get('available', False)
        }
        
        if not available_methods:
            # Fallback : prendre dernière saison dispo
            if 'last_fallback' in seasons_dict:
                return (seasons_dict['last_fallback']['stats'], 
                       {'method': 'fallback_last', 'weight': 1.0})
            return ({}, {'method': 'none_available'})
        
        # Si une seule méthode disponible
        if len(available_methods) == 1:
            method_name = list(available_methods.keys())[0]
            return (available_methods[method_name]['stats'],
                   {'method': method_name, 'weight': 1.0})
        
        # Renormaliser les poids
        total_weight = sum(weights.get(m, 0) for m in available_methods.keys())
        if total_weight > 0:
            normalized_weights = {
                m: weights.get(m, 0) / total_weight 
                for m in available_methods.keys()
            }
        else:
            # Poids égaux si tous à 0
            n = len(available_methods)
            normalized_weights = {m: 1.0/n for m in available_methods.keys()}
        
        # Agréger chaque stat
        all_stats = [data['stats'] for data in available_methods.values()]
        aggregated = {}
        
        for key in all_stats[0].keys():
            weighted_sum = sum(
                data['stats'][key] * normalized_weights[method]
                for method, data in available_methods.items()
            )
            aggregated[key] = weighted_sum
        
        metadata = {
            'methods_used': list(available_methods.keys()),
            'weights': normalized_weights,
            'original_weights': {k: weights.get(k, 0) for k in available_methods.keys()}
        }
        
        return (aggregated, metadata)
