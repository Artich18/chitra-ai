import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../lib/api';
import { Sparkles, Plus, MessageSquare, Bookmark, FileText, LogOut, Settings as SettingsIcon, ArrowUpRight, X } from 'lucide-react';

export default function Sidebar({
  sessions, activeSessionId, onSelectSession, onNewChat,
  savedJobs, user, onLogout, onOpenJob, resume, onOpenResume,
  mobileOpen = false, onCloseMobile,
}) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    let mounted = true;
    api.get('/jobs/history').then(({ data }) => { if (mounted) setHistory(data || []); }).catch(() => {});
    return () => { mounted = false; };
  }, []);

  const deleteHistory = async (id) => {
    try {
      if (id) {
        await api.delete(`/jobs/history/${id}`);
      } else {
        await api.delete('/jobs/history');
      }
      const { data } = await api.get('/jobs/history');
      setHistory(data || []);
    } catch (e) {
      // ignore
    }
  };
  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/60 backdrop-blur-sm"
          onClick={onCloseMobile}
          data-testid="sidebar-backdrop"
        />
      )}
      <aside
        className={`${mobileOpen ? 'flex' : 'hidden'} md:flex fixed md:relative inset-y-0 left-0 z-40 w-[280px] flex-col border-r border-white/5 bg-black/90 md:bg-black/30 backdrop-blur-2xl overflow-y-auto scrollbar-thin`}
        data-testid="sidebar"
      >
        {/* Mobile close button */}
        <button
          type="button"
          onClick={onCloseMobile}
          data-testid="sidebar-close-mobile"
          className="md:hidden absolute top-3 right-3 p-2 rounded-lg hover:bg-white/5 z-10"
        >
          <X className="w-4 h-4 text-slate-400" />
        </button>
      {/* Brand */}
      <div className="p-5 flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-xl btn-primary flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-base font-display font-bold">Chitra</p>
          <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 -mt-0.5">AI Career OS</p>
        </div>
      </div>

        {/* Recent job searches */}
        <div className="px-4 mt-4">
          <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2 flex items-center justify-between">
            Recent searches
            <button onClick={() => deleteHistory(null)} className="text-[10px] text-red-400">Clear</button>
          </p>
          <div className="space-y-1 max-h-[18vh] overflow-y-auto scrollbar-thin">
            {history.length === 0 && (
              <p className="text-xs text-slate-600 italic px-2 py-1.5">No recent searches</p>
            )}
            {history.map((h) => (
              <div key={h.id} className="w-full text-left text-xs px-3 py-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] border border-transparent flex items-center justify-between">
                <div className="min-w-0 pr-2">
                  <p className="truncate text-slate-200">{h.query}</p>
                  <p className="text-[10px] text-slate-500">{h.results_count} results</p>
                </div>
                <div className="flex-shrink-0">
                  <button onClick={() => deleteHistory(h.id)} className="text-[11px] text-red-400">Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>

      {/* New Chat */}
      <div className="px-4">
        <button
          onClick={onNewChat}
          data-testid="new-chat-btn"
          className="w-full btn-primary rounded-xl py-2.5 text-sm font-semibold text-white flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" /> New conversation
        </button>
      </div>

      {/* Recent chats */}
      <div className="px-4 mt-6">
        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2">Recent</p>
        <div className="space-y-1 max-h-[28vh] overflow-y-auto scrollbar-thin">
          {sessions.length === 0 && (
            <p className="text-xs text-slate-600 italic px-2 py-1.5">No chats yet</p>
          )}
          {sessions.map((s) => (
            <button
              key={s.id}
              data-testid={`session-${s.id}`}
              onClick={() => onSelectSession(s.id)}
              className={`w-full text-left text-sm px-3 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                s.id === activeSessionId
                  ? 'bg-purple-500/15 text-white border border-purple-500/30'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white border border-transparent'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-70" />
              <span className="truncate">{s.title || 'Untitled'}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Saved jobs */}
      <div className="px-4 mt-6 flex-1 min-h-0 flex flex-col">
        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-2 flex items-center justify-between">
          Saved jobs
          <span className="font-mono-data text-purple-400 normal-case tracking-normal">{savedJobs.length}</span>
        </p>
        <div className="space-y-1.5 overflow-y-auto scrollbar-thin">
          {savedJobs.length === 0 && (
            <p className="text-xs text-slate-600 italic px-2 py-1.5">Save jobs from chat to track them here.</p>
          )}
          {savedJobs.slice(0, 8).map((j) => (
            <button
              key={j.id}
              onClick={() => onOpenJob(j.id)}
              data-testid={`sidebar-job-${j.id}`}
              className="w-full text-left text-xs px-3 py-2.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.07] border border-white/5 hover:border-purple-500/30 transition-all group"
            >
              <p className="font-semibold text-slate-200 truncate group-hover:text-white">{j.title}</p>
              <p className="text-slate-500 truncate">{j.company} · {j.location}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Resume status */}
      <button
        onClick={onOpenResume}
        data-testid="sidebar-resume-btn"
        className="mx-4 mt-4 mb-2 p-3 rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-purple-500/20 text-left hover:border-purple-500/40 transition-colors flex items-center gap-3"
      >
        <FileText className="w-4 h-4 text-purple-400 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold">{resume ? 'Resume ready' : 'Upload resume'}</p>
          <p className="text-[10px] text-slate-500 truncate">{resume ? (resume.filename || 'Pasted text') : 'Unlock ATS & interview AI'}</p>
        </div>
        <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
      </button>

      {/* User */}
      <div className="p-4 border-t border-white/5 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500/40 to-purple-500/40 border border-white/10 flex items-center justify-center text-sm font-semibold uppercase">
          {user?.picture ? <img src={user.picture} alt="" className="w-full h-full rounded-full object-cover" /> : (user?.name?.[0] || 'U')}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold truncate">{user?.name}</p>
          <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
        </div>
        <Link to="/settings" data-testid="settings-link" className="p-1.5 rounded-lg hover:bg-white/5">
          <SettingsIcon className="w-4 h-4 text-slate-400" />
        </Link>
        <button onClick={onLogout} data-testid="logout-btn" className="p-1.5 rounded-lg hover:bg-white/5">
          <LogOut className="w-4 h-4 text-slate-400" />
        </button>
      </div>
    </aside>
    </>
  );
}
