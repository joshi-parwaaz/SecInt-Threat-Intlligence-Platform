import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Threats() {
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ type: '', dataset: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    fetchThreats();
  }, [filter]);

  // Debounced search
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      fetchThreats();
    }, 450);
    return () => clearTimeout(debounceRef.current);
  }, [searchQuery]);

  const fetchThreats = async () => {
    setLoading(true);
    setError(null);
    // If searchQuery present, use search endpoint
    let url;
    if (searchQuery && searchQuery.length >= 3) {
      url = `${API_BASE}/api/threats/search/content?q=${encodeURIComponent(searchQuery)}&limit=50`;
    } else {
      url = `${API_BASE}/api/threats/?limit=50`;
      if (filter.type) url += `&threat_type=${filter.type}`;
      if (filter.dataset) url += `&dataset=${filter.dataset}`;
    }

    // simple retry logic
    const maxRetries = 2;
    let attempt = 0;
    while (attempt <= maxRetries) {
      try {
        const response = await axios.get(url);
        setThreats(response.data || []);
        setLoading(false);
        return;
      } catch (err) {
        attempt += 1;
        if (attempt > maxRetries) {
          console.error('Error fetching threats:', err);
          setError('Failed to load threats. Check backend or network.');
          setLoading(false);
          return;
        }
        // small backoff
        await new Promise((r) => setTimeout(r, 300 * attempt));
      }
    }
  };

  const getThreatColor = (type) => {
    const colors = {
      credential_leak: 'bg-red-600',
      exploit: 'bg-orange-600',
      phishing: 'bg-yellow-600',
      malware: 'bg-purple-600',
      unknown: 'bg-gray-600'
    };
    return colors[type] || 'bg-gray-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-400">Loading threats...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-white">Threat Intelligence Feed</h2>
        <p className="text-gray-400 mt-2">Browse and filter detected threats</p>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search threats (min 3 chars)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2 mb-3"
          />
          {error && <div className="text-red-400 text-sm">{error}</div>}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Threat Type</label>
            <select
              value={filter.type}
              onChange={(e) => setFilter({ ...filter, type: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2"
            >
              <option value="">All Types</option>
              <option value="credential_leak">Credential Leak</option>
              <option value="exploit">Exploit</option>
              <option value="phishing">Phishing</option>
              <option value="malware">Malware</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Dataset</label>
            <select
              value={filter.dataset}
              onChange={(e) => setFilter({ ...filter, dataset: e.target.value })}
              className="w-full bg-gray-700 border border-gray-600 text-white rounded-md px-3 py-2"
            >
              <option value="">All Datasets</option>
              <option value="open_malsec">Open MalSec</option>
              <option value="malware_motif">Malware MOTIF</option>
              <option value="phishing_emails">Phishing Emails</option>
              <option value="exploitdb">ExploitDB</option>
            </select>
          </div>
        </div>
      </div>

      {/* Threat List */}
      <div className="space-y-4">
        {threats.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-8 border border-gray-700 text-center text-gray-400">
            No threats found. Try adjusting your filters or run the ingestion service.
          </div>
        ) : (
          threats.map((threat) => (
            <div
              key={threat._id}
              className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-gray-600 transition"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <span className={`inline-block px-3 py-1 text-xs font-semibold rounded ${getThreatColor(threat.threat_type)} text-white`}>
                      {threat.threat_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-400">{threat.dataset}</span>
                    {threat.classification_confidence && (
                      <span className="text-xs text-gray-500">
                        Confidence: {(threat.classification_confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed">{threat.content}</p>
                </div>
                <div className="text-xs text-gray-500 ml-6 whitespace-nowrap">
                  {new Date(threat.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Threats;
