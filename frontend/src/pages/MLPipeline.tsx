import { useState } from 'react';
import { Layout } from '../components/Layout';
import { StatsCard } from '../components/StatsCard';
import { Brain, Code, BookOpen, ChevronRight, ChevronLeft, Play, Pause } from 'lucide-react';

interface PipelineStep {
  id: string;
  icon: string;
  name: string;
  description: string;
  demo: string;
  technical: string;
  educational: string;
  codeSnippet: string;
  metrics: Record<string, string | number>;
}

const pipelineSteps: PipelineStep[] = [
  {
    id: 'ingestion',
    icon: '📥',
    name: 'Data Ingestion',
    description: 'Collecte des données NBA',
    demo: 'Récupération automatique des stats de 5,103 joueurs et 30 équipes toutes les 2 heures',
    technical: 'Python scripts utilisant NBA API et web scraping Basketball-Reference avec rate limiting',
    educational: 'On collecte les données de tous les joueurs et équipes pour avoir une vue complète',
    codeSnippet: `def fetch_nba_data():
    players = nba_api.PlayerIndex().get_data()
    teams = nba_api.TeamStats().get_data()
    return process_data(players, teams)`,
    metrics: {
      'Sources': 2,
      'Fréquence': '2h',
      'Joueurs': 5103,
      'Équipes': 30
    }
  },
  {
    id: 'features',
    icon: '⚙️',
    name: 'Feature Engineering',
    description: 'Création de 94 features',
    demo: 'Transformation des données brutes en indicateurs avancés comme PER et TS%',
    technical: '94 features harmonisées avec pandas: PER, TS%, USG%, ORtg, DRtg, etc.',
    educational: 'Le PER (Player Efficiency Rating) est le meilleur prédicteur de performance',
    codeSnippet: `def engineer_features(df):
    df['PER'] = (df['pts'] + df['reb'] + df['ast']) / df['min'] * 36
    df['TS%'] = df['pts'] / (2 * df['fga'] + 0.44 * df['fta'])
    return df`,
    metrics: {
      'Features': 94,
      'Top Feature': 'PER',
      'Catégories': 3,
      'Harmonisation': '100%'
    }
  },
  {
    id: 'training',
    icon: '🧮',
    name: 'Model Training',
    description: 'Entraînement XGBoost',
    demo: 'Le modèle apprend sur 2,624 matchs historiques pour reconnaître les patterns',
    technical: 'XGBoost avec GridSearchCV: n_estimators=200, max_depth=6, learning_rate=0.1',
    educational: 'Le modèle analyse les patterns historiques pour prédire les résultats futurs',
    codeSnippet: `model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1
)
model.fit(X_train, y_train)`,
    metrics: {
      'Algorithm': 'XGBoost',
      'Samples': 2624,
      'Estimators': 200,
      'Max Depth': 6
    }
  },
  {
    id: 'calibration',
    icon: '📊',
    name: 'Calibration',
    description: 'Ajustement des probabilités',
    demo: 'Correction pour que 80% de confiance = 80% de chances de gagner réellement',
    technical: 'Isotonic Regression pour calibrer les probabilités et améliorer la fiabilité',
    educational: 'On corrige le modèle pour que ses prédictions soient statistiquement fiables',
    codeSnippet: `calibrator = IsotonicRegression()
calibrator.fit(model.predict_proba(X_val), y_val)
proba_calibrated = calibrator.transform(proba_raw)`,
    metrics: {
      'Method': 'Isotonic',
      'Improvement': '+5%',
      'Reliability': '85%'
    }
  }
];

const globalMetrics = {
  accuracy: 83.03,
  precision: 81,
  recall: 79,
  f1_score: 80,
  roi: 12.5
};

export function MLPipeline() {
  const [activeStep, setActiveStep] = useState(0);
  const [mode, setMode] = useState<'demo' | 'technical'>('demo');
  const [isPlaying, setIsPlaying] = useState(false);

  const currentStep = pipelineSteps[activeStep];

  const handleNext = () => {
    setActiveStep((prev) => (prev + 1) % pipelineSteps.length);
  };

  const handlePrev = () => {
    setActiveStep((prev) => (prev - 1 + pipelineSteps.length) % pipelineSteps.length);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying) {
      const interval = setInterval(() => {
        setActiveStep((prev) => {
          if (prev >= pipelineSteps.length - 1) {
            clearInterval(interval);
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 2000);
    }
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Brain className="text-purple-500" size={32} />
            <div>
              <h2 className="text-3xl font-bold">Pipeline ML</h2>
              <p className="text-gray-400">Architecture & Processus</p>
            </div>
          </div>
          
          {/* Mode Toggle */}
          <div className="flex bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setMode('demo')}
              className={`flex items-center gap-2 px-4 py-2 rounded transition ${
                mode === 'demo' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <BookOpen size={18} />
              Simple
            </button>
            <button
              onClick={() => setMode('technical')}
              className={`flex items-center gap-2 px-4 py-2 rounded transition ${
                mode === 'technical' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Code size={18} />
              Technique
            </button>
          </div>
        </div>

        {/* Global Metrics */}
        <div className="grid grid-cols-5 gap-4">
          <StatsCard title="Accuracy" value={`${globalMetrics.accuracy}%`} />
          <StatsCard title="Precision" value={`${globalMetrics.precision}%`} />
          <StatsCard title="Recall" value={`${globalMetrics.recall}%`} />
          <StatsCard title="F1-Score" value={`${globalMetrics.f1_score}%`} />
          <StatsCard title="ROI Paper" value={`+${globalMetrics.roi}%`} trend={12.5} />
        </div>

        {/* Pipeline Diagram */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold">Processus</h3>
            <button
              onClick={togglePlay}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded transition"
            >
              {isPlaying ? <Pause size={18} /> : <Play size={18} />}
              {isPlaying ? 'Pause' : 'Démarrer'}
            </button>
          </div>

          {/* Steps */}
          <div className="flex items-center justify-between gap-2">
            {pipelineSteps.map((step, idx) => (
              <button
                key={step.id}
                onClick={() => setActiveStep(idx)}
                className={`flex-1 p-4 rounded-lg transition-all ${
                  idx === activeStep
                    ? 'bg-blue-600 scale-105 shadow-lg shadow-blue-500/30'
                    : idx < activeStep
                    ? 'bg-green-600/50'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <div className="text-3xl mb-2">{step.icon}</div>
                <div className="font-semibold text-sm">{step.name}</div>
                <div className="text-xs opacity-70 mt-1">{step.description}</div>
              </button>
            ))}
          </div>

          {/* Arrows */}
          <div className="flex justify-center gap-8 my-4">
            {pipelineSteps.slice(0, -1).map((_, idx) => (
              <div
                key={idx}
                className={`text-2xl transition-colors ${
                  idx < activeStep ? 'text-green-500' : 'text-gray-600'
                }`}
              >
                →
              </div>
            ))}
          </div>
        </div>

        {/* Step Details */}
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-4xl">{currentStep.icon}</span>
              <div>
                <h3 className="text-2xl font-bold">{currentStep.name}</h3>
                <p className="text-gray-400">{currentStep.description}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handlePrev}
                className="p-2 bg-gray-700 hover:bg-gray-600 rounded transition"
              >
                <ChevronLeft size={24} />
              </button>
              <button
                onClick={handleNext}
                className="p-2 bg-gray-700 hover:bg-gray-600 rounded transition"
              >
                <ChevronRight size={24} />
              </button>
            </div>
          </div>

          {/* Content based on mode */}
          <div className="space-y-4">
            <div className="bg-gray-700/50 rounded-lg p-4">
              <h4 className="font-semibold mb-2 text-blue-400">
                {mode === 'demo' ? '💡 Explication' : '💻 Code'}
              </h4>
              <p className="text-gray-300">
                {mode === 'demo' ? currentStep.demo : currentStep.technical}
              </p>
            </div>

            {mode === 'technical' && (
              <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm">
                <pre className="text-green-400 overflow-x-auto">
                  {currentStep.codeSnippet}
                </pre>
              </div>
            )}

            {mode === 'demo' && (
              <div className="bg-gray-700/50 rounded-lg p-4">
                <h4 className="font-semibold mb-2 text-yellow-400">📚 Le saviez-vous ?</h4>
                <p className="text-gray-300">{currentStep.educational}</p>
              </div>
            )}

            {/* Metrics */}
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(currentStep.metrics).map(([key, value]) => (
                <div key={key} className="bg-gray-700/30 rounded p-3 text-center">
                  <div className="text-2xl font-bold text-blue-400">{value}</div>
                  <div className="text-xs text-gray-400 uppercase">{key}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
