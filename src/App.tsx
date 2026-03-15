import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, Battery, Trash2 } from 'lucide-react';
import { parseBatteryReport } from './core/parser';
import type { BatteryReportData } from './core/types';
import Dashboard from './components/Dashboard';

function App() {
  const [reportData, setReportData] = useState<BatteryReportData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    const file = acceptedFiles[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const text = reader.result as string;
        const parsed = parseBatteryReport(text);
        if (parsed.health_data.length === 0 && parsed.usage_data.length === 0) {
          throw new Error("Could not find valid Battery Data. Are you sure this is a Windows battery-report.html file?");
        }
        setReportData(parsed);
      } catch (err: any) {
        setError(err.message || "Failed to parse file.");
      }
    };
    reader.onerror = () => setError("Error reading file.");
    reader.readAsText(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/html': ['.html']
    },
    multiple: false
  });

  return (
    <div className="app-container">
      <header>
        <div className="title-section">
          <h1>Battery Report Analyzer</h1>
          <p>Gain deep insights into your device's battery health, usage, and degradation entirely safely within your browser.</p>
        </div>
        {reportData && (
          <button className="btn btn-secondary" onClick={() => setReportData(null)}>
            <Trash2 size={18} /> Clear Data
          </button>
        )}
      </header>

      {error && (
        <div style={{ background: 'var(--danger)', color: 'white', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
          <strong>Error: </strong> {error}
        </div>
      )}

      {!reportData ? (
        <div 
          {...getRootProps()} 
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <UploadCloud className="upload-icon" />
          <h2>Drop your <code>battery-report.html</code> here</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', marginBottom: '1.5rem' }}>
            Or click to browse files. The file stays local and is never uploaded.
          </p>
          <button className="btn">
            <Battery size={20} /> Select Report
          </button>
        </div>
      ) : (
        <Dashboard data={reportData} />
      )}
    </div>
  );
}

export default App;
