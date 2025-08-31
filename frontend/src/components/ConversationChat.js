import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Bot, User, Clock, AlertCircle, CheckCircle, Loader } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL;

const ConversationChat = ({ conversationId, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversation, setConversation] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const [websocket, setWebsocket] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (conversationId) {
      fetchConversation();
      initializeWebSocket();
    }
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [conversationId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchConversation = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/conversations/${conversationId}`);
      setConversation(response.data);
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching conversation:', error);
    }
  };

  const initializeWebSocket = () => {
    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//localhost:8001/ws/${conversationId}?user_type=customer&user_id=customer_123`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWebsocket(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (conversationId) {
            initializeWebSocket();
          }
        }, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Error initializing WebSocket:', error);
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'new_message':
        const messageData = data.data;
        const newMsg = {
          id: messageData.message_id,
          content: messageData.content,
          sender_type: messageData.sender_type,
          sender_id: messageData.sender_id,
          timestamp: new Date().toISOString(),
          metadata: messageData.metadata || {}
        };
        setMessages(prev => [...prev, newMsg]);
        break;
        
      case 'typing_indicator':
        setIsTyping(data.data.typing_agents.length > 0);
        break;
        
      case 'status_update':
        console.log('Status update:', data.data.message);
        break;
        
      case 'agent_assigned':
        console.log(`Agent assigned: ${data.data.agent_name}`);
        break;
        
      case 'escalation':
        console.log('Conversation escalated:', data.data.reason);
        break;
        
      default:
        console.log('Unknown WebSocket message:', data);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || isLoading) return;

    const messageContent = newMessage.trim();
    setNewMessage('');
    setIsLoading(true);

    try {
      // Add user message to local state immediately
      const userMessage = {
        id: `temp_${Date.now()}`,
        content: messageContent,
        sender_type: 'user',
        sender_id: 'customer_123',
        timestamp: new Date().toISOString(),
        metadata: {}
      };
      setMessages(prev => [...prev, userMessage]);

      // Send message to backend
      const response = await axios.post(`${API_BASE_URL}/conversations/${conversationId}/messages`, {
        content: messageContent,
        attachments: [],
        metadata: {}
      });

      // The agent response will come through WebSocket
      console.log('Message sent successfully:', response.data);

    } catch (error) {
      console.error('Error sending message:', error);
      // Remove the temporary message on error
      setMessages(prev => prev.filter(msg => msg.id !== `temp_${Date.now()}`));
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getMessageIcon = (senderType) => {
    switch (senderType) {
      case 'agent':
        return <Bot className="h-4 w-4 text-blue-600" />;
      case 'user':
        return <User className="h-4 w-4 text-gray-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getMessageBubbleClass = (senderType) => {
    const baseClass = "max-w-xs lg:max-w-md px-4 py-2 rounded-lg break-words";
    switch (senderType) {
      case 'user':
        return `${baseClass} bg-blue-600 text-white ml-auto`;
      case 'agent':
        return `${baseClass} bg-gray-100 text-gray-900`;
      default:
        return `${baseClass} bg-yellow-50 text-yellow-900 border border-yellow-200`;
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Conversation {conversationId?.slice(-8)}
          </h2>
          {conversation && (
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                conversation.status === 'active' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {conversation.status}
              </span>
              <span>Priority: {conversation.priority}</span>
              <span>Channel: {conversation.channel}</span>
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          ×
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={message.id || index}
            className={`flex items-start gap-2 ${
              message.sender_type === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              {getMessageIcon(message.sender_type)}
            </div>
            <div className="flex flex-col space-y-1">
              <div className={getMessageBubbleClass(message.sender_type)}>
                <p className="text-sm">{message.content}</p>
              </div>
              <div className={`text-xs text-gray-500 ${
                message.sender_type === 'user' ? 'text-right' : 'text-left'
              }`}>
                {formatTimestamp(message.timestamp)}
                {message.is_ai_generated && (
                  <span className="ml-1 inline-flex items-center">
                    <Bot className="h-3 w-3" />
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {/* Typing indicator */}
        {isTyping && (
          <div className="flex items-start gap-2">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
              <Bot className="h-4 w-4 text-blue-600" />
            </div>
            <div className="bg-gray-100 text-gray-900 max-w-xs px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!newMessage.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? <Loader className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConversationChat;