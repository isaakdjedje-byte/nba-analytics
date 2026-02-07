#!/usr/bin/env python3
"""
Formules NBA officielles pour métriques avancées
NBA-18: Calcul des métriques avancées
"""

def calculate_per_simplified(stats):
    """
    PER simplifié (sans stats ligue/équipe)
    Formule Hollinger simplifiée pour stats individuelles
    """
    minutes = stats.get('minutes', 0) or 0
    if minutes == 0:
        return 0.0
    
    # Points positifs
    pts_positive = (
        (stats.get('pts', 0) or 0) +
        0.4 * (stats.get('fgm', 0) or 0) +
        0.7 * (stats.get('oreb', 0) or 0) +
        0.3 * (stats.get('dreb', 0) or 0) +
        (stats.get('stl', 0) or 0) +
        0.7 * (stats.get('ast', 0) or 0) +
        0.7 * (stats.get('blk', 0) or 0)
    )
    
    # Points négatifs
    pts_negative = (
        0.7 * (stats.get('fga', 0) or 0) +
        0.4 * ((stats.get('fta', 0) or 0) - (stats.get('ftm', 0) or 0)) +
        0.4 * (stats.get('pf', 0) or 0) +
        (stats.get('tov', 0) or 0)
    )
    
    # PER = (positif - négatif) / minutes * facteur
    per = (pts_positive - pts_negative) / minutes * 48
    
    return max(0.0, min(40.0, per))  # Limite entre 0 et 40


def calculate_per_full(stats, league_stats):
    """
    PER complet avec ajustements ligue/équipe
    Formule Hollinger complète
    """
    if stats.get('minutes', 0) == 0 or not league_stats:
        return calculate_per_simplified(stats)
    
    # uPER (unadjusted PER)
    uper = (
        (stats.get('3pm', 0) * 0.5) +
        (stats.get('fgm', 0) * (2 - stats.get('team_ast', 0) / max(stats.get('team_fgm', 1), 1))) +
        (2/3) * stats.get('ast', 0) +
        (stats.get('ftm', 0) * 0.5 * (1 + (1 - stats.get('team_ast', 0) / max(stats.get('team_fgm', 1), 1)) + 
         (2/3) * (stats.get('team_ast', 0) / max(stats.get('team_fgm', 1), 1)))) -
        (stats.get('vop', 0) * stats.get('tov', 0)) -
        (stats.get('vop', 0) * stats.get('drbp', 0) * (stats.get('fga', 0) - stats.get('fgm', 0))) -
        (stats.get('vop', 0) * 0.44 * (0.44 + 0.56 * stats.get('drbp', 0)) * (stats.get('fta', 0) - stats.get('ftm', 0))) +
        (stats.get('vop', 0) * (1 - stats.get('drbp', 0)) * (stats.get('reb', 0) - stats.get('oreb', 0))) +
        (stats.get('vop', 0) * stats.get('drbp', 0) * stats.get('oreb', 0)) +
        (stats.get('vop', 0) * stats.get('stl', 0)) +
        (stats.get('vop', 0) * stats.get('drbp', 0) * stats.get('blk', 0)) -
        (stats.get('pf', 0) * ((stats.get('lg_ft', 0) / max(stats.get('lg_pf', 1), 1)) - 
         0.44 * (stats.get('lg_fta', 0) / max(stats.get('lg_pf', 1), 1)) * stats.get('vop', 0)))
    ) / stats['minutes']
    
    # Ajustement pace
    pace_adjustment = league_stats.get('pace', 100) / max(stats.get('team_pace', 100), 1)
    
    # Normalisation ligue (moyenne = 15)
    per = uper * pace_adjustment * (15.0 / max(league_stats.get('avg_uper', 15), 1))
    
    return max(0.0, min(40.0, per))


def calculate_ts(points, fga, fta):
    """
    True Shooting Percentage
    TS% = PTS / (2 * (FGA + 0.44 * FTA))
    """
    pts = points or 0
    fga = fga or 0
    fta = fta or 0
    
    denominator = 2 * (fga + 0.44 * fta)
    
    if denominator == 0:
        return 0.0
    
    return pts / denominator


def calculate_ts_pct(stats):
    """
    Wrapper pour calculate_ts avec dict
    """
    return calculate_ts(
        stats.get('pts', 0) or 0,
        stats.get('fga', 0) or 0,
        stats.get('fta', 0) or 0
    )


def calculate_efg_pct(stats):
    """
    Effective Field Goal Percentage
    eFG% = (FGM + 0.5 * 3PM) / FGA
    """
    fga = stats.get('fga', 0) or 0
    
    if fga == 0:
        return 0.0
    
    fgm = stats.get('fgm', 0) or 0
    tpm = stats.get('3pm', 0) or 0
    
    return (fgm + 0.5 * tpm) / fga


def calculate_usage_rate(player_stats, team_stats=None):
    """
    Usage Rate (USG%)
    USG% = 100 * ((FGA + 0.44*FTA + TOV) * (TmMP/5)) / (MP * (TmFGA + 0.44*TmFTA + TmTOV))
    """
    minutes = player_stats.get('minutes', 0) or 0
    
    if minutes == 0:
        return 0.0
    
    fga = player_stats.get('fga', 0) or 0
    fta = player_stats.get('fta', 0) or 0
    tov = player_stats.get('tov', 0) or 0
    
    numerator = fga + 0.44 * fta + tov
    
    if team_stats:
        team_fga = team_stats.get('fga', 0) or 0
        team_fta = team_stats.get('fta', 0) or 0
        team_tov = team_stats.get('tov', 0) or 0
        team_minutes = team_stats.get('total_minutes', minutes * 5) or (minutes * 5)
        
        denominator = (
            team_fga + 
            0.44 * team_fta + 
            team_tov
        ) * (minutes / max(team_minutes, 1))
    else:
        # Approximation sans stats équipe
        denominator = minutes * 5  # 5 joueurs sur le terrain
    
    if denominator == 0:
        return 0.0
    
    return min(100.0, (numerator / denominator) * 100)


def calculate_game_score(stats):
    """
    Game Score (John Hollinger)
    Évalue la performance d'un match
    """
    score = (
        (stats.get('pts', 0) or 0) +
        0.4 * (stats.get('fgm', 0) or 0) -
        0.7 * (stats.get('fga', 0) or 0) -
        0.4 * ((stats.get('fta', 0) or 0) - (stats.get('ftm', 0) or 0)) +
        0.7 * (stats.get('oreb', 0) or 0) +
        0.3 * (stats.get('dreb', 0) or 0) +
        (stats.get('stl', 0) or 0) +
        0.7 * (stats.get('ast', 0) or 0) +
        0.7 * (stats.get('blk', 0) or 0) -
        0.4 * (stats.get('pf', 0) or 0) -
        (stats.get('tov', 0) or 0)
    )
    
    return score


def calculate_pace(team_stats, opp_stats, minutes=48):
    """
    Pace (rythme de jeu)
    Possessions par 48 minutes
    """
    t_fga = team_stats.get('fga', 0) or 0
    t_fta = team_stats.get('fta', 0) or 0
    t_oreb = team_stats.get('oreb', 0) or 0
    t_tov = team_stats.get('tov', 0) or 0
    
    o_fga = opp_stats.get('fga', 0) or 0
    o_fta = opp_stats.get('fta', 0) or 0
    o_oreb = opp_stats.get('oreb', 0) or 0
    o_tov = opp_stats.get('tov', 0) or 0
    
    team_poss = t_fga + 0.44 * t_fta - t_oreb + t_tov
    opp_poss = o_fga + 0.44 * o_fta - o_oreb + o_tov
    
    avg_poss = (team_poss + opp_poss) / 2
    
    if minutes == 0:
        return 0.0
    
    return avg_poss * (48 / minutes)


def calculate_bmi(height_cm, weight_kg):
    """
    Body Mass Index
    BMI = poids(kg) / taille(m)²
    """
    h = height_cm or 0
    w = weight_kg or 0
    
    if h == 0:
        return 0.0
    
    height_m = h / 100
    return w / (height_m ** 2)


# ============================================================================
# FONCTIONS UDF POUR PYSPARK
# ============================================================================

def get_per_udf(use_full=False):
    """Return PER calculation as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def per_wrapper(**kwargs):
        if use_full:
            return calculate_per_full(kwargs, kwargs.get('league_stats', {}))
        else:
            return calculate_per_simplified(kwargs)
    
    return udf(per_wrapper, DoubleType())


def get_ts_udf():
    """Return True Shooting % as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def ts_wrapper(points, fga, fta):
        return calculate_ts(points, fga, fta)
    
    return udf(ts_wrapper, DoubleType())


def get_usage_rate_udf():
    """Return Usage Rate calculation as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def usg_wrapper(fga, fta, tov, minutes, team_fga, team_fta, team_tov, team_minutes):
        player_stats = {'fga': fga, 'fta': fta, 'tov': tov, 'minutes': minutes}
        team_stats = {'fga': team_fga, 'fta': team_fta, 'tov': team_tov, 'total_minutes': team_minutes}
        return calculate_usage_rate(player_stats, team_stats)
    
    return udf(usg_wrapper, DoubleType())


def get_gamescore_udf():
    """Return Game Score as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def gs_wrapper(pts, fgm, fga, fta, ftm, oreb, dreb, stl, ast, blk, pf, tov):
        stats = {
            'pts': pts, 'fgm': fgm, 'fga': fga, 'fta': fta, 'ftm': ftm,
            'oreb': oreb, 'dreb': dreb, 'stl': stl, 'ast': ast,
            'blk': blk, 'pf': pf, 'tov': tov
        }
        return calculate_game_score(stats)
    
    return udf(gs_wrapper, DoubleType())


def get_bmi_udf():
    """Return BMI calculation as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def bmi_wrapper(height_cm, weight_kg):
        return calculate_bmi(height_cm, weight_kg)
    
    return udf(bmi_wrapper, DoubleType())


# ============================================================================
# FONCTIONS DE CALCUL BATCH (pour DataFrames)
# ============================================================================

def calculate_all_metrics(player_data):
    """
    Calcule toutes les métriques pour un joueur
    Retourne un dict avec toutes les métriques
    """
    metrics = {
        'per': calculate_per_simplified(player_data),
        'ts_pct': calculate_ts_pct(player_data),
        'efg_pct': calculate_efg_pct(player_data),
        'usg_pct': calculate_usage_rate(player_data),
        'game_score': calculate_game_score(player_data),
        'bmi': calculate_bmi(
            player_data.get('height_cm', 0),
            player_data.get('weight_kg', 0)
        )
    }
    
    return metrics
