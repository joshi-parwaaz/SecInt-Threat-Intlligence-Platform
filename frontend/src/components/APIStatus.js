import React, { useState, useEffect } from 'react';

function APIStatus() {
  const [apiHealth, setApiHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    fetchAPIHealth();
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchAPIHealth, 120000);
    return () => clearInterval(interval);
  }, []);

  const fetchAPIHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health/apis');
      const data = await response.json();
      setApiHealth(data);
      setLastUpdate(new Date());
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch API health:', err);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ok':
        return 'text-green-400 bg-green-900/30 border-green-700';
      case 'invalid':
      case 'error':
      case 'timeout':
        return 'text-red-400 bg-red-900/30 border-red-700';
      case 'rate_limited':
        return 'text-orange-400 bg-orange-900/30 border-orange-700';
      case 'not_configured':
        return 'text-gray-400 bg-gray-900/30 border-gray-700';
      default:
        return 'text-gray-400 bg-gray-900/30 border-gray-700';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ok':
        return '✅';
      case 'invalid':
      case 'error':
        return '❌';
      case 'timeout':
        return '⏱️';
      case 'rate_limited':
        return '⚠️';
      case 'not_configured':
        return '⚙️';
      default:
        return '❓';
    }
  };

  const getOverallStatusColor = (overallStatus) => {
    switch (overallStatus) {
      case 'healthy':
        return 'bg-green-600';
      case 'degraded':
        return 'bg-orange-600';
      case 'unhealthy':
        return 'bg-red-600';
      default:
        return 'bg-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
        <div className="text-gray-400 text-sm">Loading API status...</div>
      </div>
    );
  }

  if (!apiHealth) {
    return (
      <div className="bg-gray-800 p-4 rounded-lg border border-red-700">
        <div className="text-red-400 text-sm">Failed to load API status</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-xl font-bold text-white">🔌 External API Status</h3>
          <p className="text-xs text-gray-400 mt-1">Monitor threat intelligence API health and quota</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-3 py-1 rounded-full text-xs font-bold text-white shadow-lg ${getOverallStatusColor(apiHealth.overall_status)}`}>
            {apiHealth.overall_status?.toUpperCase()}
          </span>
          <button
            onClick={fetchAPIHealth}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg transition shadow-lg hover:shadow-xl transform hover:scale-105"
            title="Refresh API status now"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(apiHealth.apis || {}).map(([apiName, status]) => (
          <div
            key={apiName}
            className={`p-4 rounded-lg border ${getStatusColor(status.status)}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-sm uppercase">{apiName}</span>
              <span className="text-xl">{getStatusIcon(status.status)}</span>
            </div>
            <div className="text-xs mb-2">{status.message}</div>
            {status.quota && (
              <div className="text-xs font-mono opacity-75">{status.quota}</div>
            )}
            {status.user && (
              <div className="text-xs opacity-75">User: {status.user}</div>
            )}
          </div>
        ))}
      </div>

      {lastUpdate && (
        <div className="mt-4 text-xs text-gray-500 text-right">
          Last checked: {lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

export default APIStatus;
