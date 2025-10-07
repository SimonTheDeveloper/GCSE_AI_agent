import React, { useCallback, useEffect, useRef, useState } from 'react';
import { authHeader } from '../auth';
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

export default function Homework() {
  const [text, setText] = useState('');
  const [files, setFiles] = useState([]);
  const [images, setImages] = useState([]); // data URLs for pasted/dropped images
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const dropRef = useRef(null);

  // Handle file select
  const onFileChange = (e) => {
    const list = Array.from(e.target.files || []);
    setFiles((prev) => [...prev, ...list]);
  };

  // Drag & drop handlers
  const onDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };
  const onDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };
  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const items = Array.from(e.dataTransfer.items || []);
    const filePromises = [];
    items.forEach((it) => {
      if (it.kind === 'file') {
        const f = it.getAsFile();
        if (f) filePromises.push(Promise.resolve(f));
      }
    });
    Promise.all(filePromises).then((newFiles) => {
      if (!newFiles.length) return;
      newFiles.forEach((f) => {
        if (f.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = () => setImages((prev) => [...prev, reader.result]);
          reader.readAsDataURL(f);
        }
      });
      setFiles((prev) => [...prev, ...newFiles]);
    });
  };

  // Paste support for images or text
  const onPaste = useCallback((e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    let handled = false;
    for (const it of items) {
      if (it.type && it.type.startsWith('image/')) {
        const blob = it.getAsFile();
        if (blob) {
          const reader = new FileReader();
          reader.onload = () => setImages((prev) => [...prev, reader.result]);
          reader.readAsDataURL(blob);
          handled = true;
        }
      }
    }
    // If not an image, let default paste fill the textarea
    if (!handled) return;
    e.preventDefault();
  }, []);

  useEffect(() => {
    // Bind paste listener on the page to catch screenshots
    const handler = (e) => onPaste(e);
    window.addEventListener('paste', handler);
    return () => window.removeEventListener('paste', handler);
  }, [onPaste]);

  const removeFile = (idx) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };
  const removeImage = (idx) => {
    setImages((prev) => prev.filter((_, i) => i !== idx));
  };

  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      // We'll send images from "files" only; pasted previews are already in files when dropped.
      const fd = new FormData();
      // uid is set by AppBootstrap to localStorage and store; we can pick it from localStorage fast
      const uid = localStorage.getItem('uid');
      if (!uid) throw new Error('Please wait for bootstrap to finish (no uid).');
      fd.append('uid', uid);
      fd.append('question', text || '');
      (files || []).forEach((f) => fd.append('files', f));

      const res = await fetch(`${API_BASE}/api/v1/homework/submit`, {
        method: 'POST',
        headers: { ...authHeader() },
        body: fd,
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`Homework submit failed: ${res.status} ${res.statusText} - ${t}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error('Homework submit error:', err);
      setError(err.message || String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="section section-padding">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-10">
            <div className="courses-details">
              <div className="details-main-body">
                <div className="details-title">
                  <h2>My homework</h2>
                  <p>Type your question, upload a file (PDF, DOCX, images), or paste a screenshot. You can also drag-and-drop files or images below.</p>
                </div>

                <form onSubmit={handleSubmit}>
                  <div className="row g-3">
                    <div className="col-12">
                      <label className="form-label">Your question</label>
                      <textarea
                        className="form-control"
                        rows={6}
                        placeholder="Describe your question or assignment details..."
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                      />
                    </div>

                    <div className="col-12">
                      <label className="form-label">Upload files</label>
                      <div className="d-flex align-items-center gap-2 mb-2">
                        <input
                          ref={fileInputRef}
                          type="file"
                          multiple
                          className="form-control"
                          onChange={onFileChange}
                          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.gif,.heic,.webp,.txt"
                        />
                      </div>
                      {files.length > 0 && (
                        <ul className="list-group mb-3">
                          {files.map((f, i) => (
                            <li key={i} className="list-group-item d-flex justify-content-between align-items-center">
                              <span>{f.name} <small className="text-muted">({Math.round(f.size/1024)} KB)</small></span>
                              <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => removeFile(i)}>Remove</button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>

                    <div className="col-12">
                      <label className="form-label">Paste or drop an image</label>
                      <div
                        ref={dropRef}
                        onDragOver={onDragOver}
                        onDragLeave={onDragLeave}
                        onDrop={onDrop}
                        className={`p-4 border rounded text-center ${dragOver ? 'bg-light' : ''}`}
                        style={{borderStyle: 'dashed'}}
                      >
                        <p className="mb-1">Drag & drop images here, or press Cmd+Ctrl+Shift+4 and paste a screenshot.</p>
                        <p className="text-muted mb-0">Pasted images will appear below. You can paste directly anywhere on this page.</p>
                      </div>
                      {images.length > 0 && (
                        <div className="row mt-3 g-3">
                          {images.map((src, i) => (
                            <div key={i} className="col-6 col-md-4 col-lg-3">
                              <div className="position-relative">
                                <img src={src} alt={`pasted-${i}`} className="img-fluid rounded border" />
                                <button type="button" className="btn btn-sm btn-outline-danger position-absolute" style={{top: 8, right: 8}} onClick={() => removeImage(i)}>Remove</button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="col-12 d-flex justify-content-between align-items-center mt-2">
                      <div>
                        {error && <div className="alert alert-danger py-2 px-3 mb-0">{error}</div>}
                      </div>
                      <div>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                          {submitting ? 'Submitting…' : 'Submit'}
                        </button>
                      </div>
                    </div>
                  </div>
                </form>

                {result && (
                  <div className="mt-4">
                    <h4 className="mb-3">AI help</h4>
                    {result.aiHelp ? (
                      <div className="card">
                        <div className="card-body">
                          <pre style={{whiteSpace: 'pre-wrap'}}>{result.aiHelp}</pre>
                        </div>
                      </div>
                    ) : (
                      <p className="text-muted">AI help is unavailable. {result.warnings && result.warnings.join(' ')}</p>
                    )}

                    {(result.extractedText && result.extractedText.length > 0) && (
                      <div className="mt-4">
                        <h5>OCR extracted text</h5>
                        <ul>
                          {result.extractedText.map((t, i) => (
                            <li key={i}><pre style={{whiteSpace: 'pre-wrap'}}>{t}</pre></li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
