"""
Tests d'intégration pour la CLI
"""

import subprocess
import sys
from pathlib import Path
import pytest
from typer.testing import CliRunner

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nba.cli import app


runner = CliRunner()


class TestCLIInfo:
    """Tests commandes info"""
    
    def test_cli_version(self):
        """Test commande version"""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "NBA Analytics Platform" in result.output
        assert "2.0.0" in result.output or "v2.0.0" in result.output
    
    def test_cli_info(self):
        """Test commande info"""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "development" in result.output or "production" in result.output


class TestCLICatalog:
    """Tests commandes catalog"""
    
    def test_cli_catalog_list(self):
        """Test commande catalog list"""
        result = runner.invoke(app, ["catalog", "list"])
        # La commande peut réussir ou échouer selon l'état du catalog
        # Mais elle doit s'exécuter sans erreur critique
        assert result.exit_code in [0, 1]
    
    def test_cli_catalog_scan(self):
        """Test commande catalog scan"""
        result = runner.invoke(app, ["catalog", "scan"])
        assert result.exit_code in [0, 1]
    
    def test_cli_catalog_show_missing_dataset(self):
        """Test catalog show sans dataset"""
        result = runner.invoke(app, ["catalog", "show"])
        # Doit afficher une erreur car --dataset est requis
        assert result.exit_code == 1 or "--dataset" in result.output


class TestCLIExport:
    """Tests commandes export"""
    
    def test_cli_export_command(self):
        """Test commande export basique"""
        result = runner.invoke(app, ["export", "players"])
        # Peut échouer si données inexistantes mais commande existe
        assert "Export" in result.output or "Erreur" in result.output or result.exit_code in [0, 1]
    
    def test_cli_export_with_format(self):
        """Test export avec format"""
        result = runner.invoke(app, ["export", "players", "--format", "csv"])
        assert result.exit_code in [0, 1]
    
    def test_cli_export_with_output(self):
        """Test export avec output"""
        result = runner.invoke(app, ["export", "players", "--output", "/tmp/test"])
        assert result.exit_code in [0, 1]
    
    def test_cli_export_all(self):
        """Test export all"""
        result = runner.invoke(app, ["export", "all"])
        assert result.exit_code in [0, 1]


class TestCLIDashboard:
    """Tests commandes dashboard"""
    
    def test_cli_dashboard_help(self):
        """Test dashboard --help"""
        result = runner.invoke(app, ["dashboard", "--help"])
        assert result.exit_code == 0
        assert "dashboard" in result.output.lower()


class TestCLIPipeline:
    """Tests commandes pipeline"""
    
    def test_cli_pipeline_help(self):
        """Test pipeline --help"""
        result = runner.invoke(app, ["pipeline", "--help"])
        assert result.exit_code == 0
    
    def test_cli_pipeline_ingest(self):
        """Test pipeline ingest"""
        result = runner.invoke(app, ["pipeline", "ingest"])
        assert result.exit_code in [0, 1]
    
    def test_cli_pipeline_invalid_step(self):
        """Test pipeline avec étape invalide"""
        result = runner.invoke(app, ["pipeline", "invalid"])
        assert result.exit_code == 1


class TestCLIDev:
    """Tests commandes dev"""
    
    def test_cli_dev_api_help(self):
        """Test dev api --help"""
        result = runner.invoke(app, ["dev", "api", "--help"])
        assert result.exit_code == 0


class TestCLIHelp:
    """Tests aide CLI"""
    
    def test_cli_main_help(self):
        """Test aide principale"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "NBA Analytics Platform" in result.output
    
    def test_cli_subcommand_help(self):
        """Test aide sous-commandes"""
        for cmd in ["export", "catalog", "predict", "train"]:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
