def calculate_per(stats, league_stats):
    uPER = (
        (stats['fgm'] * 1.0) +
        (stats['3pm'] * 0.5) +
        (stats['ftm'] * 0.5) +
        (stats['rebounds'] * 0.5) +
        (stats['assists'] * 1.0) +
        (stats['steals'] * 1.0) +
        (stats['blocks'] * 1.0) -
        (stats['fga'] - stats['fgm']) * 0.5 -
        (stats['fta'] - stats['ftm']) * 0.5 -
        (stats['turnovers'] * 1.0)
    ) / stats['minutes']
    
    # Ajustement pace
    pace_adjustment = league_stats['pace'] / stats['team_pace']
    
    # Normalisation ligue
    per = uPER * pace_adjustment * (15 / league_stats['avg_uper'])
    
    return per

def calculate_usage_rate(player_stats, team_stats):
    numerator = (
        player_stats['fga'] + 
        0.44 * player_stats['fta'] + 
        player_stats['turnovers']
    )
    
    denominator = (
        team_stats['fga'] + 
        0.44 * team_stats['fta'] + 
        team_stats['turnovers']
    ) * (player_stats['minutes'] / team_stats['total_minutes'])
    
    return (numerator / denominator) * 100

def calculate_pace(team_stats, opp_stats, minutes=48):
    team_poss = (
        team_stats['fga'] + 
        0.44 * team_stats['fta'] - 
        team_stats['oreb'] + 
        team_stats['tov']
    )
    
    opp_poss = (
        opp_stats['fga'] + 
        0.44 * opp_stats['fta'] - 
        opp_stats['oreb'] + 
        opp_stats['tov']
    )
    
    avg_poss = (team_poss + opp_poss) / 2
    
    return avg_poss * (48 / minutes)


def calculate_ts(points, fga, fta):
    return points / (2 * (fga + 0.44 * fta))

# ============================================================================
# FONCTIONS UDF POUR PYSPARK
# ============================================================================
def get_per_udf():
    """Return PER calculation as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def per_wrapper(uper, team_pace, league_pace):
        return calculate_per(uper, team_pace, league_pace)
    
    return udf(per_wrapper, DoubleType())
def get_usage_rate_udf():
    """Return Usage Rate calculation as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def usg_wrapper(fga, fta, tov, minutes, team_minutes, team_fga, team_fta, team_tov):
        return calculate_usage_rate(fga, fta, tov, minutes, team_minutes, 
                                   team_fga, team_fta, team_tov)
    
    return udf(usg_wrapper, DoubleType())
def get_ts_udf():
    """Return True Shooting % as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def ts_wrapper(points, fga, fta):
        return calculate_true_shooting(points, fga, fta)
    
    return udf(ts_wrapper, DoubleType())
def get_gamescore_udf():
    """Return Game Score as Spark UDF"""
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    
    def gs_wrapper(points, fgm, fga, fta, ftm, oreb, dreb, stl, ast, blk, pf, tov):
        stats = {
            'points': points, 'fgm': fgm, 'fga': fga, 'fta': fta, 'ftm': ftm,
            'oreb': oreb, 'dreb': dreb, 'steals': stl, 'assists': ast,
            'blocks': blk, 'pf': pf, 'turnovers': tov
        }
        return calculate_game_score(stats)
    
    return udf(gs_wrapper, DoubleType())
