'use client';
import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import InvestigationResult from '../../components/InvestigationResult';
import ReportModal from '../../components/ReportModal';

export default function InvestigationPage() {
  const [demoEmails, setDemoEmails] = useState([]);
  const [mode, setMode] = useState('demo');
  const [selectedDemo, setSelectedDemo] = useState('demo1');
  const [pastedText, setPastedText] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    api.listDemoEmails().then(setDemoEmails).catch(() => {});
  }, []);

  async function runAnalysis() {
    setError('');
    setLoading(true);
    try {
      let res;
      if (mode === 'demo') {
        res = await api.analyzeDemo(selectedDemo);
      } else if (mode === 'paste') {
        if (!pastedText.trim()) throw new Error('Paste an email first.');
        res = await api.analyzeRaw(pastedText, 'pasted-email.eml');
      } else {
        if (!selectedFile) throw new Error('Choose a .eml file first.');
        res = await api.analyzeUpload(selectedFile);
      }
      setResult(res);
    } catch (e) {
      setError(e.message || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="glass-panel">
        <div className="panel-head">
          <h2>&#128231; Email Investigation</h2>
          <span className="sub">select a demo, upload a .eml, or paste raw content</span>
        </div>

        <div className="tab-row">
          {['demo', 'upload', 'paste'].map((m) => (
            <button key={m} className={`tab-btn ${mode === m ? 'active' : ''}`} onClick={() => setMode(m)}>
              {m === 'demo' ? 'Demo Email' : m === 'upload' ? 'Upload .eml' : 'Paste Content'}
            </button>
          ))}
        </div>

        {mode === 'demo' && (
          <div className="demo-grid">
            {demoEmails.map((d) => (
              <div
                key={d.demo_id}
                className={`demo-card ${selectedDemo === d.demo_id ? 'selected' : ''}`}
                onClick={() => setSelectedDemo(d.demo_id)}
              >
                <div className="dname">{d.label}</div>
                <div className="dfile">{d.filename}</div>
              </div>
            ))}
          </div>
        )}

        {mode === 'upload' && (
          <label style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, border: '1px dashed var(--border)', borderRadius: 10, padding: 30, cursor: 'pointer' }}>
            <span style={{ fontSize: 12.5, color: 'var(--text-dim)' }}>
              {selectedFile ? selectedFile.name : 'Click to choose a .eml file'}
            </span>
            <input type="file" accept=".eml,text/plain" style={{ display: 'none' }} onChange={(e) => setSelectedFile(e.target.files[0])} />
          </label>
        )}

        {mode === 'paste' && (
          <textarea rows={8} value={pastedText} onChange={(e) => setPastedText(e.target.value)} placeholder="Paste raw email headers and/or content here..." />
        )}

        <button className="btn primary full" style={{ marginTop: 14 }} onClick={runAnalysis} disabled={loading}>
          {loading ? 'Running analysis pipeline\u2026' : '\u{1F50D} Analyze Email'}
        </button>
        {error && <div className="status-line err">{error}</div>}
      </div>

      {result && <InvestigationResult result={result} onOpenReport={() => setShowReport(true)} />}
      {showReport && <ReportModal result={result} onClose={() => setShowReport(false)} />}
    </>
  );
}
