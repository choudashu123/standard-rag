import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Send, Sparkles, Loader2, Bot, Upload,
  FileText, CheckCircle2, ChevronUp, AlertCircle, X, Trash2
} from 'lucide-react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isIndexed, setIsIndexed] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  // Upload
  const [showUploader, setShowUploader] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [clearing, setClearing] = useState(false);
  const fileInputRef = useRef(null);

  // Check index status
  const checkStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/status`);
      if (res.ok) {
        const data = await res.json();
        setIsIndexed(data.is_indexed);
      }
    } catch (err) {
      console.error('Status check failed', err);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const id = setInterval(checkStatus, 5000);
    return () => clearInterval(id);
  }, []);

  // Ask question
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
        throw new Error(data.detail || 'Something went wrong.');
      }
      const data = await res.json();
      setResponse(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Upload files
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFiles.length) return;
    setUploading(true);
    setError(null);
    setSuccess(null);
    const formData = new FormData();
    selectedFiles.forEach((f) => formData.append('files', f));
    try {
      const res = await fetch(`${API_URL}/admin/upload`, { method: 'POST', body: formData });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setSuccess(`${selectedFiles.length} document(s) indexed!`);
        setSelectedFiles([]);
        if (fileInputRef.current) fileInputRef.current.value = '';
        checkStatus();
        setTimeout(() => setShowUploader(false), 2000);
      } else {
        throw new Error(data.detail || 'Upload failed. Please ensure the document contains readable text.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...files.filter((f) => !names.has(f.name))];
    });
    setError(null);
    setSuccess(null);
  };

  const removeFile = (idx) => setSelectedFiles((p) => p.filter((_, i) => i !== idx));

  // Clear knowledge base
  const handleClear = async () => {
    if (!window.confirm('Clear the entire knowledge base?')) return;
    setClearing(true);
    setError(null);
    setSuccess(null);
    setResponse(null);
    try {
      const res = await fetch(`${API_URL}/admin/clear`, { method: 'POST' });
      if (res.ok) {
        setSuccess('Knowledge base cleared!');
        setIsIndexed(false);
      } else {
        const data = await res.json();
        throw new Error(data.detail || 'Clear failed.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setClearing(false);
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
          <p className="subtitle">Instant Intelligence from Your Documents</p>
        </motion.div>
      </header>

      <main>
        {/* Action Buttons */}
        <div className="uploader-toggle" style={{ gap: '12px' }}>
          <button
            type="button"
            className={`toggle-btn ${showUploader ? 'active' : ''}`}
            onClick={() => setShowUploader(!showUploader)}
          >
            {showUploader ? <ChevronUp size={18} /> : <Upload size={18} />}
            {showUploader ? 'Close Manager' : 'Add Documents'}
          </button>

          {isIndexed && (
            <button
              type="button"
              className="toggle-btn delete-btn"
              onClick={handleClear}
              disabled={clearing}
            >
              {clearing ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
              Clear Knowledge Base
            </button>
          )}
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

                <form onSubmit={handleUpload}>
                  <div className="drop-zone" onClick={() => fileInputRef.current?.click()}>
                    <input type="file" multiple hidden ref={fileInputRef} onChange={onFileChange} accept=".pdf,.txt" />
                    <Upload className="upload-icon" size={40} />
                    <p>Click to select files</p>
                  </div>

                  {selectedFiles.length > 0 && (
                    <div className="file-preview">
                      {selectedFiles.map((file, idx) => (
                        <div key={idx} className="file-tag">
                          <FileText size={14} />
                          <span>{file.name}</span>
                          <button type="button" className="remove-file-btn" onClick={() => removeFile(idx)}>
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <button type="submit" className="glow-btn full-width" disabled={uploading || !selectedFiles.length}>
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

        {/* Chat Input */}
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
                placeholder={
                  isChecking ? 'Checking index…' :
                  isIndexed ? 'What would you like to know?' :
                  'Upload and index documents first…'
                }
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading || !isIndexed || isChecking}
              />
              <button type="submit" className="glow-btn" disabled={loading || !query.trim() || !isIndexed}>
                {loading ? <Loader2 className="animate-spin" /> : <Send size={20} />}
              </button>
            </div>
          </form>
        </motion.div>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="error-pill">
              <AlertCircle size={16} /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Response */}
        <AnimatePresence>
          {(response || loading) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="glass-card response-area"
            >
              <div className="chat-item">
                <div className="avatar bot-avatar"><Bot size={20} /></div>
                <div className="message-content">
                  <div className="message-header">AI Assistant</div>
                  {loading ? (
                    <div className="loading-dots"><span /><span /><span /></div>
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
