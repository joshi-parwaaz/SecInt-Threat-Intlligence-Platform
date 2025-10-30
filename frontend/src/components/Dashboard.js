import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-900 border border-gray-600 rounded-lg p-3 shadow-xl">
        <p className="text-white font-semibold">{payload[0].name}</p>
        <p className="text-blue-400">{payload[0].value.toLocaleString()} threats</p>
      </div>
    );
  }
  return null;
};

const RADIAN = Math.PI / 180;
const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text 
      x={x} 
      y={y} 
      fill="white" 
      textAnchor={x > cx ? 'start' : 'end'} 
      dominantBaseline="central"
      className="font-bold text-sm"
    >
      {`${(percent * 100).toFixed(1)}%`}
    </text>
  );
};

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(() => fetchAnalytics(), 30000); // poll every 30s
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    const maxRetries = 2;
    let attempt = 0;
    while (attempt <= maxRetries) {
      try {
        const response = await axios.get(`${API_BASE}/api/analytics/summary`);
        setAnalytics(response.data);
        setLoading(false);
        return;
      } catch (err) {
        attempt += 1;
        if (attempt > maxRetries) {
          setError('Failed to load analytics. Please check the backend or network.');
          setLoading(false);
          return;
        }
        // small exponential backoff
        await new Promise((r) => setTimeout(r, 300 * attempt));
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-400">Loading analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded">
        Error loading analytics: {error}
      </div>
    );
  }

  const threatTypeData = Object.entries(analytics.threats_by_type || {}).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value
  }));

  const datasetData = Object.entries(analytics.threats_by_dataset || {}).map(([name, value]) => ({
    name: name.replace('_', ' '),
    count: value
  }));

  return (
    <div className="space-y-8">
      {/* Header with gradient */}
      <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-xl p-8 shadow-2xl">
        <h2 className="text-4xl font-bold text-white mb-2">🛡️ Threat Intelligence Dashboard</h2>
        <p className="text-blue-200 text-lg">Real-time cybersecurity threat analytics and insights</p>
        <div className="mt-4 text-sm text-blue-300">
          Last updated: {analytics.last_updated ? new Date(analytics.last_updated).toLocaleString() : 'N/A'}
        </div>
      </div>

      {/* Stats Cards with gradient backgrounds */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl p-6 shadow-xl transform hover:scale-105 transition-transform">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-blue-200 text-sm font-medium">Total Threats Detected</div>
              <div className="text-4xl font-bold text-white mt-2">{analytics.total_threats?.toLocaleString()}</div>
            </div>
            <div className="text-6xl opacity-20">🎯</div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-xl p-6 shadow-xl transform hover:scale-105 transition-transform">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-green-200 text-sm font-medium">Threat Categories</div>
              <div className="text-4xl font-bold text-white mt-2">{Object.keys(analytics.threats_by_type || {}).length}</div>
            </div>
            <div className="text-6xl opacity-20">📊</div>
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl p-6 shadow-xl transform hover:scale-105 transition-transform">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-purple-200 text-sm font-medium">Active Data Sources</div>
              <div className="text-4xl font-bold text-white mt-2">{Object.keys(analytics.threats_by_dataset || {}).length}</div>
            </div>
            <div className="text-6xl opacity-20">🗄️</div>
          </div>
        </div>
      </div>

      {/* Charts with improved styling */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Threat Types Pie Chart */}
        <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 shadow-2xl">
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
            <span className="mr-3">🔍</span>
            Threat Distribution by Type
          </h3>
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={threatTypeData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={120}
                innerRadius={60}
              >
                {threatTypeData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle"
                formatter={(value, entry) => (
                  <span className="text-white font-medium">
                    {value} ({entry.payload.value.toLocaleString()})
                  </span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Datasets Bar Chart */}
        <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 shadow-2xl">
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
            <span className="mr-3">📦</span>
            Threats by Data Source
          </h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={datasetData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="name" 
                stroke="#9ca3af" 
                angle={-45}
                textAnchor="end"
                height={100}
                tick={{ fill: '#fff', fontSize: 12 }}
              />
              <YAxis 
                stroke="#9ca3af"
                tick={{ fill: '#fff' }}
                tickFormatter={(value) => value.toLocaleString()}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="count" 
                fill="url(#colorGradient)" 
                radius={[8, 8, 0, 0]}
                name="Threat Count"
              />
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#1e40af" stopOpacity={0.8}/>
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Threats with better styling */}
      <div className="bg-gray-800 rounded-xl p-8 border border-gray-700 shadow-2xl">
        <h3 className="text-2xl font-bold text-white mb-6 flex items-center">
          <span className="mr-3">⚡</span>
          Recent Threat Detections
        </h3>
        <div className="space-y-4">
          {analytics.recent_threats && analytics.recent_threats.slice(0, 5).map((threat, idx) => {
            const typeColors = {
              exploit: 'border-red-500 bg-red-900/20',
              phishing: 'border-yellow-500 bg-yellow-900/20',
              malware: 'border-purple-500 bg-purple-900/20',
              credential_leak: 'border-orange-500 bg-orange-900/20',
              unknown: 'border-gray-500 bg-gray-900/20'
            };
            const badgeColors = {
              exploit: 'bg-red-600 text-red-100',
              phishing: 'bg-yellow-600 text-yellow-100',
              malware: 'bg-purple-600 text-purple-100',
              credential_leak: 'bg-orange-600 text-orange-100',
              unknown: 'bg-gray-600 text-gray-100'
            };
            return (
              <div key={idx} className={`border-l-4 ${typeColors[threat.threat_type] || typeColors.unknown} p-5 rounded-lg hover:shadow-lg transition-shadow`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`inline-block px-3 py-1 text-xs font-bold rounded-full ${badgeColors[threat.threat_type] || badgeColors.unknown}`}>
                        {threat.threat_type.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-900 text-blue-200">
                        {threat.dataset}
                      </span>
                      <span className="text-xs text-gray-400">
                        Confidence: {(threat.classification_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-300 mt-2 line-clamp-2">{threat.content}</p>
                  </div>
                  <div className="text-xs text-gray-500 ml-4 text-right">
                    <div>{new Date(threat.timestamp).toLocaleDateString()}</div>
                    <div>{new Date(threat.timestamp).toLocaleTimeString()}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
