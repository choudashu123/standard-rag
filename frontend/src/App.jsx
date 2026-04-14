import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Send, Sparkles, Loader2, Bot, User, Upload, Shield, LogIn, FileText, CheckCircle2 } from 'lucide-react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'admin'
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Admin states
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [adminUsername, setAdminUsername] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to fetch response');
      }

      const data = await res.json();
      setResponse(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch(`${API_URL}/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: adminUsername, password: adminPassword }),
      });
      if (res.ok) {
        setIsAuthenticated(true);
        setAdminPassword('');
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    for (const file of selectedFiles) {
      formData.append('files', file);
    }

    try {
      const res = await fetch(`${API_URL}/admin/upload`, {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        setSuccess('Documents uploaded and indexed successfully!');
        setSelectedFiles([]);
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="app-container">
      <header>
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="header-content"
        >
          <div className="logo">
            <Sparkles className="icon-glow" />
            <h1 className="gradient-text">Standard RAG</h1>
          </div>
          <p className="subtitle">Intelligent Document Assistant</p>
        </motion.div>

        <nav className="nav-tabs">
          <button 
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => { setActiveTab('chat'); setError(null); setSuccess(null); }}
          >
            <Bot size={18} /> Chat
          </button>
          <button 
            className={`tab-btn ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => { setActiveTab('admin'); setError(null); setSuccess(null); }}
          >
            <Shield size={18} /> Admin
          </button>
        </nav>
      </header>

      <main>
        <AnimatePresence mode="wait">
          {activeTab === 'chat' ? (
            <motion.div
              key="chat"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="glass-card search-container">
                <form onSubmit={handleSearch}>
                  <div className="input-wrapper">
                    <Search className="search-icon" size={20} />
                    <input 
                      type="text" 
                      placeholder="Ask anything about the documents..." 
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      disabled={loading}
                    />
                    <button type="submit" className="glow-btn" disabled={loading || !query.trim()}>
                      {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                    </button>
                  </div>
                </form>
              </div>

              {error && (
                <div className="error-message">{error}</div>
              )}

              {(response || loading) && (
                <div className="glass-card response-area">
                  <div className="chat-item bot">
                    <div className="avatar bot-avatar">
                      <Bot size={20} />
                    </div>
                    <div className="message-content">
                      <div className="message-header">AI Assistant</div>
                      {loading ? (
                        <div className="loading-dots">
                          <span></span><span></span><span></span>
                        </div>
                      ) : (
                        <p className="response-text">{response}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="admin"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              {!isAuthenticated ? (
                <div className="glass-card admin-card">
                  <h2>Admin Login</h2>
                  <form onSubmit={handleAdminLogin}>
                    <div className="form-group">
                      <label>Username</label>
                      <input 
                        type="text" 
                        value={adminUsername}
                        onChange={(e) => setAdminUsername(e.target.value)}
                        placeholder="Enter admin username"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label>Password</label>
                      <input 
                        type="password" 
                        value={adminPassword}
                        onChange={(e) => setAdminPassword(e.target.value)}
                        placeholder="Enter admin password"
                        required
                      />
                    </div>
                    <button type="submit" className="submit-btn flex items-center justify-center gap-2">
                       <LogIn size={18} /> Login
                    </button>
                    {error && <div className="error-message" style={{ marginTop: '1.5rem' }}>{error}</div>}
                  </form>
                </div>
              ) : (
                <div className="glass-card admin-card">
                  <h2>Knowledge Base Manager</h2>
                  {success && (
                    <div className="success-message flex items-center justify-center gap-2">
                      <CheckCircle2 size={18} /> {success}
                    </div>
                  )}
                  {error && <div className="error-message">{error}</div>}
                  
                  <form onSubmit={handleFileUpload}>
                    <label className="upload-zone">
                      <input 
                        type="file" 
                        multiple 
                        hidden 
                        onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
                        accept=".pdf,.txt"
                      />
                      <Upload className="upload-icon mx-auto" size={48} />
                      <p>Click to select multiple PDF or TXT files</p>
                      <p className="text-sm opacity-60">Max 10MB per file</p>
                    </label>

                    {selectedFiles.length > 0 && (
                      <ul className="file-list">
                        {selectedFiles.map((file, idx) => (
                          <li key={idx} className="file-item">
                            <FileText size={16} /> {file.name} ({(file.size / 1024).toFixed(1)} KB)
                          </li>
                        ))}
                      </ul>
                    )}

                    <button 
                      type="submit" 
                      className="submit-btn" 
                      disabled={uploading || selectedFiles.length === 0}
                    >
                      {uploading ? <Loader2 className="animate-spin" /> : 'Process & Index Documents'}
                    </button>
                  </form>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer>
        <p>© 2026 Standard RAG. Powered by Gemini & LangChain.</p>
      </footer>
    </div>
  );
}

export default App;
