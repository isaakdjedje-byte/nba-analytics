"""
Variante A - Tests J5 avec CONTRAT API V1 FINAL
À utiliser dès réception de A1_VALIDATED + contrat API v1

Cette variante suppose que tous les endpoints attendus par le frontend
sont implémentés et stabilisés selon le contrat A1.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from nba.api.main import app

client = TestClient(app)


# ============================================================================
# SCHEMAS PYDANTIC POUR VALIDATION STRICTE (Basés sur contrat A1)
# ============================================================================

class PredictionResponse(BaseModel):
    """Schema strict pour endpoint /predictions"""
    home_team: str
    away_team: str
    prediction: str  # 'home' | 'away'
    proba_home_win: float
    confidence: float  # 0.0 - 1.0
    recommendation: str  # 'A+' | 'A' | 'B' | 'C'
    game_date: Optional[str]  # YYYY-MM-DD
    game_time_us: Optional[str]
    game_time_fr: Optional[str]


class PredictionsListResponse(BaseModel):
    """Schema pour liste de prédictions"""
    predictions: list[PredictionResponse]
    total: int
    filtered: int


class BetResponse(BaseModel):
    """Schema strict pour bets"""
    bet_id: str
    date: str
    match: str
    prediction: str
    stake: float
    odds: float
    status: str  # 'pending' | 'won' | 'lost'


class AnalysisTemporalResponse(BaseModel):
    """Schema pour analysis/temporal"""
    period: str
    accuracy: float
    total_predictions: int


# ============================================================================
# TESTS PREDICTIONS - ASSERTIONS STRICTES
# ============================================================================

class TestPredictionsStrict:
    """Tests /api/v1/predictions avec validations strictes"""
    
    def test_get_all_predictions_success(self):
        """Test GET /predictions retourne 200 avec schema valide"""
        response = client.get("/api/v1/predictions")
        
        # STRICT: Doit être 200, pas 404 ni 500
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # STRICT: Validation schema via Pydantic
        try:
            validated = PredictionsListResponse(**data)
        except ValidationError as e:
            pytest.fail(f"Response schema invalid: {e}")
        
        # STRICT: Assertions métier
        assert len(validated.predictions) > 0, "Should return at least one prediction"
        assert validated.total >= validated.filtered, "Total should >= filtered"
    
    def test_get_predictions_with_min_confidence(self):
        """Test filtre min_confidence fonctionne correctement"""
        min_conf = 0.7
        response = client.get(f"/api/v1/predictions?min_confidence={min_conf}")
        
        assert response.status_code == 200
        data = response.json()
        
        # STRICT: Toutes les prédictions doivent respecter le filtre
        for pred in data.get("predictions", []):
            assert pred["confidence"] >= min_conf, \
                f"Prediction confidence {pred['confidence']} < {min_conf}"
    
    def test_get_predictions_week_view(self):
        """Test vue semaine retourne structure correcte"""
        response = client.get("/api/v1/predictions?view=week")
        
        assert response.status_code == 200
        data = response.json()
        
        # STRICT: Validation schema
        validated = PredictionsListResponse(**data)
        
        # STRICT: Assertions vue semaine
        assert validated.total > 0, "Week view should have predictions"
    
    def test_get_predictions_by_date(self):
        """Test GET /calendar/date/{date} retourne prédictions"""
        test_date = "2025-02-10"
        response = client.get(f"/api/v1/calendar/date/{test_date}")
        
        assert response.status_code == 200
        data = response.json()
        
        # STRICT: Structure CalendarResponse attendue
        assert "matches" in data or "predictions" in data, \
            "Response should contain matches or predictions"
    
    def test_prediction_schema_validation(self):
        """Test que chaque prédiction respecte le schema strict"""
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        
        predictions = response.json().get("predictions", [])
        assert len(predictions) > 0, "Need predictions to validate schema"
        
        for pred in predictions:
            # STRICT: Validation individuelle
            try:
                validated = PredictionResponse(**pred)
            except ValidationError as e:
                pytest.fail(f"Invalid prediction schema: {e}")
            
            # STRICT: Contraintes métier
            assert 0 <= validated.confidence <= 1, \
                f"Confidence {validated.confidence} out of range [0,1]"
            assert validated.proba_home_win >= 0, \
                f"Probability {validated.proba_home_win} should be >= 0"
            assert validated.recommendation in ['A+', 'A', 'B', 'C'], \
                f"Invalid recommendation: {validated.recommendation}"
    
    def test_predictions_invalid_params(self):
        """Test gestion erreurs paramètres invalides"""
        # min_confidence > 1
        response = client.get("/api/v1/predictions?min_confidence=1.5")
        assert response.status_code == 422, "Should reject confidence > 1"
        
        # min_confidence < 0
        response = client.get("/api/v1/predictions?min_confidence=-0.1")
        assert response.status_code == 422, "Should reject confidence < 0"
        
        # view invalide
        response = client.get("/api/v1/predictions?view=invalid")
        assert response.status_code == 422, "Should reject invalid view"


# ============================================================================
# TESTS BETS - ASSERTIONS STRICTES
# ============================================================================

class TestBetsStrict:
    """Tests /api/v1/bets avec validations strictes"""
    
    def test_place_bet_success(self):
        """Test POST /bets crée un pari correctement"""
        bet_data = {
            "date": "2025-02-10",
            "match": "LAL vs GSW",
            "prediction": "LAL",
            "stake": 10.0,
            "odds": 1.85
        }
        
        response = client.post("/api/v1/bets", json=bet_data)
        
        # STRICT: Doit être 201 (created) ou 200
        assert response.status_code in [200, 201], \
            f"Expected 200/201, got {response.status_code}"
        
        data = response.json()
        
        # STRICT: Validation schema
        try:
            validated = BetResponse(**data)
        except ValidationError as e:
            pytest.fail(f"Invalid bet response schema: {e}")
        
        # STRICT: Vérifications métier
        assert validated.bet_id is not None, "Should return bet_id"
        assert validated.status == "pending", "New bet should be pending"
        assert validated.stake == bet_data["stake"], "Stake should match"
    
    def test_get_bets_list(self):
        """Test GET /bets retourne liste avec filtres"""
        response = client.get("/api/v1/bets?status=all&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        # STRICT: Structure attendue
        assert isinstance(data, list) or "bets" in data, \
            "Should return list of bets or object with bets key"
    
    def test_update_bet_result(self):
        """Test POST /bets/update met à jour résultat"""
        # D'abord créer un bet
        bet_data = {
            "date": "2025-02-10",
            "match": "LAL vs GSW",
            "prediction": "LAL",
            "stake": 10.0,
            "odds": 1.85
        }
        create_response = client.post("/api/v1/bets", json=bet_data)
        assert create_response.status_code in [200, 201]
        
        bet_id = create_response.json().get("bet_id")
        
        # Mettre à jour le résultat
        update_data = {
            "bet_id": bet_id,
            "result": "won"
        }
        
        response = client.post("/api/v1/bets/update", json=update_data)
        assert response.status_code == 200
        
        # STRICT: Vérifier que le statut a changé
        updated = response.json()
        assert updated.get("status") == "won", \
            f"Status should be 'won', got {updated.get('status')}"
    
    def test_bet_validation_errors(self):
        """Test validation des données bets"""
        # Stake négatif
        invalid_bet = {
            "date": "2025-02-10",
            "match": "LAL vs GSW",
            "prediction": "LAL",
            "stake": -10.0,  # INVALID
            "odds": 1.85
        }
        
        response = client.post("/api/v1/bets", json=invalid_bet)
        assert response.status_code == 422, "Should reject negative stake"
        
        # Odds invalides
        invalid_bet["stake"] = 10.0
        invalid_bet["odds"] = 0.5  # Trop bas
        
        response = client.post("/api/v1/bets", json=invalid_bet)
        assert response.status_code == 422, "Should reject invalid odds"


# ============================================================================
# TESTS ANALYSIS - ASSERTIONS STRICTES
# ============================================================================

class TestAnalysisStrict:
    """Tests /api/v1/analysis avec validations strictes"""
    
    def test_get_temporal_analysis(self):
        """Test GET /analysis/temporal retourne données temporelles"""
        response = client.get("/api/v1/analysis/temporal")
        
        # STRICT: Endpoint doit exister et répondre 200
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # STRICT: Validation schema
        try:
            validated = AnalysisTemporalResponse(**data)
        except ValidationError as e:
            pytest.fail(f"Invalid analysis schema: {e}")
        
        # STRICT: Contraintes métier
        assert 0 <= validated.accuracy <= 1, \
            f"Accuracy {validated.accuracy} should be in [0,1]"
        assert validated.total_predictions >= 0, \
            "Total predictions should be >= 0"


# ============================================================================
# TESTS END-TO-END FLUX COMPLET
# ============================================================================

class TestEndToEndStrict:
    """Tests bout-en-bout frontend-backend"""
    
    def test_full_prediction_flow(self):
        """Test flux complet: predictions → bet → update"""
        # 1. Récupérer prédictions
        pred_response = client.get("/api/v1/predictions?min_confidence=0.7")
        assert pred_response.status_code == 200
        
        predictions = pred_response.json().get("predictions", [])
        if len(predictions) == 0:
            pytest.skip("No high-confidence predictions available")
        
        pred = predictions[0]
        
        # 2. Placer un pari sur cette prédiction
        bet_data = {
            "date": pred.get("game_date", "2025-02-10"),
            "match": f"{pred['home_team']} vs {pred['away_team']}",
            "prediction": pred['prediction'],
            "stake": 5.0,
            "odds": 1.9
        }
        
        bet_response = client.post("/api/v1/bets", json=bet_data)
        assert bet_response.status_code in [200, 201]
        
        bet_id = bet_response.json().get("bet_id")
        assert bet_id is not None
        
        # 3. Vérifier le pari dans la liste
        list_response = client.get("/api/v1/bets?status=pending")
        assert list_response.status_code == 200
        
        # 4. Mettre à jour le résultat
        update_response = client.post("/api/v1/bets/update", json={
            "bet_id": bet_id,
            "result": "won"
        })
        assert update_response.status_code == 200
    
    def test_calendar_integration(self):
        """Test intégration calendrier + prédictions"""
        # Récupérer calendrier aujourd'hui
        calendar_response = client.get("/api/v1/calendar/today")
        assert calendar_response.status_code == 200
        
        # Récupérer prédictions pour aujourd'hui
        today = "2025-02-10"  # Ou date.today().isoformat()
        pred_response = client.get(f"/api/v1/calendar/date/{today}")
        
        # STRICT: Calendar et Predictions doivent être cohérents
        if pred_response.status_code == 200:
            cal_data = calendar_response.json()
            pred_data = pred_response.json()
            
            # Vérifier cohérence si données présentes
            if "matches" in cal_data and "matches" in pred_data:
                assert len(cal_data["matches"]) == len(pred_data["matches"]), \
                    "Calendar and predictions should have same match count"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
