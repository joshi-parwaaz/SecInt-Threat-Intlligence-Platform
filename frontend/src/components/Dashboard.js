import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useSpring, useTransform } from 'framer-motion';
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

// Animated Counter Component
const AnimatedCounter = ({ value, duration = 1 }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startValue = 0;
    const endValue = value || 0;
    const startTime = Date.now();
    const animationDuration = duration * 1000;

    const animate = () => {
      const currentTime = Date.now();
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / animationDuration, 1);
      
      // Ease out animation
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(startValue + (endValue - startValue) * easeProgress);
      
      setDisplayValue(current);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setDisplayValue(endValue);
      }
    };

    animate();
  }, [value, duration]);

  return <>{displayValue.toLocaleString()}</>;
};

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
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestionStatus, setIngestionStatus] = useState(null);

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

  // Fetch all data (manual refresh)
  const fetchData = async () => {
    setLoading(true);
    setIsRefreshing(true);
    setError(null);
    setShowSuccessMessage(false);
    
    // Start time for minimum loading duration
    const startTime = Date.now();
    
    try {
      await Promise.all([
        fetchStats(),
        fetchIOCs(),
        fetchTopThreats(),
        fetchBlocklist(),
        fetchAPIHealth()
      ]);
      setLastUpdated(new Date());
      
      // Ensure minimum 1.2 seconds loading time for better UX visibility
      const elapsedTime = Date.now() - startTime;
      const remainingTime = Math.max(0, 1200 - elapsedTime);
      
      if (remainingTime > 0) {
        await new Promise(resolve => setTimeout(resolve, remainingTime));
      }
      
      // Show success message
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      // Keep refresh animation for a bit longer for visual feedback
      setTimeout(() => setIsRefreshing(false), 1000);
    }
  };

  // Initial load
  useEffect(() => {
    fetchData();
  }, []);

  // Auto-refresh every 30 seconds (without loading state)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStats();
      fetchIOCs();
      fetchTopThreats();
      fetchBlocklist();
    }, 30000);
    return () => clearInterval(interval);
  }, [selectedType, selectedSeverity]);

  // Auto-refresh for API health every 2 minutes
  useEffect(() => {
    const apiInterval = setInterval(fetchAPIHealth, 120000);
    return () => clearInterval(apiInterval);
  }, []);

  // Re-fetch IOCs when filters change
  useEffect(() => {
    if (stats) {
      fetchIOCs();
    }
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

  // Trigger ingestion
  const triggerIngestion = async () => {
    setIsIngesting(true);
    try {
      const response = await fetch('http://localhost:8000/api/ingestion/trigger', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (response.ok) {
        // Start polling for status
        pollIngestionStatus();
      } else {
        alert(data.detail || 'Failed to start ingestion');
        setIsIngesting(false);
      }
    } catch (err) {
      console.error('Error triggering ingestion:', err);
      alert('Failed to start ingestion');
      setIsIngesting(false);
    }
  };

  // Poll ingestion status
  const pollIngestionStatus = async () => {
    const checkStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/ingestion/status');
        const data = await response.json();
        setIngestionStatus(data);
        
        if (!data.running) {
          setIsIngesting(false);
          if (data.last_result?.status === 'success') {
            // Refresh data after successful ingestion
            await fetchData();
            alert(`Ingestion complete! Added ${data.last_result.stats?.iocs_stored || 0} new IOCs`);
          } else if (data.last_result?.status === 'error') {
            alert(`Ingestion failed: ${data.last_result.error}`);
          }
          return false; // Stop polling
        }
        return true; // Continue polling
      } catch (err) {
        console.error('Error checking ingestion status:', err);
        setIsIngesting(false);
        return false;
      }
    };
    
    // Poll every 2 seconds
    const poll = async () => {
      const shouldContinue = await checkStatus();
      if (shouldContinue) {
        setTimeout(poll, 2000);
      }
    };
    
    poll();
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
    { name: 'Critical', value: stats.by_severity?.CRITICAL || 0, color: '#E74C3C' },
    { name: 'High', value: stats.by_severity?.HIGH || 0, color: '#E67E22' },
    { name: 'Medium', value: stats.by_severity?.MEDIUM || 0, color: '#F1C40F' },
    { name: 'Low', value: stats.by_severity?.LOW || 0, color: '#2ECC71' }
  ] : [];

  const typeData = stats?.by_type ? Object.entries(stats.by_type).map(([name, value]) => ({
    name: name.toUpperCase(),
    value,
    color: '#F1C40F'
  })) : [];

  // Heatmap data: Severity (rows) vs Type (columns)
  const heatmapData = stats ? (() => {
    const severityLevels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    const types = Object.keys(stats.by_type || {});
    
    // Create mock distribution data (in production, this would come from backend)
    // For now, distribute proportionally based on severity and type
    const totalIOCs = stats.total_iocs || 0;
    const data = [];
    
    severityLevels.forEach(severity => {
      const row = { severity };
      const severityCount = stats.by_severity?.[severity] || 0;
      
      types.forEach(type => {
        const typeCount = stats.by_type?.[type] || 0;
        // Proportional distribution (this is a simplified calculation)
        const estimate = totalIOCs > 0 ? Math.round((severityCount * typeCount) / totalIOCs) : 0;
        row[type] = estimate;
      });
      
      data.push(row);
    });
    
    return data;
  })() : [];

  const heatmapTypes = stats?.by_type ? Object.keys(stats.by_type) : [];

  // Calculate max value for heatmap color intensity
  const maxHeatmapValue = Math.max(
    ...heatmapData.flatMap(row => 
      Object.entries(row)
        .filter(([key]) => key !== 'severity')
        .map(([, value]) => value)
    ),
    1
  );

  // Get color intensity for heatmap
  const getHeatmapColor = (value, severity) => {
    const baseColors = {
      CRITICAL: { r: 231, g: 76, b: 60 },   // #E74C3C
      HIGH: { r: 230, g: 126, b: 34 },      // #E67E22
      MEDIUM: { r: 241, g: 196, b: 15 },    // #F1C40F
      LOW: { r: 46, g: 204, b: 113 }        // #2ECC71
    };
    
    const base = baseColors[severity];
    const intensity = value / maxHeatmapValue;
    const minOpacity = 0.15;
    const opacity = minOpacity + (intensity * (1 - minOpacity));
    
    return `rgba(${base.r}, ${base.g}, ${base.b}, ${opacity})`;
  };

  // Calculate insights
  const insights = stats && typeData.length > 0 ? (() => {
    const totalIOCs = stats.total_iocs || 0;
    const topType = typeData.reduce((max, curr) => curr.value > max.value ? curr : max, typeData[0]);
    const topTypePercentage = totalIOCs > 0 ? ((topType.value / totalIOCs) * 100).toFixed(1) : 0;
    
    const avgTypeCount = typeData.reduce((sum, t) => sum + t.value, 0) / typeData.length;
    const topTypeMultiplier = avgTypeCount > 0 ? (topType.value / avgTypeCount).toFixed(1) : 0;
    
    const criticalPercentage = totalIOCs > 0 ? ((stats.by_severity?.CRITICAL || 0) / totalIOCs * 100).toFixed(1) : 0;
    
    return {
      topType: topType.name,
      topTypePercentage,
      topTypeMultiplier,
      criticalPercentage,
      totalIOCs
    };
  })() : null;

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
            <p className="text-gray-400 flex items-center gap-2">
              Real-time monitoring and analysis
              {loading && <span className="ml-2 text-yellow-500 animate-pulse">● Refreshing data...</span>}
              {!loading && lastUpdated && (
                <span className="ml-2 text-gray-500 text-sm">
                  • Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={triggerIngestion}
              disabled={isIngesting}
              className="flex items-center gap-2 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              <Database className={`w-5 h-5 ${isIngesting ? 'animate-bounce' : ''}`} />
              {isIngesting ? 'Ingesting...' : 'Ingest New IOCs'}
            </button>
            <button
              onClick={fetchData}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-yellow-500 text-black rounded-lg hover:bg-yellow-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
              {loading ? 'Refreshing...' : 'Refresh Data'}
            </button>
          </div>
        </div>
        {/* Progress Bar */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-6"
          >
            <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden shadow-inner border border-gray-700">
              <motion.div
                className="h-full bg-gradient-to-r from-yellow-500 via-yellow-400 to-yellow-500 shadow-lg"
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: 1, ease: "linear", repeat: Infinity }}
                style={{
                  boxShadow: '0 0 10px rgba(234, 179, 8, 0.5)'
                }}
              />
            </div>
            <div className="flex items-center justify-center gap-2 mt-3">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <RefreshCw className="w-4 h-4 text-yellow-500" />
              </motion.div>
              <p className="text-sm text-yellow-500 font-medium">Fetching latest threat intelligence data...</p>
            </div>
          </motion.div>
        )}
        
        {/* Ingestion Progress */}
        {isIngesting && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-6"
          >
            <div className="h-2 w-full bg-gray-800 rounded-full overflow-hidden shadow-inner border border-green-700">
              <motion.div
                className="h-full bg-gradient-to-r from-green-500 via-green-400 to-green-500 shadow-lg"
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: 2, ease: "linear", repeat: Infinity }}
                style={{
                  boxShadow: '0 0 10px rgba(34, 197, 94, 0.5)'
                }}
              />
            </div>
            <div className="flex flex-col items-center justify-center gap-2 mt-3">
              <div className="flex items-center gap-2">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                >
                  <Database className="w-4 h-4 text-green-500" />
                </motion.div>
                <p className="text-sm text-green-500 font-medium">
                  {ingestionStatus?.progress || 'Ingesting new IOCs from threat feeds...'}
                </p>
              </div>
              <p className="text-xs text-gray-500">
                This may take 1-3 minutes • Fetching from OTX, URLhaus
              </p>
            </div>
          </motion.div>
        )}
        
        {/* Success Message */}
        {showSuccessMessage && !loading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 flex items-center justify-center gap-2 bg-green-500/10 border border-green-500/30 rounded-lg p-3"
          >
            <CheckCircle className="w-5 h-5 text-green-500" />
            <p className="text-green-500 font-medium">Dashboard refreshed successfully!</p>
          </motion.div>
        )}
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
        <motion.div 
          whileHover={{ scale: 1.05 }} 
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className={`relative overflow-hidden ${isRefreshing ? 'ring-2 ring-yellow-500/50' : ''} transition-all`}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-full -mr-16 -mt-16" />
            {isRefreshing && (
              <motion.div 
                className="absolute inset-0 bg-yellow-500/10"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.5, 0] }}
                transition={{ duration: 0.8, ease: "easeInOut" }}
              />
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Total IOCs</CardTitle>
                <Database className="w-8 h-8 text-yellow-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-yellow-500 mb-2">
                <AnimatedCounter value={stats?.total_iocs || 0} duration={1.2} />
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <TrendingUp className="w-3 h-3 text-green-500" />
                <span>Across all sources</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.05 }} 
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className={`relative overflow-hidden ${isRefreshing ? 'ring-2 ring-red-500/50' : ''} transition-all`}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full -mr-16 -mt-16" />
            {isRefreshing && (
              <motion.div 
                className="absolute inset-0 bg-red-500/10"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.5, 0] }}
                transition={{ duration: 0.8, delay: 0.1, ease: "easeInOut" }}
              />
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Critical Threats</CardTitle>
                <AlertTriangle className="w-8 h-8 text-red-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-red-500 mb-2">
                <AnimatedCounter value={stats?.by_severity?.CRITICAL || 0} duration={1.2} />
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Zap className="w-3 h-3 text-red-500" />
                <span>Require immediate action</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.05 }} 
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className={`relative overflow-hidden ${isRefreshing ? 'ring-2 ring-orange-500/50' : ''} transition-all`}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/10 rounded-full -mr-16 -mt-16" />
            {isRefreshing && (
              <motion.div 
                className="absolute inset-0 bg-orange-500/10"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.5, 0] }}
                transition={{ duration: 0.8, delay: 0.2, ease: "easeInOut" }}
              />
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">High Priority</CardTitle>
                <Shield className="w-8 h-8 text-orange-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-orange-500 mb-2">
                <AnimatedCounter value={stats?.by_severity?.HIGH || 0} duration={1.2} />
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Eye className="w-3 h-3 text-orange-500" />
                <span>High severity indicators</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.05 }} 
          transition={{ type: "spring", stiffness: 300 }}
        >
          <Card className={`relative overflow-hidden ${isRefreshing ? 'ring-2 ring-yellow-500/50' : ''} transition-all`}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/10 rounded-full -mr-16 -mt-16" />
            {isRefreshing && (
              <motion.div 
                className="absolute inset-0 bg-yellow-500/10"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.5, 0] }}
                transition={{ duration: 0.8, delay: 0.3, ease: "easeInOut" }}
              />
            )}
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-gray-400">Recent (24h)</CardTitle>
                <Clock className="w-8 h-8 text-yellow-500/50" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-yellow-500 mb-2">
                <AnimatedCounter value={stats?.recent_count || 0} duration={1.2} />
              </div>
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
        {/* Severity vs Type Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              Severity Distribution Heatmap
            </CardTitle>
            <CardDescription>IOC severity across threat types</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Heatmap */}
              <div>
                {/* Column Headers */}
                <div className="grid gap-2 mb-2" style={{ gridTemplateColumns: `140px repeat(${heatmapTypes.length}, 1fr)` }}>
                  <div className="text-xs font-semibold text-gray-400 flex items-center justify-end pr-3">
                    Severity / Type
                  </div>
                  {heatmapTypes.map((type, idx) => (
                    <div key={idx} className="text-xs font-semibold text-gray-300 text-center">
                      {type.toUpperCase()}
                    </div>
                  ))}
                </div>
                
                {/* Heatmap Rows */}
                {heatmapData.map((row, rowIdx) => (
                    <motion.div
                      key={rowIdx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.6 + rowIdx * 0.1 }}
                      className="grid gap-2 mb-2"
                      style={{ gridTemplateColumns: `140px repeat(${heatmapTypes.length}, 1fr)` }}
                    >
                      {/* Row Label */}
                      <div className="flex items-center justify-end pr-3">
                        <span 
                          className="text-xs font-bold px-3 py-1 rounded-lg"
                          style={{ 
                            backgroundColor: severityData.find(s => s.name.toUpperCase() === row.severity)?.color + '30',
                            color: severityData.find(s => s.name.toUpperCase() === row.severity)?.color
                          }}
                        >
                          {row.severity}
                        </span>
                      </div>
                      
                      {/* Cells */}
                      {heatmapTypes.map((type, cellIdx) => {
                        const value = row[type] || 0;
                        const totalForType = stats.by_type?.[type] || 1;
                        const percentage = ((value / totalForType) * 100).toFixed(1);
                        
                        return (
                          <motion.div
                            key={cellIdx}
                            whileHover={{ scale: 1.08 }}
                            className="group relative rounded-lg border-2 transition-all cursor-pointer flex items-center justify-center"
                            style={{
                              aspectRatio: '1',
                              backgroundColor: getHeatmapColor(value, row.severity),
                              borderColor: value > 0 ? severityData.find(s => s.name.toUpperCase() === row.severity)?.color + '60' : '#374151',
                              boxShadow: value > 0 ? `0 0 10px ${severityData.find(s => s.name.toUpperCase() === row.severity)?.color}40` : 'none'
                            }}
                          >
                            <span className="text-sm font-bold text-white text-center">
                              {value > 0 ? value.toLocaleString() : '-'}
                            </span>
                            
                            {/* Tooltip */}
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 border-2 border-yellow-500 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10 shadow-xl">
                              <div className="text-xs text-yellow-500 font-bold mb-1">{row.severity} severity {type.toUpperCase()}</div>
                              <div className="text-xs text-white font-semibold">{value.toLocaleString()} IOCs</div>
                              <div className="text-xs text-gray-400">({percentage}% of type)</div>
                            </div>
                          </motion.div>
                        );
                      })}
                    </motion.div>
                  ))}
              </div>
              
              {/* Legend */}
              <div className="flex items-center gap-4 pt-4 border-t border-gray-800">
                <span className="text-xs text-gray-400 font-semibold">Intensity:</span>
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-xs text-gray-500">Low</span>
                  <div className="flex-1 h-3 rounded-full bg-gradient-to-r from-gray-800 via-yellow-500/50 to-yellow-500"></div>
                  <span className="text-xs text-gray-500">High</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* IOC Types Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              IOC Types Distribution
            </CardTitle>
            <CardDescription>Breakdown by indicator type (Log Scale)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Bar Chart */}
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={typeData} margin={{ top: 25, right: 30, left: 70, bottom: 45 }}>
                <XAxis 
                  dataKey="name" 
                  stroke="#B0B3B8" 
                  style={{ fontSize: '12px', fontWeight: '600' }}
                  label={{ 
                    value: 'IOC Type', 
                    position: 'insideBottom', 
                    offset: -12,
                    style: { fill: '#FFFFFF', fontSize: '13px', fontWeight: '700' }
                  }}
                />
                <YAxis 
                  scale="log" 
                  domain={[1, 'auto']}
                  stroke="#B0B3B8" 
                  style={{ fontSize: '12px', fontWeight: '600' }}
                  tickFormatter={(value) => {
                    if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
                    return value;
                  }}
                  label={{ 
                    value: 'Count (Log Scale)', 
                    angle: -90, 
                    position: 'insideLeft',
                    offset: -15,
                    style: { fill: '#F1C40F', fontSize: '13px', fontWeight: '700' }
                  }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#0B0C10', 
                    border: '2px solid #F1C40F',
                    borderRadius: '12px',
                    padding: '12px'
                  }}
                  formatter={(value) => [`${value.toLocaleString()} IOCs`, 'Count']}
                  labelStyle={{ color: '#F1C40F', fontWeight: 'bold', marginBottom: '4px' }}
                />
                <Bar 
                  dataKey="value" 
                  fill="#F1C40F" 
                  radius={[8, 8, 0, 0]}
                  label={{ 
                    position: 'top', 
                    fill: '#FFFFFF', 
                    fontSize: 13,
                    fontWeight: 'bold',
                    formatter: (value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value
                  }}
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill="#F1C40F" />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Insight Panel */}
            {insights && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 }}
                className="bg-gray-900/80 rounded-lg p-5 border border-gray-800"
              >
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-yellow-500" />
                  Key Insights
                </h4>
                <div className="space-y-2.5 text-xs">
                  {/* Insight 1: Dominant Type */}
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 mt-1.5 flex-shrink-0"></div>
                    <p className="text-gray-300 leading-relaxed">
                      <span className="text-yellow-500 font-bold">{insights.topType}</span> accounts for{' '}
                      <span className="text-white font-semibold">{insights.topTypePercentage}%</span> of total IOCs,
                      indicating {insights.topType.toLowerCase()}-based threats are dominant.
                    </p>
                  </div>

                  {/* Insight 2: Activity Multiplier */}
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0"></div>
                    <p className="text-gray-300 leading-relaxed">
                      <span className="text-blue-400 font-bold">{insights.topType}</span> activity is{' '}
                      <span className="text-white font-semibold">{insights.topTypeMultiplier}×</span> higher
                      than the average IOC category.
                    </p>
                  </div>

                  {/* Insight 3: Critical Percentage */}
                  {parseFloat(insights.criticalPercentage) > 5 && (
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 flex-shrink-0"></div>
                      <p className="text-gray-300 leading-relaxed">
                        <span className="text-red-400 font-bold">{insights.criticalPercentage}%</span> of IOCs
                        are <span className="text-red-400 font-semibold">CRITICAL</span> severity,
                        requiring immediate security response.
                      </p>
                    </div>
                  )}

                  {/* Insight 4: Distribution Pattern */}
                  {stats?.by_severity && (
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5 flex-shrink-0"></div>
                      <p className="text-gray-300 leading-relaxed">
                        {Object.keys(stats.by_type || {}).length} distinct IOC types detected across{' '}
                        <span className="text-white font-semibold">{insights.totalIOCs.toLocaleString()}</span> indicators.
                      </p>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
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
