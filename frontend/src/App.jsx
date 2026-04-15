import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Send, Sparkles, Loader2, Bot, User, Upload, FileText, CheckCircle2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Upload states
  const [showUploader, setShowUploader] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const fileInputRef = useRef(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'The AI is still learning or needs documents to answer.');
      }

      const data = await res.json();
      setResponse(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
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
        setSuccess(`${selectedFiles.length} document(s) added to knowledge base!`);
        setSelectedFiles([]);
        if (fileInputRef.current) fileInputRef.current.value = '';
        setTimeout(() => setShowUploader(false), 2000);
      } else {
        throw new Error('Upload failed. Please try again.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    setSelectedFiles(prev => {
      const existingNames = new Set(prev.map(f => f.name));
      const uniqueNewFiles = newFiles.filter(f => !existingNames.has(f.name));
      return [...prev, ...uniqueNewFiles];
    });
    setError(null);
    setSuccess(null);
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
          <p className="subtitle">Instant Intelligence from Your Documents</p>
        </motion.div>
      </header>

      <main>
        {/* Document Uploader Toggle */}
        <div className="uploader-toggle">
          <button 
            className={`toggle-btn ${showUploader ? 'active' : ''}`}
            onClick={() => setShowUploader(!showUploader)}
          >
            {showUploader ? <ChevronUp size={18} /> : <Upload size={18} />}
            {showUploader ? 'Close Manager' : 'Add Documents'}
          </button>
        </div>

        {/* Upload Section */}
        <AnimatePresence>
          {showUploader && (
            <motion.div
              initial={{ height: 0, opacity: 0, marginBottom: 0 }}
              animate={{ height: 'auto', opacity: 1, marginBottom: '2rem' }}
              exit={{ height: 0, opacity: 0, marginBottom: 0 }}
              className="upload-wrapper"
            >
              <div className="glass-card upload-card">
                <h3>Prepare Your Knowledge Base</h3>
                <p className="hint">Upload PDF or TXT files. They will be indexed for instant querying.</p>
                
                <form onSubmit={handleFileUpload}>
                  <div 
                    className="drop-zone"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <input 
                      type="file" 
                      multiple 
                      hidden 
                      ref={fileInputRef}
                      onChange={onFileChange}
                      accept=".pdf,.txt"
                    />
                    <Upload className="upload-icon" size={40} />
                    <p>Click to select files</p>
                  </div>

                  {selectedFiles.length > 0 && (
                    <div className="file-preview">
                      {selectedFiles.map((file, idx) => (
                        <div key={idx} className="file-tag">
                          <FileText size={14} />
                          <span>{file.name}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <button 
                    type="submit" 
                    className="glow-btn full-width"
                    disabled={uploading || selectedFiles.length === 0}
                  >
                    {uploading ? <Loader2 className="animate-spin" /> : 'Index Documents'}
                  </button>
                </form>

                {success && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="success-pill">
                    <CheckCircle2 size={16} /> {success}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Chat Section */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
          className="glass-card search-container"
          style={{ zIndex: 10 }}
        >
          <form onSubmit={handleSearch}>
            <div className="input-wrapper">
              <Search className="search-icon" size={20} />
              <input 
                type="text" 
                placeholder="What would you like to know?" 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
              />
              <button type="submit" className="glow-btn" disabled={loading || !query.trim()}>
                {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Error/Status Display */}
        <AnimatePresence>
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="error-pill"
            >
              <AlertCircle size={16} /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Response Display */}
        <AnimatePresence>
          {(response || loading) && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="glass-card response-area"
            >
              <div className="chat-item">
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
