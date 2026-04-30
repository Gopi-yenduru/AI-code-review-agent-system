/**
 * App root — React Router setup with layout wrapper.
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ReviewDetail from './pages/ReviewDetail';
import DeveloperStats from './pages/DeveloperStats';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ background: 'var(--gradient-dark)' }}>
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/reviews/:id" element={<ReviewDetail />} />
            <Route path="/developer/:username" element={<DeveloperStats />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
