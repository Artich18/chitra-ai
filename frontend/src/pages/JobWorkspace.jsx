import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Sparkles, MessageSquare, Bookmark, RefreshCw, Loader2, Briefcase, MapPin, Banknote, Clock, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';

import api from '../lib/api';
import SuccessRing from '../components/SuccessRing';

export default function JobWorkspace() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [tab, setTab] = useState('overview');

  const loadAll = async () => {
    try {
      const [jobRes, analysisRes] = await Promise.all([
        api.get(`/jobs/${jobId}`),
        api.get(`/jobs/${jobId}/analysis`),
      ]);
      setJob(jobRes.data);
      setAnalysis(analysisRes.data);
    } catch (e) {
      toast.error('Could not load job');
      navigate('/');
    } finally { setLoading(false); }
  };

  useEffect(() => { loadAll(); /* eslint-disable-next-line */ }, [jobId]);

  const refresh = async () => {
    setRefreshing(true);
    try {
      const { data } = await api.post(`/jobs/${jobId}/analysis/refresh`);
      setAnalysis(data);
      toast.success('Analysis refreshed');
    } catch { toast.error('Could not refresh'); }
    setRefreshing(false);
  };

  const toggleSave = async () => {
    if (!job) return;
    try {
      if (job.is_saved) { await api.delete(`/jobs/${jobId}/save`); setJob({ ...job, is_saved: false }); toast.success('Removed'); }
      else { await api.post(`/jobs/${jobId}/save`); setJob({ ...job, is_saved: true }); toast.success('Saved'); }
    } catch { toast.error('Failed'); }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-7 h-7 animate-spin text-purple-400" />
      </div>
    );
  }

  const prob = Number(analysis?.success_probability ?? 0);
  const ats = Number(analysis?.ats_score ?? 0);
  const match = Number(analysis?.resume_match ?? 0);

  return (
    <div className="min-h-screen px-4 md:px-10 py-8" data-testid="job-workspace">
      <div className="max-w-7xl mx-auto">
        {/* Top */}
        <div className="flex items-center justify-between mb-6">
          <button onClick={() => navigate('/')} data-testid="workspace-back" className="flex items-center gap-2 text-xs text-slate-400 hover:text-white">
            <ArrowLeft className="w-4 h-4" /> Back to chat
          </button>
          <div className="flex gap-2">
            <button onClick={refresh} disabled={refreshing} data-testid="refresh-analysis" className="text-xs font-medium px-3 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 flex items-center gap-1.5">
              {refreshing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />} Refresh
            </button>
            <button onClick={toggleSave} data-testid="workspace-save" className={`text-xs font-medium px-3 py-2 rounded-full border flex items-center gap-1.5 ${job.is_saved ? 'bg-purple-500/20 border-purple-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-300'}`}>
              <Bookmark className="w-3.5 h-3.5" /> {job.is_saved ? 'Saved' : 'Save'}
            </button>
            <button onClick={() => navigate(`/?job=${jobId}`)} data-testid="workspace-chat" className="text-xs font-semibold px-4 py-2 rounded-full btn-primary text-white flex items-center gap-1.5">
              <MessageSquare className="w-3.5 h-3.5" /> Chat about this job
            </button>
          </div>
        </div>

        {/* Hero */}
        <div className="glass-strong rounded-3xl p-6 md:p-8 mb-6 gradient-border">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-white/10 flex items-center justify-center shrink-0">
                <Briefcase className="w-6 h-6 text-purple-200" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-display font-bold mb-1">{job.title}</h1>
                <p className="text-slate-400">{job.company}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5" />{job.location}</span>
                  {job.salary && <span className="flex items-center gap-1.5"><Banknote className="w-3.5 h-3.5" />{job.salary}</span>}
                  {job.experience && <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />{job.experience}</span>}
                  <span className="text-purple-300">{job.type}</span>
                </div>
              </div>
            </div>

            {/* Success Probability */}
            <div className="flex items-center gap-5">
              <SuccessRing value={prob} size={130} />
              <div className="space-y-2">
                <Metric label="ATS Score" value={ats} accent="from-blue-500 to-cyan-400" />
                <Metric label="Resume Match" value={match} accent="from-purple-500 to-pink-400" />
              </div>
            </div>
          </div>

          {analysis?.reasoning && (
            <p className="text-sm text-slate-300 mt-5 leading-relaxed border-l-2 border-purple-500/40 pl-4">
              <Sparkles className="inline w-3.5 h-3.5 text-purple-400 mr-1" />
              {analysis.reasoning}
            </p>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-5 overflow-x-auto scrollbar-thin" data-testid="workspace-tabs">
          {[
            ['overview', 'Action Plan'],
            ['resume', 'Resume AI'],
            ['interview', 'Interview AI'],
            ['skills', 'Skill AI'],
          ].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} data-testid={`tab-${id}`}
              className={`shrink-0 text-xs font-medium px-4 py-2 rounded-full border transition-colors ${
                tab === id ? 'bg-purple-500/20 border-purple-500/40 text-white' : 'bg-white/5 border-white/10 text-slate-400 hover:text-white'
              }`}
            >{label}</button>
          ))}
        </div>

        {tab === 'overview' && <ActionPlanPanel analysis={analysis} job={job} />}
        {tab === 'resume' && <ResumePanel analysis={analysis} />}
        {tab === 'interview' && <InterviewPanel analysis={analysis} />}
        {tab === 'skills' && <SkillsPanel analysis={analysis} />}
      </div>
    </div>
  );
}

function Metric({ label, value, accent }) {
  return (
    <div className="w-40">
      <div className="flex justify-between text-[11px] mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="font-mono-data text-white">{value}%</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <motion.div initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 1 }} className={`h-full bg-gradient-to-r ${accent}`} />
      </div>
    </div>
  );
}

function Section({ title, children, count }) {
  return (
    <div className="glass rounded-2xl p-5">
      <h3 className="text-xs uppercase tracking-[0.18em] text-slate-500 mb-3 flex justify-between">
        {title}
        {count !== undefined && <span className="font-mono-data text-purple-300 normal-case">{count}</span>}
      </h3>
      {children}
    </div>
  );
}

function ActionPlanPanel({ analysis, job }) {
  const steps = analysis?.action_plan || [];
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <div className="lg:col-span-2 glass rounded-2xl p-6">
        <h2 className="text-lg font-display font-semibold mb-1">Today's Action Plan</h2>
        <p className="text-xs text-slate-500 mb-4">Tailored to land this exact role</p>
        <ol className="space-y-3">
          {steps.length === 0 && <p className="text-sm text-slate-500">No action items yet.</p>}
          {steps.map((s, i) => (
            <li key={i} className="flex gap-4 p-4 rounded-2xl bg-white/[0.03] border border-white/5">
              <div className="shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-purple-500/30 flex items-center justify-center font-mono-data text-sm text-purple-200">{i + 1}</div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-white">{s.title}</p>
                {s.detail && <p className="text-xs text-slate-400 mt-1">{s.detail}</p>}
                <div className="flex gap-3 mt-2 text-[10px] font-mono-data text-slate-500">
                  {s.duration_min && <span>{s.duration_min} min</span>}
                  {s.category && <span className="text-purple-400">#{s.category}</span>}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </div>
      <div className="space-y-5">
        <Section title="Missing Skills" count={analysis?.missing_skills?.length || 0}>
          <div className="flex flex-wrap gap-1.5">
            {(analysis?.missing_skills || []).map((s) => (
              <span key={s} className="text-[11px] px-2.5 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-200">{s}</span>
            ))}
          </div>
        </Section>
        <Section title="Job Description">
          <p className="text-xs text-slate-400 leading-relaxed">{job.description || 'No description'}</p>
          {job.skills?.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {job.skills.map((s) => (
                <span key={s} className="text-[10px] px-2 py-1 bg-white/5 border border-white/10 rounded-full text-slate-300">{s}</span>
              ))}
            </div>
          )}
        </Section>
      </div>
    </div>
  );
}

function ResumePanel({ analysis }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
      <Section title="Missing Keywords (ATS)" count={analysis?.missing_keywords?.length || 0}>
        <div className="flex flex-wrap gap-1.5">
          {(analysis?.missing_keywords || []).map((k) => (
            <span key={k} className="text-[11px] font-mono-data px-2.5 py-1 bg-amber-500/10 border border-amber-500/20 rounded-full text-amber-200">{k}</span>
          ))}
        </div>
      </Section>
      <Section title="Weak Resume Sections" count={analysis?.weak_sections?.length || 0}>
        <ul className="space-y-1.5 text-sm text-slate-300">
          {(analysis?.weak_sections || []).map((w, i) => <li key={i} className="flex gap-2"><span className="text-pink-400">→</span>{w}</li>)}
        </ul>
      </Section>
      <Section title="Concrete Improvements">
        <ul className="space-y-1.5 text-sm text-slate-300">
          {(analysis?.resume_improvements || []).map((w, i) => <li key={i} className="flex gap-2"><span className="text-purple-400">•</span>{w}</li>)}
        </ul>
      </Section>
      <Section title="Gaps to Close">
        <div className="space-y-3 text-xs">
          <GapList title="Projects" items={analysis?.project_gaps} />
          <GapList title="Certifications" items={analysis?.certification_gaps} />
          <GapList title="Portfolio" items={analysis?.portfolio_gaps} />
          <GapList title="Experience" items={analysis?.experience_gaps} />
        </div>
      </Section>
    </div>
  );
}

function GapList({ title, items }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mb-1">{title}</p>
      <ul className="space-y-1 text-slate-300">{items.map((i, idx) => <li key={idx} className="flex gap-2"><span className="text-purple-400">·</span>{i}</li>)}</ul>
    </div>
  );
}

function InterviewPanel({ analysis }) {
  const qs = analysis?.interview_questions || [];
  return (
    <div className="space-y-3">
      {qs.length === 0 && <p className="text-sm text-slate-500">No interview questions yet.</p>}
      {qs.map((q, i) => (
        <details key={i} className="glass rounded-2xl p-5 group" data-testid={`interview-q-${i}`}>
          <summary className="cursor-pointer list-none flex justify-between items-start gap-4">
            <div>
              <span className="text-[10px] uppercase tracking-[0.18em] text-purple-400">{q.category}</span>
              <p className="text-sm font-semibold text-white mt-1">{q.q}</p>
            </div>
            <span className="font-mono-data text-xs text-slate-500 shrink-0">#{i + 1}</span>
          </summary>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
              <p className="text-emerald-400 font-semibold mb-1">Strong Answer</p>
              <p className="text-slate-300 leading-relaxed">{q.strong_answer}</p>
            </div>
            <div className="p-3 rounded-xl bg-red-500/5 border border-red-500/15">
              <p className="text-red-400 font-semibold mb-1">Weak Answer</p>
              <p className="text-slate-300 leading-relaxed">{q.weak_answer}</p>
            </div>
            {q.why && <div className="p-3 rounded-xl bg-white/[0.03] border border-white/5 md:col-span-2"><p className="text-slate-400 font-semibold mb-1">Why this is asked</p><p className="text-slate-300">{q.why}</p></div>}
            {q.common_mistake && <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/15"><p className="text-amber-400 font-semibold mb-1">Common Mistake</p><p className="text-slate-300">{q.common_mistake}</p></div>}
            {q.follow_up && <div className="p-3 rounded-xl bg-purple-500/5 border border-purple-500/15"><p className="text-purple-300 font-semibold mb-1">Follow-up</p><p className="text-slate-300">{q.follow_up}</p></div>}
          </div>
        </details>
      ))}
    </div>
  );
}

function SkillsPanel({ analysis }) {
  const skills = analysis?.skill_gap || [];
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {skills.length === 0 && <p className="text-sm text-slate-500">No skills detected yet.</p>}
      {skills.map((s, i) => (
        <div key={i} className="glass rounded-2xl p-5" data-testid={`skill-${i}`}>
          <div className="flex justify-between items-start mb-3">
            <p className="text-lg font-display font-semibold">{s.skill}</p>
            <span className="text-[10px] font-mono-data text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded-full">{s.difficulty}</span>
          </div>
          <div className="flex gap-4 text-[11px] text-slate-400 mb-3">
            <span>{s.current_level} → <span className="text-white">{s.target_level}</span></span>
            <span className="font-mono-data">~{s.estimated_hours}h</span>
          </div>
          {s.learning_path?.length > 0 && (
            <ol className="text-xs text-slate-300 space-y-1 mb-3">
              {s.learning_path.map((p, j) => <li key={j} className="flex gap-2"><span className="text-purple-400 font-mono-data">{j + 1}.</span>{p}</li>)}
            </ol>
          )}
          {s.resources?.length > 0 && (
            <div className="space-y-1.5 pt-3 border-t border-white/5">
              {s.resources.map((r, j) => (
                <a key={j} href={r.url || '#'} target="_blank" rel="noreferrer" className="flex items-center justify-between text-xs text-slate-300 hover:text-white p-2 rounded-lg bg-white/[0.03] border border-white/5 hover:border-purple-500/30">
                  <span><span className="text-purple-400 mr-2">{r.type}</span>{r.name}</span>
                  <ExternalLink className="w-3 h-3 text-slate-500" />
                </a>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
