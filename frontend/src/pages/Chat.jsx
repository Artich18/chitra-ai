import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Sparkles, Loader2, FileText, Plus, MessageSquare, Bookmark, ArrowRight, Menu } from 'lucide-react';
import { toast } from 'sonner';

import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/chat/Sidebar';
import MessageBubble from '../components/chat/MessageBubble';
import QuickActions from '../components/chat/QuickActions';
import ResumeUpload from '../components/chat/ResumeUpload';

export default function Chat() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const jobIdContext = searchParams.get('job');

  const [sessions, setSessions] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [savedJobs, setSavedJobs] = useState([]);
  const [resume, setResume] = useState(null);
  const [showResume, setShowResume] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const scrollerRef = useRef(null);

  useEffect(() => {
    api.get('/chat/sessions').then(({ data }) => setSessions(data || []));
    api.get('/jobs/saved').then(({ data }) => setSavedJobs(data || []));
    api.get('/resume/active').then(({ data }) => setResume(data?.id ? data : null)).catch(() => {});
  }, []);

  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const loadSession = useCallback(async (id) => {
    setSessionId(id);
    setMobileMenuOpen(false);
    const { data } = await api.get(`/chat/sessions/${id}/messages`);
    setMessages(data.messages || []);
  }, []);

  const newChat = () => {
    setSessionId(null);
    setMessages([]);
    setMobileMenuOpen(false);
  };

  const send = async (overrideContent, quickAction) => {
    const content = (overrideContent ?? input).trim();
    if (!content || sending) return;
    setInput('');
    setSending(true);

    const optimistic = {
      id: 'tmp-' + Date.now(),
      role: 'user',
      content,
      kind: 'text',
      created_at: new Date().toISOString(),
    };
    setMessages((m) => [...m, optimistic]);

    try {
      const { data } = await api.post('/chat/send', {
        session_id: sessionId,
        content,
        quick_action: quickAction || null,
        job_id: jobIdContext || null,
      });
      setSessionId(data.session_id);
      setMessages((m) => [
        ...m.filter((x) => x.id !== optimistic.id),
        data.user_message,
        data.assistant_message,
      ]);
      // refresh sessions
      api.get('/chat/sessions').then(({ data }) => setSessions(data || []));
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to send message');
      setMessages((m) => m.filter((x) => x.id !== optimistic.id));
    } finally {
      setSending(false);
    }
  };

  const editMessage = async (messageId, newContent) => {
    try {
      const { data } = await api.patch(`/chat/messages/${messageId}`, { content: newContent });
      setMessages((m) => m.map((msg) => (msg.id === messageId ? data : msg)));
      toast.success('Message updated');
    } catch (e) {
      toast.error('Could not update message');
    }
  };

  const handleSaveJob = async (jobId) => {
    try {
      await api.post(`/jobs/${jobId}/save`);
      toast.success('Job saved');
      const { data } = await api.get('/jobs/saved');
      setSavedJobs(data || []);
    } catch (e) {
      toast.error('Could not save');
    }
  };

  const handleOpenWorkspace = (jobId) => navigate(`/jobs/${jobId}`);

  return (
    <div className="min-h-screen flex" data-testid="chat-page">
      <Sidebar
        sessions={sessions}
        activeSessionId={sessionId}
        onSelectSession={loadSession}
        onNewChat={newChat}
        savedJobs={savedJobs}
        user={user}
        onLogout={logout}
        onOpenJob={(id) => { setMobileMenuOpen(false); navigate(`/jobs/${id}`); }}
        resume={resume}
        onOpenResume={() => { setMobileMenuOpen(false); setShowResume(true); }}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      <main className="flex-1 flex flex-col h-screen md:h-auto md:min-h-screen min-w-0">
        {/* Header */}
        <header className="px-6 md:px-10 pt-8 pb-4 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            data-testid="mobile-menu-btn"
            className="md:hidden shrink-0 w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center"
            aria-label="Open menu"
          >
            <Menu className="w-4 h-4 text-slate-300" />
          </button>
          <div className="min-w-0 flex-1">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500 mb-1">
              {new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}
            </p>
            <h1 className="text-3xl md:text-4xl font-display font-semibold" data-testid="welcome-header">
              Hey {user?.name?.split(' ')[0] || 'there'}, <span className="gradient-text">what's the move today?</span>
            </h1>
          </div>
          <button
            onClick={() => setShowResume(true)}
            data-testid="header-resume-btn"
            className="hidden md:flex items-center gap-2 text-xs font-medium px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-purple-400" />
            {resume ? 'Resume on file' : 'Upload resume'}
          </button>
        </header>

        {/* Chat surface */}
        <section className="flex-1 min-h-0 px-2 md:px-10 pb-20 md:pb-6 flex flex-col">
          <div className="flex-1 glass-strong rounded-3xl flex flex-col overflow-hidden min-w-0" data-testid="chat-card">
            {/* Messages */}
            <div
              ref={scrollerRef}
              className="flex-1 overflow-y-auto scrollbar-thin px-3 md:px-8 py-6 space-y-5"
              data-testid="chat-messages"
            >
              {messages.length === 0 && !sending && (
                <EmptyState />
              )}
              <AnimatePresence initial={false}>
                {messages.map((m) => (
                  <MessageBubble
                    key={m.id}
                    message={m}
                    onSaveJob={handleSaveJob}
                    onOpenWorkspace={handleOpenWorkspace}
                    savedJobIds={new Set(savedJobs.map((j) => j.id))}
                    onEditMessage={editMessage}
                  />
                ))}
              </AnimatePresence>
              {sending && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3 text-sm text-slate-400">
                  <div className="w-7 h-7 rounded-xl btn-primary flex items-center justify-center pulse-glow">
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                  </div>
                  <span className="font-mono-data text-xs">Chitra is thinking</span>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
                </motion.div>
              )}
            </div>

            {/* Quick actions */}
            {messages.length === 0 && (
              <div className="px-5 md:px-8 pb-3">
                <QuickActions onSelect={(action, prompt) => send(prompt, action)} />
              </div>
            )}

            {/* Input */}
            <form
              onSubmit={(e) => { e.preventDefault(); send(); }}
              className="border-t border-white/5 p-4 md:p-5 flex items-end gap-3"
            >
              <button
                type="button"
                onClick={() => setShowResume(true)}
                data-testid="attach-resume-btn"
                className="shrink-0 w-12 h-12 md:w-11 md:h-11 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center transition-colors"
                title="Upload resume"
              >
                <FileText className="w-4 h-4 text-purple-400" />
              </button>
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder='Ask Chitra anything — "Find React jobs in Bangalore"'
                  data-testid="chat-input"
                  className="w-full bg-white/5 border border-white/10 rounded-2xl pl-5 pr-14 md:pr-12 py-4 md:py-3.5 text-base md:text-sm placeholder:text-slate-500 focus:outline-none focus:border-purple-500/50 transition-colors"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || sending}
                  data-testid="chat-send-btn"
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 w-10 h-10 md:w-9 md:h-9 rounded-xl btn-primary flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4 text-white" />
                </button>
              </div>
            </form>
          </div>
        </section>
      </main>

      {showResume && (
        <ResumeUpload
          current={resume}
          onClose={() => setShowResume(false)}
          onSaved={(r) => { setResume(r); setShowResume(false); toast.success('Resume saved'); }}
        />
      )}
    </div>
  );
}

function EmptyState() {
  const starters = [
    { label: 'Find Frontend Developer jobs in Bangalore', emoji: '🎯' },
    { label: 'Analyze my resume', emoji: '📄' },
    { label: 'Prepare me for a TCS interview', emoji: '💼' },
    { label: 'Generate my 6-month career roadmap', emoji: '🚀' },
  ];
  return (
    <div className="h-full flex flex-col items-center justify-center text-center py-10">
      <div className="w-14 h-14 rounded-2xl btn-primary flex items-center justify-center mb-5 pulse-glow">
        <Sparkles className="w-7 h-7 text-white" />
      </div>
      <h3 className="text-xl font-display font-semibold mb-1.5">Chat is where everything happens.</h3>
      <p className="text-sm text-slate-400 max-w-md">
        Ask for jobs, resume help, ATS fixes, interview prep — Chitra handles it all without leaving this conversation.
      </p>
      <div className="mt-6 w-full max-w-full grid grid-cols-1 gap-3 sm:grid-cols-2 sm:max-w-3xl">
        {starters.map((s) => (
          <button
            key={s.label}
            data-testid={`starter-${s.label.slice(0, 18).replace(/\s+/g, '-').toLowerCase()}`}
            className="w-full min-h-[4.5rem] text-left text-sm px-4 py-4 rounded-2xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/5 hover:border-purple-500/30 transition-all flex flex-col justify-between gap-3 group break-words"
            onClick={() => {
              const input = document.querySelector('[data-testid="chat-input"]');
              if (input) { input.value = s.label; input.focus(); }
              const form = input?.closest('form');
              // dispatch input event for controlled component
              const ev = new Event('input', { bubbles: true });
              input?.dispatchEvent(ev);
            }}
          >
            <span className="flex items-start gap-3 text-slate-300 group-hover:text-white">
              <span className="text-lg">{s.emoji}</span>
              <span className="leading-snug">{s.label}</span>
            </span>
            <ArrowRight className="w-4 h-4 text-slate-600 self-end group-hover:text-purple-400 transition-colors" />
          </button>
        ))}
      </div>
    </div>
  );
}
