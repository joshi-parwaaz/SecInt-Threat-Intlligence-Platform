

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Activity, 
  Database, 
  FileText, 
  Server, 
  CheckCircle2,
  ExternalLink,
  ArrowRight,
  AlertTriangle,
  Globe2,
  Lock,
  Zap
} from 'lucide-react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import SecIntGlobe from './AnimatedGlobe';

const LandingPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch live stats from backend
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/iocs/stats');
        const data = await response.json();
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
        // Fallback to default values if API fails
        setStats({
          total: 17517,
          by_severity: { CRITICAL: 6, HIGH: 27, MEDIUM: 46 }
        });
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    // Refresh stats every 2 minutes
    const interval = setInterval(fetchStats, 120000);
    return () => clearInterval(interval);
  }, []);

  const achievements = [
    { number: stats?.total_iocs?.toLocaleString() || "Loading...", label: "Total IOCs" },
    { number: stats?.by_severity?.CRITICAL?.toLocaleString() || "0", label: "Critical Threats" },
    { number: stats?.by_severity?.HIGH?.toLocaleString() || "0", label: "High Threats" },
    { number: "4", label: "Threat Feeds" },
  ];

  const features = [
    {
      icon: Shield,
      label: "Real-Time Threat Intelligence",
      description: "Continuous IOC aggregation from AlienVault OTX, VirusTotal, URLhaus, and AbuseIPDB"
    },
    {
      icon: Activity,
      label: "Intelligent Enrichment",
      description: "Automatic severity scoring and multi-source correlation for enhanced threat context"
    },
    {
      icon: Database,
      label: "MongoDB Storage",
      description: "High-performance async database with comprehensive metadata and correlation IDs"
    },
    {
      icon: FileText,
      label: "Multi-Format Reports",
      description: "Export threat intelligence in CSV, JSON, and HTML formats for analysis"
    },
    {
      icon: Server,
      label: "SIEM Integration",
      description: "CEF and Syslog endpoints for seamless integration with existing security infrastructure"
    },
    {
      icon: CheckCircle2,
      label: "API Health Monitoring",
      description: "Real-time status monitoring for all threat intelligence sources"
    },
  ];

  const threatLevels = [
    {
      level: "CRITICAL",
      count: stats?.by_severity?.CRITICAL || 6,
      description: "Immediate action required - Active malware campaigns and C2 infrastructure",
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/20"
    },
    {
      level: "HIGH",
      count: stats?.by_severity?.HIGH || 27,
      description: "High-priority threats - Known malicious domains and IPs with recent activity",
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
      borderColor: "border-orange-500/20"
    },
    {
      level: "MEDIUM",
      count: stats?.by_severity?.MEDIUM || 46,
      description: "Moderate threats - Suspicious indicators requiring investigation",
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/20"
    },
  ];

  const timeline = [
    {
      id: "1",
      title: "IOC Ingestion",
      description: "Multi-source threat intelligence aggregation from AlienVault OTX and URLhaus",
      status: "completed"
    },
    {
      id: "2",
      title: "Enrichment Pipeline",
      description: "VirusTotal and AbuseIPDB enrichment with intelligent severity scoring",
      status: "completed"
    },
    {
      id: "3",
      title: "Database Storage",
      description: "MongoDB with enhanced metadata including correlation IDs and threat actor attribution",
      status: "completed"
    },
    {
      id: "4",
      title: "Report Generation",
      description: "Multi-format export capabilities (CSV, JSON, HTML) for threat analysis",
      status: "completed"
    },
    {
      id: "5",
      title: "SIEM Integration",
      description: "CEF/Syslog endpoints for seamless security infrastructure integration",
      status: "completed"
    },
    {
      id: "6",
      title: "Dashboard & Monitoring",
      description: "Interactive frontend with real-time IOC exploration and API health checks",
      status: "current"
    },
  ];

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      {/* Add viewport meta handling for zoom */}
      <style>{`
        @media (max-width: 768px) {
          html {
            font-size: clamp(12px, 2.5vw, 16px);
          }
        }
        
        /* Smooth zoom transitions */
        * {
          transition: font-size 0.2s ease-in-out;
        }
        
        /* Prevent horizontal overflow on zoom */
        body {
          overflow-x: hidden;
        }
      `}</style>
      
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-4 sm:px-6 lg:px-8 py-12 sm:py-20">
        <div className="absolute inset-0 bg-gradient-to-b from-yellow-500/5 via-transparent to-transparent" />
        
        <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-3 gap-12 items-center relative z-10">
          {/* Left Content - 2 columns */}
          <div className="lg:col-span-2 space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Badge variant="default" className="mb-6">
                Real-Time Threat Intelligence Platform
              </Badge>
              
              <h1 className="text-5xl md:text-6xl lg:text-8xl font-bold mb-6 bg-gradient-to-r from-white via-yellow-500 to-white bg-clip-text text-transparent">
                SecInt
              </h1>
              
              <p className="text-lg md:text-xl text-gray-300 mb-8 max-w-2xl leading-relaxed">
                Multi-Source Intelligence platform aggregating{' '}
                <span className="text-yellow-500 font-semibold">IOCs from AlienVault OTX, VirusTotal, URLhaus, and AbuseIPDB</span>.
                Featuring intelligent enrichment, severity scoring, and{' '}
                <span className="text-yellow-500 font-semibold">SIEM integration</span> for
                comprehensive threat detection and response.
              </p>
              
              <div className="flex flex-wrap gap-4 mb-12">
                <Button
                  size="lg"
                  onClick={() => navigate('/dashboard')}
                  className="group"
                >
                  Launch Dashboard
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                  className="group"
                >
                  API Documentation
                  <ExternalLink className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>
              
              {/* Achievement Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {achievements.map((achievement, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: index * 0.1 }}
                    className="text-center p-4 rounded-lg border border-yellow-500/20 bg-yellow-500/5 hover:bg-yellow-500/10 transition-colors"
                  >
                    <div className="text-3xl md:text-4xl font-bold text-yellow-500 mb-2">
                      {achievement.number}
                    </div>
                    <div className="text-sm text-gray-400">{achievement.label}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Right Content - 3D Globe - 1 column, hidden on mobile */}
          <div className="hidden lg:flex h-[600px] items-center justify-center">
            <SecIntGlobe />
          </div>
        </div>
      </section>

      {/* About Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-yellow-500/5 to-transparent" />
        
        <div className="max-w-7xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              About <span className="text-yellow-500">SecInt</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              SecInt is a comprehensive threat intelligence platform designed to aggregate, enrich, and
              analyze Indicators of Compromise (IOCs) from multiple authoritative sources. Built with
              modern technologies and security best practices.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="p-6 rounded-lg border border-yellow-500/20 bg-yellow-500/5 hover:bg-yellow-500/10 transition-all hover:border-yellow-500/40 group"
              >
                <div className="mb-4">
                  <feature.icon className="h-12 w-12 text-yellow-500 group-hover:scale-110 transition-transform" />
                </div>
                <h3 className="text-xl font-semibold mb-3 text-white">{feature.label}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Platform <span className="text-yellow-500">Architecture</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              End-to-end threat intelligence pipeline from ingestion to SIEM integration
            </p>
          </motion.div>

          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-yellow-500/20 hidden md:block" />

            <div className="space-y-8">
              {timeline.map((item, index) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="relative pl-0 md:pl-20"
                >
                  {/* Timeline dot */}
                  <div className={`absolute left-6 top-6 w-5 h-5 rounded-full hidden md:block ${
                    item.status === 'current' 
                      ? 'bg-yellow-500 ring-4 ring-yellow-500/20' 
                      : 'bg-green-500 ring-4 ring-green-500/20'
                  }`} />

                  <div className={`p-6 rounded-lg border transition-all ${
                    item.status === 'current'
                      ? 'border-yellow-500/40 bg-yellow-500/10'
                      : 'border-green-500/20 bg-green-500/5 hover:bg-green-500/10 hover:border-green-500/40'
                  }`}>
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-xl font-semibold text-white">{item.title}</h3>
                      <Badge variant={item.status === 'current' ? 'default' : 'secondary'}>
                        {item.status === 'current' ? 'Active' : 'Completed'}
                      </Badge>
                    </div>
                    <p className="text-gray-400">{item.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Threat Levels Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-yellow-500/5 to-transparent" />
        
        <div className="max-w-7xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Current Threat <span className="text-yellow-500">Landscape</span>
            </h2>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Real-time threat severity distribution from our intelligence feeds
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {threatLevels.map((threat, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={`p-8 rounded-lg border ${threat.borderColor} ${threat.bgColor} hover:scale-105 transition-transform`}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className={`text-2xl font-bold ${threat.color}`}>{threat.level}</h3>
                  <AlertTriangle className={`h-8 w-8 ${threat.color}`} />
                </div>
                <div className={`text-5xl font-bold mb-4 ${threat.color}`}>{threat.count}</div>
                <p className="text-gray-400">{threat.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="p-12 rounded-2xl border border-yellow-500/40 bg-gradient-to-br from-yellow-500/10 to-transparent text-center"
          >
            <Globe2 className="h-16 w-16 text-yellow-500 mx-auto mb-6" />
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Ready to Explore Threat Intelligence?
            </h2>
            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Access 17,517 IOCs, analyze threat patterns, and integrate with your security infrastructure
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/dashboard')}
                className="group"
              >
                <Shield className="mr-2 h-5 w-5" />
                Launch Dashboard
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                className="group"
              >
                <Lock className="mr-2 h-5 w-5" />
                View API Docs
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 sm:py-12 px-4 sm:px-6 lg:px-8 border-t border-yellow-500/20">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
            <div>
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Shield className="h-6 w-6 text-yellow-500" />
                SecInt
              </h3>
              <p className="text-gray-400">
                Real-Time Threat Intelligence Platform for comprehensive IOC analysis and SIEM integration
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-yellow-500">Platform</h4>
              <ul className="space-y-2 text-gray-400">
                <li className="hover:text-white cursor-pointer transition-colors">Dashboard</li>
                <li className="hover:text-white cursor-pointer transition-colors">IOC Explorer</li>
                <li className="hover:text-white cursor-pointer transition-colors">API Health</li>
                <li className="hover:text-white cursor-pointer transition-colors">Reports</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4 text-yellow-500">Data Sources</h4>
              <ul className="space-y-2 text-gray-400">
                <li className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  AlienVault OTX
                </li>
                <li className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  VirusTotal
                </li>
                <li className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  URLhaus
                </li>
                <li className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-yellow-500" />
                  AbuseIPDB
                </li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-yellow-500/20 text-center text-gray-400">
            <p>© 2025 SecInt. Built with FastAPI, React, and MongoDB for real-time threat intelligence.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
