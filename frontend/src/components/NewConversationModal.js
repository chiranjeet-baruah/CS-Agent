import React, { useState } from 'react';
import axios from 'axios';
import { X, Mail, MessageCircle, Phone, Smartphone } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const NewConversationModal = ({ isOpen, onClose, onConversationCreated }) => {
  const [formData, setFormData] = useState({
    customer_email: '',
    customer_name: '',
    channel: 'web_chat',
    priority: 'medium',
    initial_message: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.initial_message.trim()) {
      setError('Please enter an initial message');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/conversations`, {
        customer_email: formData.customer_email || null,
        customer_name: formData.customer_name || null,
        channel: formData.channel,
        priority: formData.priority,
        initial_message: formData.initial_message,
        metadata: {
          source: 'admin_panel',
          created_by: 'admin'
        }
      });

      // Reset form
      setFormData({
        customer_email: '',
        customer_name: '',
        channel: 'web_chat',
        priority: 'medium',
        initial_message: ''
      });

      // Notify parent component
      if (onConversationCreated) {
        onConversationCreated(response.data);
      }

      onClose();

    } catch (error) {
      console.error('Error creating conversation:', error);
      setError(error.response?.data?.detail || 'Failed to create conversation');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getChannelIcon = (channel) => {
    switch (channel) {
      case 'web_chat':
        return <MessageCircle className="h-4 w-4" />;
      case 'email':
        return <Mail className="h-4 w-4" />;
      case 'phone':
        return <Phone className="h-4 w-4" />;
      case 'sms':
        return <Smartphone className="h-4 w-4" />;
      default:
        return <MessageCircle className="h-4 w-4" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="inline-block w-full max-w-md p-6 my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-lg">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Start New Conversation</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Customer Information */}
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-700">Customer Information (Optional)</h4>
              
              <div>
                <label htmlFor="customer_name" className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Name
                </label>
                <input
                  type="text"
                  id="customer_name"
                  name="customer_name"
                  value={formData.customer_name}
                  onChange={handleInputChange}
                  placeholder="Enter customer name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="customer_email" className="block text-sm font-medium text-gray-700 mb-1">
                  Customer Email
                </label>
                <input
                  type="email"
                  id="customer_email"
                  name="customer_email"
                  value={formData.customer_email}
                  onChange={handleInputChange}
                  placeholder="customer@example.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Channel Selection */}
            <div>
              <label htmlFor="channel" className="block text-sm font-medium text-gray-700 mb-1">
                Channel
              </label>
              <select
                id="channel"
                name="channel"
                value={formData.channel}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="web_chat">
                  Web Chat
                </option>
                <option value="email">
                  Email
                </option>
                <option value="phone">
                  Phone
                </option>
                <option value="sms">
                  SMS
                </option>
                <option value="whatsapp">
                  WhatsApp
                </option>
              </select>
            </div>

            {/* Priority Selection */}
            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                id="priority"
                name="priority"
                value={formData.priority}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            {/* Initial Message */}
            <div>
              <label htmlFor="initial_message" className="block text-sm font-medium text-gray-700 mb-1">
                Initial Message *
              </label>
              <textarea
                id="initial_message"
                name="initial_message"
                value={formData.initial_message}
                onChange={handleInputChange}
                rows={4}
                placeholder="Enter the initial message to start the conversation..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !formData.initial_message.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {loading && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
                {loading ? 'Creating...' : 'Start Conversation'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewConversationModal;