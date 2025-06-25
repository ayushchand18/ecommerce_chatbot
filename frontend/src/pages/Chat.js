import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ProductCard from '../components/ProductCard';
import '../styles/Chat.css';

const Chat = ({ user }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Fetch chat sessions on component mount
  useEffect(() => {
    fetchSessions();
    fetchCategories();
  }, []);

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSession) {
      fetchMessages(activeSession);
    } else {
      setMessages([]);
    }
  }, [activeSession]);

  const fetchSessions = async () => {
    try {
      const res = await axios.get('/chat/sessions');
      setSessions(res.data);
      if (res.data.length > 0 && !activeSession) {
        setActiveSession(res.data[0].id);
      }
    } catch (error) {
      console.error('Error fetching sessions:', error);
    }
  };

  const fetchMessages = async (sessionId) => {
    try {
      const res = await axios.get(`/chat/sessions/${sessionId}/messages`);
      setMessages(res.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await axios.get('/categories');
      setCategories(res.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const res = await axios.post('/chat/sessions');
      setSessions([res.data, ...sessions]);
      setActiveSession(res.data.id);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeSession) return;

    setIsLoading(true);
    try {
      const res = await axios.post(`/chat/sessions/${activeSession}/messages`, {
        content: newMessage
      });
      
      setMessages([...messages, res.data.user_message, res.data.bot_message]);
      setNewMessage('');
      
      // Check if the bot response contains product information
      if (res.data.bot_message.content.includes('Here are some products')) {
        const productQuery = extractProductQuery(newMessage);
        if (productQuery) {
          await searchProducts(productQuery);
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const extractProductQuery = (message) => {
    const priceMatch = message.match(/(under|below|less than)\s?\$?(\d+)/i);
    const categoryMatch = message.match(/(electronics|books|clothing|home|sports|toys)/i);
    const productMatch = message.match(/(laptop|phone|book|shirt|etc)/i);
    
    return {
      query: productMatch ? productMatch[0] : '',
      category: categoryMatch ? categoryMatch[0].toLowerCase() : '',
      max_price: priceMatch ? parseInt(priceMatch[2]) : null
    };
  };

  const searchProducts = async (query) => {
    try {
      const params = {};
      if (query.query) params.query = query.query;
      if (query.category) params.category = query.category;
      if (query.max_price) params.max_price = query.max_price;
      
      const res = await axios.get('/products', { params });
      setProducts(res.data);
      
      if (res.data.length > 0) {
        const botMessage = {
          id: Date.now(),
          content: `I found ${res.data.length} products matching your criteria. Here are some options:`,
          is_bot: true,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        const botMessage = {
          id: Date.now(),
          content: "I couldn't find any products matching your criteria. Try different search terms.",
          is_bot: true,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
      }
    } catch (error) {
      console.error('Error searching products:', error);
    }
  };

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="chat-sidebar">
        <button onClick={createNewSession} className="new-session-btn">
          New Chat
        </button>
        <div className="sessions-list">
          {sessions.map(session => (
            <div
              key={session.id}
              className={`session-item ${activeSession === session.id ? 'active' : ''}`}
              onClick={() => setActiveSession(session.id)}
            >
              <div className="session-title">
                Chat {new Date(session.created_at).toLocaleDateString()}
              </div>
              <div className="session-time">
                {new Date(session.updated_at).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="chat-main">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>Welcome to the E-commerce Chatbot</h2>
              <p>Start by asking about products you're interested in, like:</p>
              <ul>
                <li>"Show me laptops under $1000"</li>
                <li>"What books do you have?"</li>
                <li>"I'm looking for red shirts"</li>
              </ul>
            </div>
          ) : (
            messages.map(message => (
              <div
                key={message.id}
                className={`message ${message.is_bot ? 'bot' : 'user'}`}
              >
                <div className="message-content">
                  {message.content}
                </div>
                <div className="message-time">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
        
        <form onSubmit={handleSendMessage} className="chat-input">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message here..."
            disabled={isLoading || !activeSession}
          />
          <button type="submit" disabled={isLoading || !activeSession}>
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
      
      {products.length > 0 && (
        <div className="products-panel">
          <h3>Recommended Products</h3>
          <div className="products-grid">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
