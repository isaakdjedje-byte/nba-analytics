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


# ============================================================================
# NBA-23: METRIQUES AVANCEES POUR CLUSTERING
# ============================================================================

def calculate_ast_pct(ast, team_fg, fg, minutes, team_minutes):
    """
    Assist Percentage (AST%)
    Formule: 100 * AST / (((MP / (Tm MP / 5)) * Tm FG) - FG)
    """
    import pandas as pd
    import numpy as np
    
    # Handle pandas Series
    if isinstance(ast, pd.Series):
        ast = ast.fillna(0)
        team_fg = team_fg.fillna(0) if isinstance(team_fg, pd.Series) else team_fg
        fg = fg.fillna(0) if isinstance(fg, pd.Series) else fg
        minutes = minutes.fillna(0) if isinstance(minutes, pd.Series) else minutes
        team_minutes = team_minutes.fillna(0) if isinstance(team_minutes, pd.Series) else team_minutes
    else:
        ast = ast or 0
        team_fg = team_fg or 0
        fg = fg or 0
        minutes = minutes or 0
        team_minutes = team_minutes or (minutes * 5)
    
    # Avoid division by zero
    denominator = (team_minutes / 5)
    mp_adjusted = np.where(denominator != 0, minutes / denominator, 0)
    
    team_fg_minus_player = (mp_adjusted * team_fg) - fg
    team_fg_minus_player = np.where(team_fg_minus_player <= 0, 1, team_fg_minus_player)  # Avoid div by zero
    
    result = (ast / team_fg_minus_player) * 100
    return np.minimum(result, 100.0)


def calculate_stl_pct(stl, opp_possessions, minutes, team_minutes):
    """
    Steal Percentage (STL%)
    Formule: 100 * (STL * (Tm MP / 5)) / (MP * Opp Poss)
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(stl, pd.Series):
        stl = stl.fillna(0)
        minutes = minutes.fillna(0) if isinstance(minutes, pd.Series) else minutes
        team_minutes = team_minutes.fillna(0) if isinstance(team_minutes, pd.Series) else team_minutes
        opp_possessions = opp_possessions.fillna(100) if isinstance(opp_possessions, pd.Series) else opp_possessions
    
    numerator = stl * (team_minutes / 5)
    denominator = minutes * opp_possessions
    denominator = np.where(denominator == 0, 1, denominator)
    
    result = (numerator / denominator) * 100
    return np.minimum(result, 100.0)


def calculate_blk_pct(blk, opp_fga, opp_3pa, minutes, team_minutes):
    """
    Block Percentage (BLK%)
    Formule: 100 * (BLK * (Tm MP / 5)) / (MP * (Opp FGA - Opp 3PA))
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(blk, pd.Series):
        blk = blk.fillna(0)
        minutes = minutes.fillna(0) if isinstance(minutes, pd.Series) else minutes
        team_minutes = team_minutes.fillna(0) if isinstance(team_minutes, pd.Series) else team_minutes
        opp_fga = opp_fga.fillna(0) if isinstance(opp_fga, pd.Series) else opp_fga
        opp_3pa = opp_3pa.fillna(0) if isinstance(opp_3pa, pd.Series) else opp_3pa
    
    opp_2pa = opp_fga - opp_3pa
    opp_2pa = np.where(opp_2pa <= 0, 1, opp_2pa)
    
    numerator = blk * (team_minutes / 5)
    denominator = minutes * opp_2pa
    denominator = np.where(denominator == 0, 1, denominator)
    
    result = (numerator / denominator) * 100
    return np.minimum(result, 100.0)


def calculate_tov_pct(tov, fga, fta):
    """
    Turnover Percentage (TOV%)
    Formule: 100 * TOV / (FGA + 0.44 * FTA + TOV)
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(tov, pd.Series):
        tov = tov.fillna(0)
        fga = fga.fillna(0) if isinstance(fga, pd.Series) else fga
        fta = fta.fillna(0) if isinstance(fta, pd.Series) else fta
    
    denominator = fga + 0.44 * fta + tov
    denominator = np.where(denominator == 0, 1, denominator)
    
    result = (tov / denominator) * 100
    return np.minimum(result, 100.0)


def calculate_trb_pct(reb, team_reb, opp_reb, minutes, team_minutes):
    """
    Total Rebound Percentage (TRB%)
    Formule: 100 * (TRB * (Tm MP / 5)) / (MP * (Tm TRB + Opp TRB))
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(reb, pd.Series):
        reb = reb.fillna(0)
        minutes = minutes.fillna(0) if isinstance(minutes, pd.Series) else minutes
        team_minutes = team_minutes.fillna(0) if isinstance(team_minutes, pd.Series) else team_minutes
        team_reb = team_reb.fillna(0) if isinstance(team_reb, pd.Series) else team_reb
        opp_reb = opp_reb.fillna(0) if isinstance(opp_reb, pd.Series) else opp_reb
    
    total_reb_available = team_reb + opp_reb
    total_reb_available = np.where(total_reb_available == 0, 1, total_reb_available)
    
    numerator = reb * (team_minutes / 5)
    denominator = minutes * total_reb_available
    denominator = np.where(denominator == 0, 1, denominator)
    
    result = (numerator / denominator) * 100
    return np.minimum(result, 100.0)


def calculate_vorp_estimated(per, minutes, lg_avg_per=15.0):
    """
    VORP (Value Over Replacement Player) estime
    Formule simplifiee: (PER - 15) * (MP / 48) / 10
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(per, pd.Series):
        per = per.fillna(0)
        minutes = minutes.fillna(0) if isinstance(minutes, pd.Series) else minutes
    
    bpm_estimated = (per - lg_avg_per) * 0.8
    vorp = (bpm_estimated + 2) * (minutes / 48) / 10
    
    return vorp


def calculate_ws_per_48(per, minutes, team_games=82):
    """
    Win Shares Per 48 Minutes (WS/48) estime
    Formule simplifiee basee sur le PER
    """
    import pandas as pd
    
    if isinstance(per, pd.Series):
        per = per.fillna(0)
    
    ws_per_48 = (per / 15.0) * 0.1
    return ws_per_48


def calculate_ftr(fta, fga):
    """
    Free Throw Rate (FTR)
    Formule: FTA / FGA
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(fta, pd.Series):
        fta = fta.fillna(0)
        fga = fga.fillna(0) if isinstance(fga, pd.Series) else fga
    
    fga = np.where(fga == 0, 1, fga)
    return fta / fga


def calculate_3par(fg3a, fga):
    """
    3-Point Attempt Rate (3PAr)
    Formule: 3PA / FGA
    """
    import pandas as pd
    import numpy as np
    
    if isinstance(fg3a, pd.Series):
        fg3a = fg3a.fillna(0)
        fga = fga.fillna(0) if isinstance(fga, pd.Series) else fga
    
    fga = np.where(fga == 0, 1, fga)
    return fg3a / fga


def calculate_all_advanced_metrics(player_data, team_data=None, opp_data=None):
    """
    Calcule toutes les metriques avancees NBA-23
    
    Args:
        player_data: dict avec stats du joueur
        team_data: dict avec stats de l'equipe (optional)
        opp_data: dict avec stats adverses (optional)
    
    Returns:
        dict avec toutes les metriques avancees
    """
    metrics = calculate_all_metrics(player_data)
    
    # Ajout metriques avancees
    minutes = player_data.get('minutes', 0)
    team_minutes = team_data.get('total_minutes', minutes * 5) if team_data else minutes * 5
    
    # Approximation sans donnees equipe complete
    team_fg = team_data.get('fgm', 0) if team_data else player_data.get('fgm', 0) * 5
    team_reb = (team_data.get('oreb', 0) + team_data.get('dreb', 0)) if team_data else player_data.get('reb', 0) * 5
    opp_reb = opp_data.get('reb', 0) if opp_data else team_reb
    opp_poss = opp_data.get('possessions', 100) if opp_data else 100
    opp_fga = opp_data.get('fga', 0) if opp_data else player_data.get('fga', 0) * 5
    opp_3pa = opp_data.get('fg3a', 0) if opp_data else player_data.get('fg3a', 0) * 5
    
    metrics.update({
        'ast_pct': calculate_ast_pct(
            player_data.get('ast', 0),
            team_fg,
            player_data.get('fgm', 0),
            minutes,
            team_minutes
        ),
        'stl_pct': calculate_stl_pct(
            player_data.get('stl', 0),
            opp_poss,
            minutes,
            team_minutes
        ),
        'blk_pct': calculate_blk_pct(
            player_data.get('blk', 0),
            opp_fga,
            opp_3pa,
            minutes,
            team_minutes
        ),
        'tov_pct': calculate_tov_pct(
            player_data.get('tov', 0),
            player_data.get('fga', 0),
            player_data.get('fta', 0)
        ),
        'trb_pct': calculate_trb_pct(
            player_data.get('reb', 0),
            team_reb,
            opp_reb,
            minutes,
            team_minutes
        ),
        'vorp': calculate_vorp_estimated(
            metrics.get('per', 0),
            minutes
        ),
        'ws_per_48': calculate_ws_per_48(
            metrics.get('per', 0),
            minutes
        ),
        'ftr': calculate_ftr(
            player_data.get('fta', 0),
            player_data.get('fga', 0)
        ),
        '3par': calculate_3par(
            player_data.get('fg3a', 0),
            player_data.get('fga', 0)
        )
    })
    
    return metrics


# =============================================================================
# VERSIONS VECTORISÉES POUR DATAFRAMES PANDAS
# NBA-23: Évite la duplication de code entre modules
# =============================================================================

def calculate_ts_pct_vectorized(df):
    """
    Calcule le True Shooting % de manière vectorisée pour DataFrames.
    
    TS% = PTS / (2 * (FGA + 0.44 * FTA))
    
    Args:
        df: DataFrame avec colonnes 'pts', 'fga', 'fta'
        
    Returns:
        pd.Series: TS% pour chaque ligne
    """
    import pandas as pd
    import numpy as np
    
    pts = df.get('pts', 0)
    fga = df.get('fga', 0)
    fta = df.get('fta', 0)
    
    denominator = 2 * (fga + 0.44 * fta)
    ts_pct = np.where(denominator > 0, pts / denominator, 0)
    
    return pd.Series(ts_pct, index=df.index)


def calculate_efg_pct_vectorized(df):
    """
    Calcule l'Effective FG % de manière vectorisée pour DataFrames.
    
    eFG% = (FGM + 0.5 * 3PM) / FGA
    
    Args:
        df: DataFrame avec colonnes 'fgm', 'fg3m', 'fga'
        
    Returns:
        pd.Series: eFG% pour chaque ligne
    """
    import pandas as pd
    import numpy as np
    
    fgm = df.get('fgm', 0)
    fg3m = df.get('fg3m', 0)
    fga = df.get('fga', 0)
    
    efg_pct = np.where(fga > 0, (fgm + 0.5 * fg3m) / fga, 0)
    
    return pd.Series(efg_pct, index=df.index)


def calculate_bmi_vectorized(df):
    """
    Calcule l'Indice de Masse Corporelle (BMI) de manière vectorisée.
    
    BMI = poids (kg) / taille (m)²
    
    Args:
        df: DataFrame avec colonnes 'weight_kg', 'height_cm'
        
    Returns:
        pd.Series: BMI pour chaque ligne
    """
    height_m = df['height_cm'] / 100
    bmi = df['weight_kg'] / (height_m ** 2)
    
    return bmi


def calculate_ftr_vectorized(df):
    """
    Calcule le Free Throw Rate (FTA / FGA) de manière vectorisée.
    
    Args:
        df: DataFrame avec colonnes 'fta', 'fga'
        
    Returns:
        pd.Series: FTR pour chaque ligne
    """
    import numpy as np
    
    fta = df.get('fta', 0)
    fga = df.get('fga', 0)
    
    ftr = np.where(fga > 0, fta / fga, 0)
    
    return ftr


def calculate_3par_vectorized(df):
    """
    Calcule le 3-Point Attempt Rate (3PA / FGA) de manière vectorisée.
    
    Args:
        df: DataFrame avec colonnes 'fg3a', 'fga'
        
    Returns:
        pd.Series: 3PAr pour chaque ligne
    """
    import numpy as np
    
    fg3a = df.get('fg3a', 0)
    fga = df.get('fga', 0)
    
    par = np.where(fga > 0, fg3a / fga, 0)
    
    return par


class NBAFormulasVectorized:
    """
    Classe utilitaire avec toutes les formules NBA vectorisées.
    
    Cette classe évite la duplication de code entre NBA-21, NBA-22 et NBA-23.
    Toutes les méthodes sont statiques et peuvent être utilisées directement
    ou via l'héritage dans BaseFeatureEngineer.
    
    Example:
        >>> from src.utils.nba_formulas import NBAFormulasVectorized
        >>> formulas = NBAFormulasVectorized()
        >>> df['ts_pct'] = formulas.calculate_ts_pct(df)
    """
    
    @staticmethod
    def calculate_ts_pct(df):
        """True Shooting % - vectorisé"""
        return calculate_ts_pct_vectorized(df)
    
    @staticmethod
    def calculate_efg_pct(df):
        """Effective FG% - vectorisé"""
        return calculate_efg_pct_vectorized(df)
    
    @staticmethod
    def calculate_bmi(df):
        """BMI - vectorisé"""
        return calculate_bmi_vectorized(df)
    
    @staticmethod
    def calculate_ftr(df):
        """Free Throw Rate - vectorisé"""
        return calculate_ftr_vectorized(df)
    
    @staticmethod
    def calculate_3par(df):
        """3-Point Attempt Rate - vectorisé"""
        return calculate_3par_vectorized(df)
