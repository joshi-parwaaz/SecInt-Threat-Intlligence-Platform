import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Datasets() {
  const [datasets, setDatasets] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDatasetStatus();
    fetchLogs();
  }, []);

  const fetchDatasetStatus = async () => {
    const maxRetries = 2;
    let attempt = 0;
    while (attempt <= maxRetries) {
      try {
        const response = await axios.get(`${API_BASE}/api/datasets/status`);
        setDatasets(response.data.datasets || []);
        setLoading(false);
        return;
      } catch (err) {
        attempt += 1;
        if (attempt > maxRetries) {
          console.error('Error fetching datasets:', err);
          setLoading(false);
          return;
        }
        await new Promise((r) => setTimeout(r, 300 * attempt));
      }
    }
  };

  const fetchLogs = async () => {
    const maxRetries = 2;
    let attempt = 0;
    while (attempt <= maxRetries) {
      try {
        const response = await axios.get(`${API_BASE}/api/datasets/logs?limit=20`);
        setLogs(response.data || []);
        return;
      } catch (err) {
        attempt += 1;
        if (attempt > maxRetries) {
          console.error('Error fetching logs:', err);
          return;
        }
        await new Promise((r) => setTimeout(r, 300 * attempt));
      }
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      completed: 'bg-green-600',
      failed: 'bg-red-600',
      running: 'bg-yellow-600',
      not_found: 'bg-gray-600'
    };
    return colors[status] || 'bg-gray-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-400">Loading dataset status...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="bg-gradient-to-r from-green-900 to-teal-900 rounded-xl p-8 shadow-2xl">
        <h2 className="text-4xl font-bold text-white mb-2">📦 Dataset Management</h2>
        <p className="text-green-200 text-lg">Monitor data sources and ingestion health</p>
      </div>

      {/* Dataset Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {datasets.length === 0 ? (
          <div className="col-span-full bg-gray-800 rounded-xl p-12 border border-gray-700 text-center">
            <div className="text-6xl mb-4">📊</div>
            <div className="text-gray-400 text-lg">No dataset status available</div>
            <div className="text-gray-500 text-sm mt-2">Run the ingestion service to populate data</div>
          </div>
        ) : (
          datasets.map((dataset, idx) => {
            const datasetIcons = {
              phishing_emails: '📧',
              exploitdb: '💻',
              malware_motif: '🦠',
              open_malsec: '🔓'
            };
            const gradients = [
              'from-blue-600 to-blue-800',
              'from-red-600 to-red-800',
              'from-purple-600 to-purple-800',
              'from-green-600 to-green-800'
            ];
            return (
              <div key={idx} className={`bg-gradient-to-br ${gradients[idx % 4]} rounded-xl p-6 shadow-xl transform hover:scale-105 transition-transform`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white capitalize">{dataset.dataset.replace('_', ' ')}</h3>
                  <div className="text-4xl">{datasetIcons[dataset.dataset] || '📁'}</div>
                </div>
                <div className="space-y-3">
                  <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
                    <div className="text-xs text-white/70 mb-1">Total Threats</div>
                    <div className="text-2xl font-bold text-white">{dataset.total_threats?.toLocaleString() || 0}</div>
                  </div>
                  <div className="bg-white/10 rounded-lg p-3 backdrop-blur">
                    <div className="text-xs text-white/70 mb-1">Threat Categories</div>
                    <div className="text-2xl font-bold text-white">{dataset.unique_threat_types || 0}</div>
                  </div>
                  <div className="text-xs text-white/60 mt-2">
                    Updated: {dataset.latest_update ? new Date(dataset.latest_update).toLocaleDateString() : 'N/A'}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Ingestion Logs */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-xl font-semibold text-white mb-4">Recent Ingestion Logs</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Dataset
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Processed
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Failed
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-gray-400">
                    No ingestion logs found
                  </td>
                </tr>
              ) : (
                logs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-gray-700">
                    <td className="px-4 py-3 text-sm text-white">{log.dataset}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${getStatusColor(log.status)} text-white`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-white">{log.records_processed || 0}</td>
                    <td className="px-4 py-3 text-sm text-white">{log.records_failed || 0}</td>
                    <td className="px-4 py-3 text-sm text-gray-400">
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Datasets;
