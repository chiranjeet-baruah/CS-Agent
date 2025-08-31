import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { MessageCircle, Users, Settings, BarChart3, Menu, X } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/agents`);
      // The new backend returns the agents array directly, not wrapped in an object
      setAgents(response.data || []);
    } catch (error) {
      console.error('Error fetching agents:', error);
      setError('Failed to load agents. Please check your connection.');
      setAgents([]); // Ensure agents is always an array
    } finally {
      setLoading(false);
    }
  };

  const Dashboard = () => (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-lg p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Multi-Agent Customer Service AI Platform</h1>
        <p className="text-gray-600">Enterprise-grade customer service automation with coordinated AI agents</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <button 
            onClick={fetchAgents}
            className="mt-2 text-red-600 hover:text-red-800 font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Agents</p>
              <p className="text-2xl font-bold text-gray-900">{agents.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <MessageCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Conversations Today</p>
              <p className="text-2xl font-bold text-gray-900">0</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <BarChart3 className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Response Time</p>
              <p className="text-2xl font-bold text-gray-900">~100ms</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">AI Agents</h2>
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div key={agent.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    agent.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {agent.status}
                  </span>
                </div>
                <p className="text-gray-600 text-sm mb-3">{agent.description}</p>
                <div className="space-y-1">
                  <p className="text-xs font-medium text-gray-500">Capabilities:</p>
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
  );

  const Sidebar = () => (
    <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform ${
      sidebarOpen ? 'translate-x-0' : '-translate-x-full'
    } transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
      <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">CS-Agent</h1>
        <button
          onClick={() => setSidebarOpen(false)}
          className="lg:hidden"
        >
          <X className="h-6 w-6" />
        </button>
      </div>
      <nav className="mt-6">
        <Link
          to="/"
          className="flex items-center px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-gray-900"
          onClick={() => setSidebarOpen(false)}
        >
          <BarChart3 className="h-5 w-5 mr-3" />
          Dashboard
        </Link>
        <Link
          to="/agents"
          className="flex items-center px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-gray-900"
          onClick={() => setSidebarOpen(false)}
        >
          <Users className="h-5 w-5 mr-3" />
          Agents
        </Link>
        <Link
          to="/conversations"
          className="flex items-center px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-gray-900"
          onClick={() => setSidebarOpen(false)}
        >
          <MessageCircle className="h-5 w-5 mr-3" />
          Conversations
        </Link>
        <Link
          to="/settings"
          className="flex items-center px-6 py-3 text-gray-700 hover:bg-gray-50 hover:text-gray-900"
          onClick={() => setSidebarOpen(false)}
        >
          <Settings className="h-5 w-5 mr-3" />
          Settings
        </Link>
      </nav>
    </div>
  );

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
                <span className="text-sm text-gray-500">Enterprise AI Platform</span>
              </div>
            </div>
          </div>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agents" element={<Dashboard />} />
              <Route path="/conversations" element={<div>Conversations coming soon...</div>} />
              <Route path="/settings" element={<div>Settings coming soon...</div>} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;