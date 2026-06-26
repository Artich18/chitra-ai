import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { X, Upload, FileText, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '../../lib/api';

export default function ResumeUpload({ current, onClose, onSaved }) {
  const [mode, setMode] = useState('upload');
  const [pasted, setPasted] = useState('');
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    const ok = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
      || /\.(pdf|docx)$/i.test(file.name);
    if (!ok) {
      toast.error('Please upload a PDF or DOCX file');
      return;
    }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const { data } = await api.post('/resume/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onSaved(data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Upload failed');
    } finally {
      setBusy(false);
    }
  };

  const handlePaste = async () => {
    if (pasted.trim().length < 30) { toast.error('Paste at least a few lines'); return; }
    setBusy(true);
    try {
      const { data } = await api.post('/resume/paste', { content_text: pasted });
      onSaved(data);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" data-testid="resume-modal">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-2xl glass-strong rounded-3xl p-6 md:p-8 relative"
      >
        <button onClick={onClose} data-testid="resume-close" className="absolute top-4 right-4 p-2 rounded-lg hover:bg-white/5">
          <X className="w-4 h-4 text-slate-400" />
        </button>

        <h3 className="text-xl font-display font-semibold mb-1">
          {current ? 'Update your resume' : 'Upload your resume'}
        </h3>
        <p className="text-sm text-slate-400 mb-5">
          Chitra reads your resume to personalise every answer, ATS score and interview prep.
        </p>

        <div className="flex gap-2 mb-5">
          <button
            onClick={() => setMode('upload')} data-testid="resume-mode-upload"
            className={`text-xs font-medium px-3.5 py-1.5 rounded-full border transition-colors ${
              mode === 'upload' ? 'bg-purple-500/20 border-purple-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-400'
            }`}
          >Upload PDF / DOCX</button>
          <button
            onClick={() => setMode('paste')} data-testid="resume-mode-paste"
            className={`text-xs font-medium px-3.5 py-1.5 rounded-full border transition-colors ${
              mode === 'paste' ? 'bg-purple-500/20 border-purple-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-400'
            }`}
          >Paste text</button>
        </div>

        {mode === 'upload' ? (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files?.[0]); }}
            onClick={() => fileRef.current?.click()}
            data-testid="resume-dropzone"
            className={`rounded-2xl border-2 border-dashed transition-colors cursor-pointer p-10 text-center ${
              dragOver ? 'border-purple-500/60 bg-purple-500/5' : 'border-white/10 hover:border-purple-500/40'
            }`}
          >
            <input
              ref={fileRef} type="file" accept=".pdf,.docx" hidden
              data-testid="resume-file-input"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
            <div className="w-12 h-12 mx-auto rounded-2xl btn-primary flex items-center justify-center mb-3">
              {busy ? <Loader2 className="w-5 h-5 text-white animate-spin" /> : <Upload className="w-5 h-5 text-white" />}
            </div>
            <p className="text-sm font-semibold text-white">{busy ? 'Parsing your resume…' : 'Drop your resume here or click to browse'}</p>
            <p className="text-xs text-slate-500 mt-1">PDF or DOCX · Max 10MB</p>
          </div>
        ) : (
          <div>
            <textarea
              value={pasted}
              onChange={(e) => setPasted(e.target.value)}
              placeholder="Paste your resume text here..."
              data-testid="resume-paste-textarea"
              className="w-full h-56 bg-white/5 border border-white/10 rounded-2xl p-4 text-sm placeholder:text-slate-500 focus:outline-none focus:border-purple-500/50 resize-none font-mono-data"
            />
            <button
              onClick={handlePaste} disabled={busy}
              data-testid="resume-paste-save"
              className="mt-3 btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold text-white flex items-center gap-2 disabled:opacity-60"
            >
              {busy && <Loader2 className="w-4 h-4 animate-spin" />} Save resume
            </button>
          </div>
        )}

        {current && (
          <div className="mt-5 flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/5">
            <FileText className="w-4 h-4 text-purple-400" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{current.filename || 'Pasted resume'}</p>
              <p className="text-[10px] text-slate-500">Active · {(current.content_text || '').length} chars</p>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
