#!/usr/bin/env python3
"""
NBA-23: Matcher hiérarchique des archétypes

Remplace le système de matching simple par un algorithme hiérarchique
qui classe les joueurs en niveaux: ELITE > STARTER > ROLE_PLAYER > BENCH
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.spatial.distance import cosine


@dataclass
class ArchetypeDefinition:
    """Définition d'un archétype avec ses critères"""
    archetype_id: str
    name: str
    name_fr: str
    description: str
    level: str  # 'ELITE', 'STARTER', 'ROLE_PLAYER', 'BENCH'
    primary_criteria: Dict[str, Tuple[str, float]]  # {feature: (operator, threshold)}
    secondary_criteria: Dict[str, Tuple[str, float]]
    key_features: List[str]
    examples: List[str]


class HierarchicalArchetypeMatcher:
    """
    Matcher hiérarchique des archétypes NBA.
    
    Taxonomie:
    - ELITE (PER >= 25): Scoreurs, Playmakers, Two-way stars
    - STARTER (PER 17-25): Offensifs, Défensifs, Balanced  
    - ROLE_PLAYER (PER 11-17): 3-and-D, Energy, Specialists
    - BENCH (PER < 11): Development, Specialists limités
    
    Utilise la similarité cosinus pour matcher les profils aux définitions.
    """
    
    # Définitions des archétypes par niveau
    ARCHETYPES = {
        # === ELITE (PER >= 25) ===
        'ELITE_SCORER': ArchetypeDefinition(
            archetype_id='ELITE_SCORER',
            name='Elite Scorer',
            name_fr='Scoreur Élite',
            description='Scoreur à haut volume avec efficacité exceptionnelle',
            level='ELITE',
            primary_criteria={
                'per': ('>=', 25.0),
                'pts_per_36': ('>=', 26.0),
                'ts_pct': ('>=', 0.58)
            },
            secondary_criteria={
                'usg_pct': ('>=', 28.0),
                'efg_pct': ('>=', 0.52)
            },
            key_features=['per', 'pts_per_36', 'ts_pct', 'usg_pct'],
            examples=['Kevin Durant', 'Stephen Curry', 'Joel Embiid']
        ),
        
        'ELITE_PLAYMAKER': ArchetypeDefinition(
            archetype_id='ELITE_PLAYMAKER',
            name='Elite Playmaker',
            name_fr='Créateur Élite',
            description='Créateur d\'occasions avec hauts assists et faibles pertes',
            level='ELITE',
            primary_criteria={
                'per': ('>=', 25.0),
                'ast_per_36': ('>=', 9.0),
                'ast_to_ratio': ('>=', 3.5)
            },
            secondary_criteria={
                'usg_pct': ('>=', 24.0),
                'pts_per_36': ('>=', 18.0)
            },
            key_features=['per', 'ast_per_36', 'ast_to_ratio', 'usg_pct'],
            examples=['Chris Paul', 'Trae Young', 'Tyrese Haliburton']
        ),
        
        'ELITE_TWO_WAY': ArchetypeDefinition(
            archetype_id='ELITE_TWO_WAY',
            name='Elite Two-Way',
            name_fr='Élite Double-Sens',
            description='Star équilibrée offense/défense',
            level='ELITE',
            primary_criteria={
                'per': ('>=', 25.0),
                'pts_per_36': ('>=', 22.0),
                'stl_per_36': ('>=', 1.3)
            },
            secondary_criteria={
                'defensive_activity': ('>=', 2.5),
                'versatility_score': ('>=', 0.7)
            },
            key_features=['per', 'pts_per_36', 'stl_per_36', 'versatility_score'],
            examples=['LeBron James', 'Kawhi Leonard', 'Jimmy Butler']
        ),
        
        'ELITE_BIG': ArchetypeDefinition(
            archetype_id='ELITE_BIG',
            name='Elite Big',
            name_fr='Grand Élite',
            description='Grand homme dominant protection et rebonds',
            level='ELITE',
            primary_criteria={
                'per': ('>=', 23.0),
                'blk_per_36': ('>=', 2.0),
                'reb_per_36': ('>=', 11.0),
                'height_cm': ('>=', 208.0)
            },
            secondary_criteria={
                'ts_pct': ('>=', 0.60),
                'rim_protection_index': ('>=', 15.0)
            },
            key_features=['per', 'blk_per_36', 'reb_per_36', 'height_cm'],
            examples=['Rudy Gobert', 'Brook Lopez', 'Myles Turner']
        ),
        
        # === STARTER (PER 17-25) ===
        'STARTER_OFFENSIVE': ArchetypeDefinition(
            archetype_id='STARTER_OFFENSIVE',
            name='Offensive Starter',
            name_fr='Starter Offensif',
            description='Starter avec apport offensif majeur',
            level='STARTER',
            primary_criteria={
                'per': ('range', (17.0, 25.0)),
                'pts_per_36': ('>=', 20.0),
                'usg_pct': ('>=', 25.0)
            },
            secondary_criteria={
                'ts_pct': ('>=', 0.55),
                'offensive_load': ('>=', 5.0)
            },
            key_features=['per', 'pts_per_36', 'usg_pct', 'ts_pct'],
            examples=['Bradley Beal', 'Zach LaVine', 'DeMar DeRozan']
        ),
        
        'STARTER_DEFENSIVE': ArchetypeDefinition(
            archetype_id='STARTER_DEFENSIVE',
            name='Defensive Starter',
            name_fr='Starter Défensif',
            description='Starter avec impact défensif majeur',
            level='STARTER',
            primary_criteria={
                'per': ('range', (15.0, 22.0)),
                'stl_per_36': ('>=', 1.5),
                'defensive_activity': ('>=', 3.0)
            },
            secondary_criteria={
                'pts_per_36': ('<', 18.0),
                'usg_pct': ('<', 22.0)
            },
            key_features=['per', 'stl_per_36', 'defensive_activity', 'pts_per_36'],
            examples=['Alex Caruso', 'Dyson Daniels', 'Jrue Holiday']
        ),
        
        'STARTER_BALANCED': ArchetypeDefinition(
            archetype_id='STARTER_BALANCED',
            name='Balanced Starter',
            name_fr='Starter Équilibré',
            description='Starter polyvalent sans faiblesse majeure',
            level='STARTER',
            primary_criteria={
                'per': ('range', (17.0, 23.0)),
                'versatility_score': ('>=', 0.6),
                'consistency_score': ('>=', 0.6)
            },
            secondary_criteria={
                'pts_per_36': ('range', (15.0, 22.0)),
                'ast_per_36': ('>=', 4.0)
            },
            key_features=['per', 'versatility_score', 'consistency_score'],
            examples=['Jaylen Brown', 'Paul George', 'Mikal Bridges']
        ),
        
        # === ROLE PLAYER (PER 11-17) ===
        'ROLE_3_AND_D': ArchetypeDefinition(
            archetype_id='ROLE_3_AND_D',
            name='3-and-D Wing',
            name_fr='Ailier 3-et-D',
            description='Spécialiste 3 points avec défense solide',
            level='ROLE_PLAYER',
            primary_criteria={
                'per': ('range', (11.0, 17.0)),
                'three_pt_rate': ('>=', 0.45),
                'stl_per_36': ('>=', 1.2)
            },
            secondary_criteria={
                'usg_pct': ('<', 20.0),
                'ts_pct': ('>=', 0.55)
            },
            key_features=['per', 'three_pt_rate', 'stl_per_36', 'ts_pct'],
            examples=['Mikal Bridges', 'OG Anunoby', 'Dorian Finney-Smith']
        ),
        
        'ROLE_ENERGY_BIG': ArchetypeDefinition(
            archetype_id='ROLE_ENERGY_BIG',
            name='Energy Big',
            name_fr='Grand Énergie',
            description='Grand homme à haute énergie sortant du banc',
            level='ROLE_PLAYER',
            primary_criteria={
                'per': ('range', (11.0, 16.0)),
                'reb_per_36': ('>=', 12.0),
                'pf_per_36': ('>=', 4.5),
                'minutes_per_game': ('<', 24.0)
            },
            secondary_criteria={
                'blk_per_36': ('>=', 1.0),
                'height_cm': ('>=', 203.0)
            },
            key_features=['per', 'reb_per_36', 'pf_per_36', 'minutes_per_game'],
            examples=['Montrezl Harrell', 'Isaiah Stewart', 'Naz Reid']
        ),
        
        'ROLE_SHOOTER': ArchetypeDefinition(
            archetype_id='ROLE_SHOOTER',
            name='Floor Spacer',
            name_fr='Espaceur',
            description='Spécialiste du tir à longue distance',
            level='ROLE_PLAYER',
            primary_criteria={
                'per': ('range', (11.0, 16.0)),
                'three_pt_rate': ('>=', 0.55),
                'ts_pct': ('>=', 0.58)
            },
            secondary_criteria={
                'usg_pct': ('<', 18.0),
                'pts_per_36': ('range', (12.0, 18.0))
            },
            key_features=['per', 'three_pt_rate', 'ts_pct'],
            examples=['Doug McDermott', 'Bryn Forbes', 'Patty Mills']
        ),
        
        'ROLE_DEFENSIVE': ArchetypeDefinition(
            archetype_id='ROLE_DEFENSIVE',
            name='Defensive Specialist',
            name_fr='Spécialiste Défensif',
            description='Défenseur d\'élite avec rôle offensif limité',
            level='ROLE_PLAYER',
            primary_criteria={
                'per': ('range', (10.0, 15.0)),
                'stl_per_36': ('>=', 1.8),
                'defensive_activity': ('>=', 3.0),
                'pts_per_36': ('<', 12.0)
            },
            secondary_criteria={
                'usg_pct': ('<', 15.0),
                'three_pt_rate': ('<', 0.35)
            },
            key_features=['per', 'stl_per_36', 'defensive_activity', 'pts_per_36'],
            examples=['Matisse Thybulle', 'Dyson Daniels', 'Kris Dunn']
        ),
        
        # === BENCH (PER < 11) ===
        'BENCH_ENERGY': ArchetypeDefinition(
            archetype_id='BENCH_ENERGY',
            name='Bench Energy',
            name_fr='Énergie Banc',
            description='Joueur d\'énergie sur le banc',
            level='BENCH',
            primary_criteria={
                'per': ('<', 11.0),
                'minutes_per_game': ('<', 18.0),
                'pf_per_36': ('>=', 5.0)
            },
            secondary_criteria={
                'consistency_score': ('<', 0.5)
            },
            key_features=['per', 'minutes_per_game', 'pf_per_36'],
            examples=['Jarred Vanderbilt', 'Naz Reid', 'Trendon Watford']
        ),
        
        'BENCH_DEVELOPMENT': ArchetypeDefinition(
            archetype_id='BENCH_DEVELOPMENT',
            name='Development Player',
            name_fr='Joueur en Développement',
            description='Jeune joueur en développement',
            level='BENCH',
            primary_criteria={
                'per': ('<', 12.0),
                'years_active': ('<', 3),
                'minutes_per_game': ('<', 20.0)
            },
            secondary_criteria={
                'starter_ratio': ('<', 0.3)
            },
            key_features=['per', 'years_active', 'minutes_per_game'],
            examples=['Rookies et sophomores limités']
        ),
        
        'BENCH_VETERAN': ArchetypeDefinition(
            archetype_id='BENCH_VETERAN',
            name='Veteran Bench',
            name_fr='Vétéran Banc',
            description='Vétéran en fin de carrière sur le banc',
            level='BENCH',
            primary_criteria={
                'per': ('<', 12.0),
                'years_active': ('>=', 10),
                'minutes_per_game': ('<', 18.0)
            },
            secondary_criteria={
                'consistency_score': ('>=', 0.4)
            },
            key_features=['per', 'years_active', 'minutes_per_game'],
            examples=['Vétérans en fin de contrat']
        )
    }
    
    def match(self, player_profile: Dict) -> Tuple[str, float, str]:
        """
        Trouve le meilleur archétype pour un profil de joueur.
        
        Args:
            player_profile: Dict avec les features moyennes du joueur
            
        Returns:
            Tuple (archetype_id, confidence_score, level)
        """
        # Étape 1: Déterminer le niveau (ELITE/STARTER/ROLE/BENCH)
        per = player_profile.get('per', 15.0)
        level = self._get_level(per)
        
        # Étape 2: Filtrer les archétypes du niveau
        candidates = self._get_archetypes_by_level(level)
        
        if not candidates:
            return f"{level}_GENERIC", 0.5, level
        
        # Étape 3: Calculer le score de matching pour chaque candidat
        best_match = None
        best_score = 0.0
        
        for archetype_id, archetype in candidates.items():
            score = self._calculate_match_score(player_profile, archetype)
            
            if score > best_score:
                best_score = score
                best_match = archetype_id
        
        # Étape 4: Vérifier si le score est suffisant
        if best_score < 0.4:
            # Score trop faible, retourne un générique
            return f"{level}_GENERIC", best_score, level
        
        return best_match, best_score, level
    
    def _get_level(self, per: float) -> str:
        """Détermine le niveau basé sur le PER."""
        if per >= 25.0:
            return 'ELITE'
        elif per >= 17.0:
            return 'STARTER'
        elif per >= 11.0:
            return 'ROLE_PLAYER'
        else:
            return 'BENCH'
    
    def _get_archetypes_by_level(self, level: str) -> Dict[str, ArchetypeDefinition]:
        """Retourne tous les archétypes d'un niveau donné."""
        return {
            k: v for k, v in self.ARCHETYPES.items() 
            if v.level == level
        }
    
    def _calculate_match_score(self, profile: Dict, 
                               archetype: ArchetypeDefinition) -> float:
        """
        Calcule le score de matching entre un profil et un archétype.
        
        Utilise une combinaison de:
        - Score des critères primaires (60%)
        - Score des critères secondaires (30%)
        - Bonus de niveau (10%)
        """
        primary_score = self._score_criteria(profile, archetype.primary_criteria)
        secondary_score = self._score_criteria(profile, archetype.secondary_criteria)
        
        # Score pondéré
        total_score = 0.6 * primary_score + 0.3 * secondary_score + 0.1
        
        return min(1.0, max(0.0, total_score))
    
    def _score_criteria(self, profile: Dict, 
                        criteria: Dict[str, Tuple[str, float]]) -> float:
        """
        Calcule le score pour un ensemble de critères.
        
        Retourne un score entre 0 et 1 basé sur le % de critères satisfaits.
        """
        if not criteria:
            return 0.5
        
        satisfied = 0
        total_weight = 0
        
        for feature, (operator, threshold) in criteria.items():
            weight = 1.0
            value = profile.get(feature, 0)
            
            # Vérifie si le critère est satisfait
            is_satisfied = False
            
            if operator == '>=':
                is_satisfied = value >= threshold
            elif operator == '<=':
                is_satisfied = value <= threshold
            elif operator == '<':
                is_satisfied = value < threshold
            elif operator == '>':
                is_satisfied = value > threshold
            elif operator == 'range':
                low, high = threshold
                is_satisfied = low <= value <= high
            
            if is_satisfied:
                satisfied += weight
            
            total_weight += weight
        
        return satisfied / total_weight if total_weight > 0 else 0.0
    
    def get_archetype_info(self, archetype_id: str) -> Optional[ArchetypeDefinition]:
        """Retourne les informations d'un archétype."""
        return self.ARCHETYPES.get(archetype_id)
    
    def get_all_archetypes(self) -> List[str]:
        """Retourne la liste de tous les IDs d'archétypes."""
        return list(self.ARCHETYPES.keys())
    
    def get_archetypes_by_level(self, level: str) -> List[str]:
        """Retourne les IDs des archétypes d'un niveau."""
        return [k for k, v in self.ARCHETYPES.items() if v.level == level]


if __name__ == "__main__":
    print("NBA-23 Hierarchical Archetype Matcher")
    print("=" * 60)
    
    matcher = HierarchicalArchetypeMatcher()
    
    print(f"\nTotal archétypes définis: {len(matcher.ARCHETYPES)}")
    
    for level in ['ELITE', 'STARTER', 'ROLE_PLAYER', 'BENCH']:
        archs = matcher.get_archetypes_by_level(level)
        print(f"\n{level}: {len(archs)} archétypes")
        for arch_id in archs[:3]:
            arch = matcher.get_archetype_info(arch_id)
            print(f"  - {arch_id}: {arch.name_fr}")
    
    # Test avec un profil exemple
    test_profile = {
        'per': 27.5,
        'pts_per_36': 28.0,
        'ts_pct': 0.62,
        'usg_pct': 32.0
    }
    
    archetype_id, confidence, level = matcher.match(test_profile)
    print(f"\nTest profil (PER 27.5):")
    print(f"  Match: {archetype_id}")
    print(f"  Confiance: {confidence:.2%}")
    print(f"  Niveau: {level}")
