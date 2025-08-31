import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { MessageCircle, Users, Settings, BarChart3, Menu, X, Bot, Zap, Shield, Globe } from 'lucide-react';
import ConversationList from './components/ConversationList';
import ConversationChat from './components/ConversationChat';
import Analytics from './components/Analytics';
import NewConversationModal from './components/NewConversationModal';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [agents, setAgents] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch agents and dashboard stats in parallel
      const [agentsResponse, statsResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/agents`),
        axios.get(`${API_BASE_URL}/dashboard/stats`)
      ]);
      
      setAgents(agentsResponse.data || []);
      setDashboardStats(statsResponse.data);
      
    } catch (error) {
      console.error('Error fetching initial data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const Dashboard = () => {
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [showNewConversationModal, setShowNewConversationModal] = useState(false);

    const handleSelectConversation = (conversation) => {
      setSelectedConversation(conversation);
    };

    const handleNewConversation = () => {
      setShowNewConversationModal(true);
    };

    const handleConversationCreated = (data) => {
      console.log('New conversation created:', data);
      // Refresh dashboard stats
      fetchInitialData();
    };

    if (selectedConversation) {
      return (
        <ConversationChat
          conversationId={selectedConversation._id}
          onClose={() => setSelectedConversation(null)}
        />
      );
    }

    return (
      <div className="space-y-6">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">Multi-Agent Customer Service AI Platform</h1>
              <p className="text-blue-100 text-lg">Enterprise-grade customer service automation with coordinated AI agents</p>
              <div className="flex items-center gap-6 mt-4">
                <div className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  <span className="text-sm">~100ms Response Time</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  <span className="text-sm">Enterprise Security</span>
                </div>
                <div className="flex items-center gap-2">
                  <Globe className="h-5 w-5" />
                  <span className="text-sm">Multi-Channel Support</span>
                </div>
              </div>
            </div>
            <div className="hidden lg:block">
              <Bot className="h-24 w-24 text-blue-200" />
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
            <button 
              onClick={fetchInitialData}
              className="mt-2 text-red-600 hover:text-red-800 font-medium"
            >
              Retry
            </button>
          </div>
        )}

        {/* Key Performance Metrics */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Agents</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.active_agents}</p>
                  <p className="text-xs text-green-600">All systems operational</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-lg">
                  <MessageCircle className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Conversations</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.active_conversations}</p>
                  <p className="text-xs text-gray-500">Live customer interactions</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Zap className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Response Time</p>
                  <p className="text-2xl font-bold text-gray-900">{Math.round(dashboardStats.avg_response_time_ms)}ms</p>
                  <p className="text-xs text-green-600">Target: <100ms</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center">
                <div className="p-3 bg-yellow-100 rounded-lg">
                  <BarChart3 className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Customer Satisfaction</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardStats.customer_satisfaction}/5.0</p>
                  <p className="text-xs text-green-600">Target: >4.5</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversation Management */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Conversation Management</h2>
                <button
                  onClick={handleNewConversation}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  New Conversation
                </button>
              </div>
            </div>
            <div className="h-96">
              <ConversationList
                onSelectConversation={handleSelectConversation}
                onNewConversation={handleNewConversation}
              />
            </div>
          </div>

          {/* AI Agents Status */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">AI Agents</h2>
            </div>
            <div className="p-6">
              {loading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {agents.map((agent) => (
                    <div key={agent._id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <Bot className="h-5 w-5 text-blue-600" />
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                            <p className="text-sm text-gray-600">{agent.description}</p>
                          </div>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          agent.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-4">
                          <span className="text-gray-600">
                            Load: {agent.current_load}/{agent.max_concurrent_conversations}
                          </span>
                          <span className="text-gray-600">
                            Model: {agent.configuration.model_name}
                          </span>
                        </div>
                        <div className="text-blue-600">
                          {agent.configuration.model_provider}
                        </div>
                      </div>
                      
                      <div className="mt-3">
                        <div className="flex flex-wrap gap-1">
                          {agent.capabilities.map((capability, index) => (
                            <span key={index} className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs">
                              {capability.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Performance Overview */}
        {dashboardStats && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Performance Overview</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">{dashboardStats.resolution_rate}%</div>
                  <div className="text-sm text-gray-600">Resolution Rate</div>
                  <div className="text-xs text-gray-500 mt-1">Target: >85%</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">{dashboardStats.escalation_rate}%</div>
                  <div className="text-sm text-gray-600">Escalation Rate</div>
                  <div className="text-xs text-gray-500 mt-1">Target: <10%</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{dashboardStats.conversations_today}</div>
                  <div className="text-sm text-gray-600">Conversations Today</div>
                  <div className="text-xs text-gray-500 mt-1">{dashboardStats.messages_today} messages</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* New Conversation Modal */}
        <NewConversationModal
          isOpen={showNewConversationModal}
          onClose={() => setShowNewConversationModal(false)}
          onConversationCreated={handleConversationCreated}
        />
      </div>
    );
  };

  const Sidebar = () => {
    const location = useLocation();
    
    const navigation = [
      { name: 'Dashboard', href: '/', icon: BarChart3 },
      { name: 'Conversations', href: '/conversations', icon: MessageCircle },
      { name: 'Agents', href: '/agents', icon: Users },
      { name: 'Analytics', href: '/analytics', icon: BarChart3 },
      { name: 'Settings', href: '/settings', icon: Settings },
    ];

    return (
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Bot className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">CS-Agent</h1>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        <nav className="mt-6">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5 mr-3" />
                {item.name}
              </Link>
            );
          })}
        </nav>
        
        {/* Status Indicator */}
        <div className="absolute bottom-6 left-6 right-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-green-700 font-medium">System Operational</span>
            </div>
            <p className="text-xs text-green-600 mt-1">All agents online</p>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top bar */}
          <div className="bg-white shadow-sm border-b border-gray-200">
            <div className="flex items-center justify-between h-16 px-6">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden"
              >
                <Menu className="h-6 w-6" />
              </button>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">Multi-Agent Customer Service AI Platform</span>
                <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  Enterprise Ready
                </div>
              </div>
            </div>
          </div>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/conversations" element={<Dashboard />} />
              <Route path="/agents" element={<Dashboard />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/settings" element={<div className="text-center p-8"><Settings className="h-12 w-12 mx-auto mb-4 text-gray-400" /><p className="text-gray-500">Settings panel coming soon...</p></div>} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;