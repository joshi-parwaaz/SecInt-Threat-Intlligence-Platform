import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Shield,
  Download,
  FileDown,
  Filter,
  X,
  TrendingUp,
  Database,
  Eye,
  Zap,
  Globe,
  Lock
} from 'lucide-react';
import { PieChart, Pie, BarChart, Bar, Cell, ResponsiveContainer, Tooltip, Legend, XAxis, YAxis } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/Card';

const Dashboard = () => {
  // State
  const [stats, setStats] = useState(null);
  const [iocs, setIocs] = useState([]);
  const [topThreats, setTopThreats] = useState([]);
  const [blocklist, setBlocklist] = useState(null);
  const [apiHealth, setApiHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');

  // Fetch all data
  const fetchData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchStats(),
        fetchIOCs(),
        fetchTopThreats(),
        fetchBlocklist(),
        fetchAPIHealth()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Auto-refresh for API health every 2 minutes
  useEffect(() => {
    const apiInterval = setInterval(fetchAPIHealth, 120000);
    return () => clearInterval(apiInterval);
  }, []);

  // Fetch Stats
  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/iocs/stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  // Fetch IOCs with filters
  const fetchIOCs = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedType !== 'all') params.append('ioc_type', selectedType);
      if (selectedSeverity !== 'all') params.append('severity', selectedSeverity);
      params.append('limit', '100');

      const response = await fetch(`http://localhost:8000/api/iocs/?${params}`);
      const data = await response.json();
      setIocs(data.iocs || []);
    } catch (err) {
      console.error('Error fetching IOCs:', err);
    }
  };

  // Re-fetch when filters change
  useEffect(() => {
    if (!loading) fetchIOCs();
  }, [selectedType, selectedSeverity]);

  // Fetch Top Threats
  const fetchTopThreats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/top-threats?limit=10');
      const data = await response.json();
      setTopThreats(data.data || []);
    } catch (err) {
      console.error('Error fetching top threats:', err);
    }
  };

  // Fetch Blocklist
  const fetchBlocklist = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/blocklist');
      const data = await response.json();
      setBlocklist(data);
    } catch (err) {
      console.error('Error fetching blocklist:', err);
    }
  };

  // Fetch API Health
  const fetchAPIHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health/apis');
      const data = await response.json();
      setApiHealth(data);
    } catch (err) {
      console.error('Error fetching API health:', err);
    }
  };

  // Download Report
  const downloadReport = async (format) => {
    try {
      let url = '';
      if (format === 'csv') {
        url = 'http://localhost:8000/api/reports/download/csv';
      } else if (format === 'json') {
        url = 'http://localhost:8000/api/reports/download/json';
      } else if (format === 'html') {
        url = 'http://localhost:8000/api/reports/download/html';
      }

      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `threat_report.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (err) {
      console.error(`Error downloading ${format} report:`, err);
    }
  };

  // Download Blocklist
  const downloadBlocklist = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/reports/blocklist');
      const result = await response.json();
      const data = result.data;
      
      let content = '# Threat Intelligence Blocklist\n';
      content += `# Generated: ${new Date().toISOString()}\n`;
      content += `# Total IPs: ${result.metadata.totals.ips}\n`;
      content += `# Total Domains: ${result.metadata.totals.domains}\n`;
      content += `# Total URLs: ${result.metadata.totals.urls}\n`;
      content += `# Total Hashes: ${result.metadata.totals.hashes}\n\n`;
      
      content += '# IP Addresses\n';
      data.ipv4_addresses?.forEach(ip => content += `${ip}\n`);
      
      content += '\n# Domains\n';
      data.domains?.forEach(domain => content += `${domain}\n`);
      
      content += '\n# URLs\n';
      data.urls?.forEach(url => content += `${url}\n`);
      
      content += '\n# File Hashes (SHA256)\n';
      data.file_hashes?.sha256?.forEach(hash => content += `${hash}\n`);
      
      content += '\n# File Hashes (MD5)\n';
      data.file_hashes?.md5?.forEach(hash => content += `${hash}\n`);
      
      const blob = new Blob([content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'blocklist.txt';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error downloading blocklist:', err);
    }
  };

  // Helper functions
  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'bg-red-500',
      HIGH: 'bg-orange-500',
      MEDIUM: 'bg-yellow-500',
      LOW: 'bg-green-500'
    };
    return colors[severity] || 'bg-gray-500';
  };

  const getStatusColor = (status) => {
    const colors = {
      ok: 'text-green-500',
      invalid: 'text-red-500',
      error: 'text-red-500',
      timeout: 'text-orange-500',
      rate_limited: 'text-yellow-500',
      not_configured: 'text-gray-500'
    };
    return colors[status] || 'text-gray-500';
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'ok': return <CheckCircle className="w-5 h-5" />;
      case 'invalid':
      case 'error': return <XCircle className="w-5 h-5" />;
      case 'timeout': return <Clock className="w-5 h-5" />;
      case 'rate_limited': return <AlertTriangle className="w-5 h-5" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  const getOverallStatusColor = (status) => {
    const colors = {
      healthy: 'text-green-500',
      degraded: 'text-yellow-500',
      unhealthy: 'text-red-500'
    };
    return colors[status] || 'text-gray-500';
  };

  // Chart data
  const severityData = stats ? [
    { name: 'Critical', value: stats.by_severity?.CRITICAL || 0, color: '#ef4444' },
    { name: 'High', value: stats.by_severity?.HIGH || 0, color: '#f97316' },
    { name: 'Medium', value: stats.by_severity?.MEDIUM || 0, color: '#eab308' },
    { name: 'Low', value: stats.by_severity?.LOW || 0, color: '#22c55e' }
  ] : [];

  const typeData = stats?.by_type ? Object.entries(stats.by_type).map(([name, value]) => ({
    name: name.toUpperCase(),
    value,
    color: '#eab308'
  })) : [];

  // Calculate percentage for severity
  const totalSeverity = severityData.reduce((sum, item) => sum + item.value, 0);
  const severityWithPercent = severityData.map(item => ({
    ...item,
    percentage: totalSeverity > 0 ? ((item.value / totalSeverity) * 100).toFixed(1) : 0
  }));

  // Get icon for IOC type
  const getTypeIcon = (type) => {
    switch(type?.toLowerCase()) {
      case 'ipv4': return <Globe className="w-4 h-4" />;
      case 'domain': return <Globe className="w-4 h-4" />;
      case 'url': return <Globe className="w-4 h-4" />;
      case 'sha256': return <Lock className="w-4 h-4" />;
      case 'md5': return <Lock className="w-4 h-4" />;
      case 'cve': return <Shield className="w-4 h-4" />;
      default: return <Database className="w-4 h-4" />;
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-yellow-500 animate-spin mx-auto mb-4" />
          <p className="text-yellow-500 text-lg">Loading threat intelligence...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-8">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-yellow-500 mb-2">Threat Intelligence Dashboard</h1>
            <p className="text-gray-400">Real-time monitoring and analysis</p>
          </div>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </motion.div>

      {/* Download Buttons */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => downloadReport('csv')}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all"
              >
                <Download className="w-4 h-4" />
                CSV Report
              </button>
              <button
                onClick={() => downloadReport('json')}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all"
              >
                <Download className="w-4 h-4" />
                JSON Report
              </button>
              <button
                onClick={() => downloadReport('html')}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all"
              >
                <Download className="w-4 h-4" />
                HTML Report
              </button>
              <button
                onClick={downloadBlocklist}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all"
              >
                <FileDown className="w-4 h-4" />
                Download Blocklist
              </button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-yellow-500" />
              Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4 items-center">
              <div>
                <label className="block text-sm text-gray-400 mb-2">IOC Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="px-4 py-2 bg-gray-900 border border-yellow-500/30 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                >
                  <option value="all">All Types</option>
                  <option value="ipv4">IPv4</option>
                  <option value="domain">Domain</option>
                  <option value="url">URL</option>
                  <option value="sha256">SHA256</option>
                  <option value="md5">MD5</option>
                  <option value="cve">CVE</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Severity</label>
                <select
                  value={selectedSeverity}
                  onChange={(e) => setSelectedSeverity(e.target.value)}
                  className="px-4 py-2 bg-gray-900 border border-yellow-500/30 rounded-lg text-white focus:outline-none focus:border-yellow-500"
                >
                  <option value="all">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>
              {(selectedType !== 'all' || selectedSeverity !== 'all') && (
                <button
                  onClick={() => {
                    setSelectedType('all');
                    setSelectedSeverity('all');
                  }}
                  className="mt-6 flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all"
                >
                  <X className="w-4 h-4" />
                  Reset Filters
                </button>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Stats Grid */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
      >
        <motion.div whileHover={{ scale: 1.05 }} transition={{ type: "spring", stiffness: 300 }}>
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-full -mr-16 -mt-16" />
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Total IOCs</CardTitle>
                <Database className="w-8 h-8 text-yellow-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-yellow-500 mb-2">{stats?.total?.toLocaleString() || 0}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <TrendingUp className="w-3 h-3 text-green-500" />
                <span>Across all sources</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div whileHover={{ scale: 1.05 }} transition={{ type: "spring", stiffness: 300 }}>
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full -mr-16 -mt-16" />
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Critical Threats</CardTitle>
                <AlertTriangle className="w-8 h-8 text-red-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-red-500 mb-2">{stats?.by_severity?.CRITICAL?.toLocaleString() || 0}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Zap className="w-3 h-3 text-red-500" />
                <span>Require immediate action</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div whileHover={{ scale: 1.05 }} transition={{ type: "spring", stiffness: 300 }}>
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full -mr-16 -mt-16" />
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">High Priority</CardTitle>
                <Shield className="w-8 h-8 text-orange-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-orange-500 mb-2">{stats?.by_severity?.HIGH?.toLocaleString() || 0}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Eye className="w-3 h-3 text-orange-500" />
                <span>High severity indicators</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div whileHover={{ scale: 1.05 }} transition={{ type: "spring", stiffness: 300 }}>
          <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-full -mr-16 -mt-16" />
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Recent (24h)</CardTitle>
                <Clock className="w-8 h-8 text-yellow-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-yellow-500 mb-2">{stats?.recent_24h?.toLocaleString() || 0}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Activity className="w-3 h-3 text-yellow-500" />
                <span>New IOCs today</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* API Health Status */}
      {apiHealth && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-yellow-500" />
                API Health Status
                <span className={`text-sm ml-auto ${getOverallStatusColor(apiHealth.overall_status)}`}>
                  {apiHealth.overall_status?.toUpperCase()}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(apiHealth.apis || {}).map(([name, data]) => (
                  <div key={name} className="p-4 bg-gray-900/50 rounded-lg border border-yellow-500/20">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-sm">{name}</h4>
                      <span className={getStatusColor(data.status)}>
                        {getStatusIcon(data.status)}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">
                      Status: <span className={getStatusColor(data.status)}>{data.status}</span>
                    </p>
                    {data.quota && (
                      <p className="text-xs text-gray-400 mt-1">
                        Quota: {data.quota.remaining}/{data.quota.limit}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Charts */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              Severity Distribution
            </CardTitle>
            <CardDescription>IOCs categorized by threat level</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percentage }) => `${name} ${percentage}%`}
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              
              <div className="space-y-3 min-w-[200px]">
                {severityWithPercent.map((item, idx) => (
                  <motion.div 
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + idx * 0.1 }}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full`} style={{ backgroundColor: item.color }} />
                      <span className="text-sm text-gray-300">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">{item.value.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">{item.percentage}%</div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              IOC Types Distribution
            </CardTitle>
            <CardDescription>Breakdown by indicator type</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={typeData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <XAxis dataKey="name" stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1f2937', 
                    border: '1px solid #eab308',
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="value" fill="#eab308" radius={[8, 8, 0, 0]}>
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill="#eab308" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </motion.div>

      {/* Top Threats */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="mb-8"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Top 10 Critical Threats
            </CardTitle>
            <CardDescription>Most severe indicators requiring immediate attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4">
              {topThreats.map((threat, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + idx * 0.05 }}
                  className="group relative p-4 bg-gradient-to-r from-gray-900/50 to-gray-800/30 rounded-lg border border-yellow-500/20 hover:border-yellow-500/50 transition-all duration-300"
                >
                  <div className="absolute top-2 left-2 w-8 h-8 bg-yellow-500/10 rounded-full flex items-center justify-center">
                    <span className="text-yellow-500 font-bold text-sm">#{idx + 1}</span>
                  </div>
                  
                  <div className="ml-10 grid grid-cols-1 md:grid-cols-6 gap-4 items-center">
                    <div className="md:col-span-2">
                      <div className="flex items-center gap-2 mb-1">
                        {getTypeIcon(threat.ioc_type)}
                        <span className="px-2 py-1 bg-yellow-500/20 text-yellow-500 rounded text-xs font-semibold">
                          {threat.ioc_type?.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm font-mono text-white break-all group-hover:text-yellow-500 transition-colors">
                        {threat.ioc_value}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Severity</p>
                      <span className={`px-3 py-1 ${getSeverityColor(threat.severity)} text-white rounded-full text-xs font-semibold inline-block`}>
                        {threat.severity}
                      </span>
                    </div>
                    
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Malware Family</p>
                      <p className="text-sm text-white font-medium">{threat.malware_family || 'Unknown'}</p>
                    </div>
                    
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Threat Score</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-red-500 to-red-600"
                            style={{ width: `${(threat.severity_score / 100) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-bold text-red-500">{threat.severity_score}</span>
                      </div>
                    </div>
                    
                    <div>
                      <p className="text-xs text-gray-500 mb-1">VT Detections</p>
                      <div className="flex items-center gap-1">
                        <Shield className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm text-white font-semibold">
                          {threat.vt_detections || 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Full IOC List */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
      >
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-yellow-500" />
                  All Indicators of Compromise
                </CardTitle>
                <CardDescription className="mt-1">
                  Showing {iocs.length.toLocaleString()} IOCs
                  {(selectedType !== 'all' || selectedSeverity !== 'all') && ' (filtered)'}
                </CardDescription>
              </div>
              {iocs.length > 0 && (
                <div className="text-right">
                  <div className="text-2xl font-bold text-yellow-500">{iocs.length}</div>
                  <div className="text-xs text-gray-500">Total Records</div>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-yellow-500/30">
                    <th className="text-left p-4 text-sm font-semibold text-gray-300">Type</th>
                    <th className="text-left p-4 text-sm font-semibold text-gray-300">IOC Value</th>
                    <th className="text-left p-4 text-sm font-semibold text-gray-300">Severity</th>
                    <th className="text-left p-4 text-sm font-semibold text-gray-300">Source</th>
                    <th className="text-left p-4 text-sm font-semibold text-gray-300">First Seen</th>
                  </tr>
                </thead>
                <tbody>
                  <AnimatePresence>
                    {iocs.map((ioc, idx) => (
                      <motion.tr 
                        key={idx}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ delay: idx * 0.01 }}
                        className="border-b border-gray-800 hover:bg-yellow-500/5 transition-all duration-200 group"
                      >
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            {getTypeIcon(ioc.ioc_type)}
                            <span className="px-3 py-1 bg-yellow-500/20 text-yellow-500 rounded-full text-xs font-semibold group-hover:bg-yellow-500/30 transition-colors">
                              {ioc.ioc_type?.toUpperCase()}
                            </span>
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="text-sm font-mono text-gray-300 group-hover:text-yellow-500 transition-colors">
                            {ioc.ioc_value}
                          </span>
                        </td>
                        <td className="p-4">
                          <span className={`px-3 py-1 ${getSeverityColor(ioc.severity)} text-white rounded-full text-xs font-semibold inline-block`}>
                            {ioc.severity}
                          </span>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <Activity className="w-3 h-3 text-gray-500" />
                            <span className="text-sm text-gray-300">{ioc.source}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2 text-gray-400">
                            <Clock className="w-3 h-3" />
                            <span className="text-sm">
                              {new Date(ioc.first_seen).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric', 
                                year: 'numeric' 
                              })}
                            </span>
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
              
              {iocs.length === 0 && (
                <div className="text-center py-12">
                  <Database className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <p className="text-gray-500">No IOCs found matching the current filters</p>
                  <button
                    onClick={() => {
                      setSelectedType('all');
                      setSelectedSeverity('all');
                    }}
                    className="mt-4 px-4 py-2 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all"
                  >
                    Clear Filters
                  </button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default Dashboard;
