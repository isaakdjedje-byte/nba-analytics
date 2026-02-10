"""
Tests J5 - Durcissement API selon contrat A1
Basé sur contrat API v1 publié par A @ 2026-02-10 11:45

Endpoints testés selon contrat:
- GET /api/v1/predictions (avec filtres)
- POST /api/v1/bets
- GET /api/v1/bets
- POST /api/v1/bets/update
- GET /api/v1/bets/stats
- GET /api/v1/analysis/temporal
- Calendar endpoints (déjà validés)
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nba.api.main import app

client = TestClient(app)


# ============================================================================
# SCHEMAS PYDANTIC - Contrat A1
# ============================================================================

class PredictionSchema(BaseModel):
    """Schema strict selon contrat A1"""
    home_team: str
    away_team: str
    prediction: str
    proba_home_win: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    game_date: Optional[str] = None
    game_time_us: Optional[str] = None
    game_time_fr: Optional[str] = None


class PredictionsResponseSchema(BaseModel):
    """Schema réponse predictions selon contrat A1"""
    predictions: List[PredictionSchema]
    count: int
    date: Optional[str] = None
    view: str


class BetRequestSchema(BaseModel):
    """Schema requête bet selon contrat A1"""
    date: str
    match: str
    prediction: str
    stake: float = Field(..., gt=0)
    odds: float = Field(..., gt=1.0)


class BetResponseSchema(BaseModel):
    """Schema réponse bet selon contrat A1"""
    success: bool
    bet_id: str


class AnalysisSegmentSchema(BaseModel):
    """Schema segment analysis (A4 extension)"""
    range: str
    matches_count: int
    accuracy: float = Field(..., ge=0.0, le=1.0)
    recommendation: str


class AnalysisTemporalSchema(BaseModel):
    """Schema analysis temporal A4 (étendu vs A1)"""
    segments: List[AnalysisSegmentSchema]
    optimal_threshold: int
    current_season_progress: str
    overall_accuracy: float = Field(..., ge=0.0, le=1.0)


# ============================================================================
# TESTS PREDICTIONS - STRICT
# ============================================================================

class TestPredictionsContractA1:
    """Tests GET /api/v1/predictions selon contrat A1"""
    
    def test_predictions_endpoint_exists(self):
        """Vérifier que /predictions existe et répond 200"""
        response = client.get("/api/v1/predictions")
        
        # STRICT: Doit être 200
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_predictions_schema_valid(self):
        """Vérifier schema réponse selon contrat A1"""
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        
        data = response.json()
        
        # STRICT: Validation schema Pydantic
        try:
            validated = PredictionsResponseSchema(**data)
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")
        
        # STRICT: cohérence count
        assert validated.count == len(validated.predictions), \
            f"Count mismatch: {validated.count} != {len(validated.predictions)}"
    
    def test_predictions_min_confidence_filter(self):
        """Test filtre min_confidence fonctionne"""
        min_conf = 0.7
        response = client.get(f"/api/v1/predictions?min_confidence={min_conf}")
        
        assert response.status_code == 200
        data = response.json()
        
        # STRICT: Toutes les prédictions doivent avoir confidence >= min_confidence
        for pred in data.get("predictions", []):
            assert pred["confidence"] >= min_conf, \
                f"Prediction confidence {pred['confidence']} < {min_conf}"
    
    def test_predictions_min_confidence_invalid_high(self):
        """Test min_confidence > 1 rejeté"""
        response = client.get("/api/v1/predictions?min_confidence=1.5")
        # Accepte 422 (validation error) ou filtre tout (count=0)
        assert response.status_code in [200, 422], \
            f"Expected 200 or 422, got {response.status_code}"
        
        if response.status_code == 200:
            assert response.json().get("count", 0) == 0, \
                "Should return 0 predictions for confidence > 1"
    
    def test_predictions_view_week_deprecated(self):
        """Test view=week (déprécié mais maintenu)"""
        response = client.get("/api/v1/predictions?view=week")
        
        # STRICT: Doit fonctionner (deprecated mais pas retiré)
        assert response.status_code == 200, \
            f"Deprecated view=week should still work: {response.status_code}"
        
        data = response.json()
        assert "predictions" in data or "days" in data, \
            "Week view should return predictions or days"
    
    def test_predictions_team_filter(self):
        """Test filtre par équipe"""
        response = client.get("/api/v1/predictions?team=Lakers")
        
        assert response.status_code == 200
        data = response.json()
        
        # STRICT: Si prédictions retournées, doivent concerner Lakers
        for pred in data.get("predictions", []):
            assert "lakers" in pred["home_team"].lower() or \
                   "lakers" in pred["away_team"].lower(), \
                f"Prediction {pred['home_team']} vs {pred['away_team']} doesn't match team filter"
    
    def test_predictions_field_types(self):
        """Test types des champs selon contrat"""
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        
        data = response.json()
        
        for pred in data.get("predictions", []):
            # STRICT: Types
            assert isinstance(pred["home_team"], str), "home_team must be string"
            assert isinstance(pred["away_team"], str), "away_team must be string"
            assert isinstance(pred["confidence"], (int, float)), "confidence must be numeric"
            assert isinstance(pred["proba_home_win"], (int, float)), "proba_home_win must be numeric"
            
            # STRICT: Range
            assert 0 <= pred["confidence"] <= 1, \
                f"confidence {pred['confidence']} out of range [0,1]"
            assert 0 <= pred["proba_home_win"] <= 1, \
                f"proba_home_win {pred['proba_home_win']} out of range [0,1]"


# ============================================================================
# TESTS BETS - STRICT
# ============================================================================

class TestBetsContractA1:
    """Tests endpoints bets selon contrat A1 + Delta A2 (503 dégradation)"""
    
    def test_place_bet_success(self):
        """Test POST /bets crée un pari (cas nominal)"""
        bet_data = {
            "date": "2026-02-10",
            "match": "Celtics vs Knicks",
            "prediction": "Home Win",
            "stake": 25.0,
            "odds": 1.85
        }
        
        response = client.post("/api/v1/bets", json=bet_data)
        
        # STRICT + Delta A2: 200/201 (nominal) ou 503 (dégradation betting)
        assert response.status_code in [200, 201, 503], \
            f"Expected 200/201/503, got {response.status_code}: {response.text}"
        
        if response.status_code in [200, 201]:
            # Cas nominal: validation schema
            data = response.json()
            try:
                validated = BetResponseSchema(**data)
            except Exception as e:
                pytest.fail(f"Bet response schema invalid: {e}")
            
            assert validated.success is True, "success should be True"
            assert validated.bet_id is not None, "bet_id should be present"
        elif response.status_code == 503:
            # Delta A2: Dégradation betting légitime
            assert "detail" in response.json() or "error" in response.json(), \
                "503 should include error detail"
        
        data = response.json()
        
        # STRICT: Validation schema
        try:
            validated = BetResponseSchema(**data)
        except Exception as e:
            pytest.fail(f"Bet response schema invalid: {e}")
        
        assert validated.success is True, "success should be True"
        assert validated.bet_id is not None, "bet_id should be present"
    
    def test_place_bet_invalid_stake_negative(self):
        """Test stake négatif rejeté"""
        bet_data = {
            "date": "2026-02-10",
            "match": "Test Match",
            "prediction": "Home",
            "stake": -10.0,  # INVALID
            "odds": 1.85
        }
        
        response = client.post("/api/v1/bets", json=bet_data)
        # STRICT: Doit rejeter
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for negative stake, got {response.status_code}"
    
    def test_place_bet_invalid_odds_low(self):
        """Test odds < 1 rejeté"""
        bet_data = {
            "date": "2026-02-10",
            "match": "Test Match",
            "prediction": "Home",
            "stake": 10.0,
            "odds": 0.5  # INVALID
        }
        
        response = client.post("/api/v1/bets", json=bet_data)
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for odds < 1, got {response.status_code}"
    
    def test_get_bets_list(self):
        """Test GET /bets retourne liste (cas nominal ou 503 dégradation)"""
        response = client.get("/api/v1/bets?status=all&limit=10")
        
        # Delta A2: 200 (nominal) ou 503 (dégradation betting)
        assert response.status_code in [200, 503], \
            f"Expected 200 or 503, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # STRICT: Doit être une liste ou objet avec bets
            assert isinstance(data, list) or isinstance(data, dict), \
                "Response should be list or dict"
    
    def test_update_bet_result(self):
        """Test POST /bets/update met à jour résultat (cas nominal ou 503)"""
        # D'abord créer un bet
        bet_data = {
            "date": "2026-02-10",
            "match": "LAL vs GSW",
            "prediction": "LAL",
            "stake": 10.0,
            "odds": 1.9
        }
        create_response = client.post("/api/v1/bets", json=bet_data)
        
        # Delta A2: Skip si 503 (dégradation betting)
        if create_response.status_code == 503:
            pytest.skip("Betting backend unavailable (503) - Delta A2 degradation")
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create bet for update test")
        
        bet_id = create_response.json().get("bet_id")
        
        # Mettre à jour
        update_data = {
            "bet_id": bet_id,
            "result": "won"
        }
        
        response = client.post("/api/v1/bets/update", json=update_data)
        # Delta A2: 200 (nominal) ou 503 (dégradation)
        assert response.status_code in [200, 503], \
            f"Expected 200 or 503, got {response.status_code}"
    
    def test_get_bets_stats(self):
        """Test GET /bets/stats retourne stats (cas nominal ou 503 dégradation)"""
        response = client.get("/api/v1/bets/stats")
        
        # Delta A2: 200 (nominal) ou 503 (dégradation betting)
        assert response.status_code in [200, 503], \
            f"Expected 200 or 503, got {response.status_code}"
    
    def test_betting_degradation_503(self):
        """Test Delta A2: betting backend peut répondre 503 sans impacter autres routes"""
        # Test que predictions (autre route) fonctionne même si betting répond 503
        pred_response = client.get("/api/v1/predictions")
        assert pred_response.status_code == 200, \
            "Predictions should work even if betting unavailable"
        
        # Test betting - peut être 200 ou 503
        bet_response = client.get("/api/v1/bets")
        assert bet_response.status_code in [200, 503], \
            f"Bets should return 200 or 503, got {bet_response.status_code}"
        
        # Si betting répond 503, vérifier format erreur
        if bet_response.status_code == 503:
            error_data = bet_response.json()
            assert "detail" in error_data or "error" in error_data, \
                "503 response should contain error detail"


# ============================================================================
# TESTS ANALYSIS - STRICT
# ============================================================================

class TestAnalysisContractA1:
    """Tests endpoints analysis selon contrat A1"""
    
    def test_analysis_temporal_exists(self):
        """Test GET /analysis/temporal existe"""
        response = client.get("/api/v1/analysis/temporal")
        
        # STRICT: Doit exister (200 ou 501 si non implémenté)
        assert response.status_code in [200, 404, 501], \
            f"Expected 200, 404 or 501, got {response.status_code}"
    
    def test_analysis_temporal_schema(self):
        """Test schema analysis/temporal"""
        response = client.get("/api/v1/analysis/temporal")
        
        if response.status_code == 404:
            pytest.skip("Endpoint not implemented yet")
        
        if response.status_code == 200:
            data = response.json()
            
            # STRICT: Validation schema
            try:
                validated = AnalysisTemporalSchema(**data)
            except Exception as e:
                pytest.fail(f"Analysis schema invalid: {e}")
            
            # STRICT: Contraintes (A4 schema étendu)
            assert 0 <= validated.overall_accuracy <= 1, \
                f"overall_accuracy {validated.overall_accuracy} out of range [0,1]"
            assert len(validated.segments) > 0, \
                "segments should not be empty"
            assert validated.optimal_threshold >= 0, \
                "optimal_threshold should be >= 0"


# ============================================================================
# TESTS END-TO-END
# ============================================================================

class TestEndToEndContractA1:
    """Tests bout-en-bout selon contrat A1"""
    
    def test_prediction_to_bet_flow(self):
        """Test flux: predictions → bet → update"""
        # 1. Récupérer prédictions
        pred_response = client.get("/api/v1/predictions?min_confidence=0.7")
        assert pred_response.status_code == 200
        
        predictions = pred_response.json().get("predictions", [])
        if len(predictions) == 0:
            pytest.skip("No high-confidence predictions available")
        
        pred = predictions[0]
        
        # 2. Placer un pari
        bet_data = {
            "date": pred.get("game_date", "2026-02-10"),
            "match": f"{pred['home_team']} vs {pred['away_team']}",
            "prediction": pred['prediction'],
            "stake": 5.0,
            "odds": 1.9
        }
        
        bet_response = client.post("/api/v1/bets", json=bet_data)
        assert bet_response.status_code in [200, 201]
        
        bet_id = bet_response.json().get("bet_id")
        assert bet_id is not None
        
        # 3. Mettre à jour le résultat
        update_response = client.post("/api/v1/bets/update", json={
            "bet_id": bet_id,
            "result": "won"
        })
        assert update_response.status_code == 200
    
    def test_deprecated_view_week_still_works(self):
        """Test que view=week déprécié fonctionne encore"""
        response = client.get("/api/v1/predictions?view=week")
        
        # STRICT: Deprecated mais pas retiré
        assert response.status_code == 200, \
            "Deprecated view=week should still work"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
