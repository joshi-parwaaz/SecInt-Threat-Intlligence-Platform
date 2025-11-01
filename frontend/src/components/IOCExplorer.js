import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function IOCExplorer() {
  const [iocs, setIocs] = useState([]);
  const [stats, setStats] = useState(null);
  const [topThreats, setTopThreats] = useState([]);
  const [blocklist, setBlocklist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');

  useEffect(() => {
    fetchStats();
    fetchIOCs();
    fetchTopThreats();
    fetchBlocklist();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchStats();
      fetchIOCs();
      fetchTopThreats();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [selectedType, selectedSeverity]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/iocs/stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchTopThreats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/top-threats?limit=10');
      const data = await response.json();
      if (data.success) {
        setTopThreats(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch top threats:', err);
    }
  };

  const fetchBlocklist = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/blocklist');
      const data = await response.json();
      if (data.success) {
        setBlocklist(data);  // Store the full response object
      }
    } catch (err) {
      console.error('Failed to fetch blocklist:', err);
    }
  };

  const fetchIOCs = async () => {
    setLoading(true);
    try {
      let url = 'http://localhost:8000/api/iocs?limit=100';
      if (selectedType !== 'all') url += `&ioc_type=${selectedType}`;
      if (selectedSeverity !== 'all') url += `&severity=${selectedSeverity}`;
      
      const response = await fetch(url);
      const data = await response.json();
      // API returns {iocs: [...], total: number}
      setIocs(data.iocs || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch IOCs');
      console.error(err);
      setIocs([]);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const severityUpper = severity?.toUpperCase();
    if (severityUpper === 'CRITICAL') return 'text-red-400 bg-red-900/30 border-red-700';
    if (severityUpper === 'HIGH') return 'text-orange-400 bg-orange-900/30 border-orange-700';
    if (severityUpper === 'MEDIUM') return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
    if (severityUpper === 'LOW') return 'text-green-400 bg-green-900/30 border-green-700';
    return 'text-gray-400 bg-gray-900/30 border-gray-700';
  };

  const getSeverityLabel = (severity) => {
    return severity || 'UNKNOWN';
  };

  const downloadReport = async (format) => {
    try {
      const response = await fetch(`http://localhost:8000/api/reports/download/${format}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `secint_report_${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(`Failed to download ${format} report:`, err);
      alert(`Failed to download ${format} report`);
    }
  };

  const downloadBlocklist = () => {
    if (!blocklist || !blocklist.data) return;
    
    const data = blocklist.data;
    
    // Create text content with all IOCs
    let content = '# SecInt v2 - Threat Blocklist\n';
    content += `# Generated: ${new Date().toISOString()}\n`;
    content += `# Critical and High Severity IOCs\n\n`;
    
    // Add IP addresses
    if (data.ipv4_addresses && data.ipv4_addresses.length > 0) {
      content += '## IP Addresses\n';
      data.ipv4_addresses.forEach(ip => {
        content += `${ip}\n`;
      });
      content += '\n';
    }
    
    // Add domains
    if (data.domains && data.domains.length > 0) {
      content += '## Domains\n';
      data.domains.forEach(domain => {
        content += `${domain}\n`;
      });
      content += '\n';
    }
    
    // Add URLs
    if (data.urls && data.urls.length > 0) {
      content += '## URLs\n';
      data.urls.forEach(url => {
        content += `${url}\n`;
      });
      content += '\n';
    }
    
    // Add file hashes
    if (data.file_hashes) {
      if (data.file_hashes.md5 && data.file_hashes.md5.length > 0) {
        content += '## MD5 Hashes\n';
        data.file_hashes.md5.forEach(hash => {
          content += `${hash}\n`;
        });
        content += '\n';
      }
      
      if (data.file_hashes.sha1 && data.file_hashes.sha1.length > 0) {
        content += '## SHA1 Hashes\n';
        data.file_hashes.sha1.forEach(hash => {
          content += `${hash}\n`;
        });
        content += '\n';
      }
      
      if (data.file_hashes.sha256 && data.file_hashes.sha256.length > 0) {
        content += '## SHA256 Hashes\n';
        data.file_hashes.sha256.forEach(hash => {
          content += `${hash}\n`;
        });
        content += '\n';
      }
    }
    
    // Download the file
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `secint_blocklist_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  // Prepare chart data
  const severityChartData = stats ? [
    { name: 'CRITICAL', value: stats.by_severity?.CRITICAL || 0, color: '#ef4444' },
    { name: 'HIGH', value: stats.by_severity?.HIGH || 0, color: '#f97316' },
    { name: 'MEDIUM', value: stats.by_severity?.MEDIUM || 0, color: '#f59e0b' },
    { name: 'LOW', value: stats.by_severity?.LOW || 0, color: '#10b981' }
  ] : [];

  const typeChartData = stats && stats.by_type ? Object.entries(stats.by_type).map(([name, value]) => ({
    name: name.toUpperCase(),
    value
  })) : [];

  return (
    <div className="space-y-6">
      {/* Header with Download Buttons */}
      <div className="bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-gray-700 rounded-lg p-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-white">🔍 IOC Explorer</h2>
            <p className="text-gray-400 mt-2">Real-time threat intelligence from multiple sources</p>
            {stats && (
              <p className="text-sm text-gray-500 mt-1">
                Last updated: {new Date().toLocaleTimeString()} • Auto-refresh: 30s
              </p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => downloadReport('csv')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition shadow-lg hover:shadow-xl transform hover:scale-105"
              title="Export all IOCs to CSV format"
            >
              📊 CSV
            </button>
            <button
              onClick={() => downloadReport('json')}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition shadow-lg hover:shadow-xl transform hover:scale-105"
              title="Export all IOCs to JSON format"
            >
              📋 JSON
            </button>
            <button
              onClick={() => downloadReport('html')}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition shadow-lg hover:shadow-xl transform hover:scale-105"
              title="View formatted HTML report"
            >
              📄 HTML
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
            <div className="text-gray-400 text-sm">Total IOCs</div>
            <div className="text-3xl font-bold text-white mt-2">{stats.total_iocs?.toLocaleString() || 0}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg border border-red-700">
            <div className="text-gray-400 text-sm">Critical Threats</div>
            <div className="text-3xl font-bold text-red-400 mt-2">{stats.by_severity?.CRITICAL || 0}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg border border-orange-700">
            <div className="text-gray-400 text-sm">High Severity</div>
            <div className="text-3xl font-bold text-orange-400 mt-2">{stats.by_severity?.HIGH || 0}</div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg border border-green-700">
            <div className="text-gray-400 text-sm">Recent (24h)</div>
            <div className="text-3xl font-bold text-green-400 mt-2">{stats.recent_count || 0}</div>
          </div>
        </div>
      )}

      {/* Actionable Insights Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 10 IPs to Block */}
        <div className="bg-gray-800 p-6 rounded-lg border border-red-700/50 shadow-lg">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-xl font-bold text-white">🚨 Top 10 Threats to Block</h3>
              <p className="text-xs text-gray-400 mt-1">High priority IOCs for immediate firewall blocking</p>
            </div>
            <button
              onClick={downloadBlocklist}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition shadow-lg hover:shadow-xl transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!blocklist || !blocklist.data || (
                (!blocklist.data.ipv4_addresses || blocklist.data.ipv4_addresses.length === 0) && 
                (!blocklist.data.domains || blocklist.data.domains.length === 0) &&
                (!blocklist.data.urls || blocklist.data.urls.length === 0) &&
                (!blocklist.data.file_hashes || 
                  ((!blocklist.data.file_hashes.md5 || blocklist.data.file_hashes.md5.length === 0) &&
                   (!blocklist.data.file_hashes.sha1 || blocklist.data.file_hashes.sha1.length === 0) &&
                   (!blocklist.data.file_hashes.sha256 || blocklist.data.file_hashes.sha256.length === 0)))
              )}
              title="Download firewall-ready blocklist"
            >
              ⬇️ Download Blocklist
            </button>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {topThreats.length > 0 ? (
              topThreats.map((threat, idx) => (
                <div key={idx} className="bg-gray-900 p-3 rounded border border-gray-700 hover:border-red-600 transition">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-mono text-sm text-white">{threat.ioc_value}</div>
                      <div className="text-xs text-gray-400 mt-1">
                        {threat.ioc_type} • {threat.malware_family || 'Unknown'} • Score: {threat.severity_score}
                      </div>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded ${
                      threat.severity === 'CRITICAL' ? 'bg-red-900 text-red-300' :
                      threat.severity === 'HIGH' ? 'bg-orange-900 text-orange-300' :
                      'bg-yellow-900 text-yellow-300'
                    }`}>
                      {threat.severity}
                    </span>
                  </div>
                  {threat.vt_detections && (
                    <div className="text-xs text-gray-500 mt-2">
                      🛡️ VT: {threat.vt_detections}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">No threats data available</div>
            )}
          </div>
        </div>

        {/* Severity Distribution Chart */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">📊 Severity Distribution</h3>
          {severityChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center text-gray-500 py-8">No data available</div>
          )}
        </div>
      </div>

      {/* IOC Type Distribution Chart */}
      {typeChartData.length > 0 && (
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-xl font-bold text-white mb-4">📈 IOC Type Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={typeChartData}>
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }} />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Filters */}
      <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm font-semibold">🔍 Filters:</span>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-gray-400 text-sm">IOC Type:</label>
            <select 
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 hover:border-blue-500 transition focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">🌐 All Types</option>
              <option value="ipv4">📍 IPv4 Address</option>
              <option value="domain">🌍 Domain</option>
              <option value="url">🔗 URL</option>
              <option value="sha256">📄 SHA256</option>
              <option value="md5">📄 MD5</option>
              <option value="cve">🐛 CVE</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-gray-400 text-sm">Min Severity:</label>
            <select 
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 hover:border-red-500 transition focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="all">📊 All Severities</option>
              <option value="CRITICAL">🔴 Critical</option>
              <option value="HIGH">🟠 High</option>
              <option value="MEDIUM">🟡 Medium</option>
              <option value="LOW">🟢 Low</option>
            </select>
          </div>
          <button
            onClick={() => {
              setSelectedType('all');
              setSelectedSeverity('all');
            }}
            className="ml-auto px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition"
            title="Reset all filters"
          >
            🔄 Reset Filters
          </button>
        </div>
      </div>

      {/* IOC List */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Severity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Source</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">First Seen</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-400">
                    Loading IOCs...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-red-400">
                    {error}
                  </td>
                </tr>
              ) : iocs.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-6 py-8 text-center text-gray-400">
                    No IOCs found. Start the ingestion service to populate data.
                  </td>
                </tr>
              ) : (
                iocs.map((ioc, idx) => (
                  <tr key={idx} className="hover:bg-gray-700/50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded-full bg-blue-900/30 text-blue-400 border border-blue-700">
                        {ioc.ioc_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-sm text-white max-w-md truncate" title={ioc.ioc_value}>
                      {ioc.ioc_value}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full border ${getSeverityColor(ioc.severity)}`}>
                        {getSeverityLabel(ioc.severity)} ({ioc.severity_score || 0})
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400">
                      {ioc.source || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400">
                      {ioc.first_seen ? new Date(ioc.first_seen).toLocaleString() : 'N/A'}
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

export default IOCExplorer;
