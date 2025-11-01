import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import LandingPage from './components/LandingPage';

function App() {
  return (
    <Router>
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<LandingPageWrapper />} />
        
        {/* Dashboard */}
        <Route path="/dashboard" element={<DashboardLayout />} />
      </Routes>
    </Router>
  );
}

function LandingPageWrapper() {
  const navigate = useNavigate();
  
  return <LandingPage onEnter={() => navigate('/dashboard')} />;
}

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-black">
      {/* Navigation */}
      <nav className="bg-gray-900/80 backdrop-blur-sm border-b border-yellow-500/20 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold text-white hover:text-yellow-400 transition-colors flex items-center gap-2">
                <span className="text-2xl">🛡️</span> SecInt
              </Link>
            </div>
            <div className="flex space-x-4">
              <Link
                to="/dashboard"
                className="text-yellow-500 bg-yellow-500/10 px-4 py-2 rounded-lg text-sm font-medium border border-yellow-500/30"
              >
                Dashboard
              </Link>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-300 hover:bg-gray-800 hover:text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                API Docs
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        <Dashboard />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-yellow-500/20 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-400 text-sm">
            <p className="font-semibold text-white mb-2">SecInt - Real-Time Threat Intelligence Platform</p>
            <p className="text-xs">Multi-Source Intelligence • Real-time Enrichment • Automated Severity Scoring</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
