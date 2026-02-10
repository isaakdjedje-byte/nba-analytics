import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Betting } from './pages/Betting';
import { Predictions } from './pages/Predictions';
import { MLPipeline } from './pages/MLPipeline';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/betting" element={<Betting />} />
        <Route path="/ml-pipeline" element={<MLPipeline />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
