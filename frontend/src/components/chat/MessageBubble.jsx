import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, User as UserIcon, Bookmark, ExternalLink, Briefcase, MapPin, Banknote, Clock } from 'lucide-react';

export default function MessageBubble({ message, onSaveJob, onOpenWorkspace, savedJobIds, onEditMessage }) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const [isEditing, setIsEditing] = React.useState(false);
  const [editText, setEditText] = React.useState(message.content || '');

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <div className="shrink-0 w-8 h-8 rounded-xl btn-primary flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
      )}
      <div className={`max-w-[88%] md:max-w-[78%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={
            isUser
              ? 'bg-gradient-to-br from-blue-600/30 to-purple-600/25 border border-white/10 rounded-2xl rounded-tr-sm p-4 text-sm leading-relaxed'
              : 'bg-[#0e0e15]/80 border border-purple-500/15 rounded-2xl rounded-tl-sm p-5 text-sm leading-relaxed text-slate-200'
          }
          data-testid={`message-${message.role}`}
        >
          {isAssistant && !isEditing && (
            <div className="flex justify-end -mt-4 -mr-2">
              <button
                onClick={() => { setIsEditing(true); setEditText(message.content || ''); }}
                className="text-xs text-slate-400 hover:text-white"
                title="Edit assistant message"
              >Edit</button>
            </div>
          )}

          {isEditing ? (
            <div className="space-y-2">
              <textarea value={editText} onChange={(e) => setEditText(e.target.value)} className="w-full bg-black/20 p-2 rounded text-sm text-slate-200" />
              <div className="flex gap-2">
                <button onClick={async () => {
                  if (onEditMessage) await onEditMessage(message.id, editText);
                  setIsEditing(false);
                }} className="btn-primary text-xs px-3 py-1 rounded">Save</button>
                <button onClick={() => setIsEditing(false)} className="text-xs px-3 py-1 rounded bg-white/5">Cancel</button>
              </div>
            </div>
          ) : (
            <FormattedText text={message.content} />
          )}

          {message.kind === 'job_cards' && message.payload?.jobs?.length > 0 && (
            <div className="mt-4 grid grid-cols-1 gap-3">
              {message.payload.jobs.map((job) => (
                <JobCardInline
                  key={job.id}
                  job={job}
                  onSave={() => onSaveJob(job.id)}
                  onOpen={() => onOpenWorkspace(job.id)}
                  saved={savedJobIds.has(job.id)}
                />
              ))}
            </div>
          )}

          {message.kind === 'action_plan' && Array.isArray(message.payload?.action_plan) && (
            <ActionPlan steps={message.payload.action_plan} />
          )}
        </div>
      </div>
      {isUser && (
        <div className="shrink-0 w-8 h-8 rounded-xl bg-white/10 border border-white/10 flex items-center justify-center">
          <UserIcon className="w-4 h-4 text-slate-300" />
        </div>
      )}
    </motion.div>
  );
}

function FormattedText({ text }) {
  // Minimal markdown-ish formatting: paragraphs, bullets, bold **
  if (!text) return null;
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-2.5">
      {blocks.map((block, i) => {
        const lines = block.split('\n');
        const isList = lines.every((l) => /^\s*[-*•]\s+/.test(l));
        if (isList) {
          return (
            <ul key={i} className="space-y-1.5 pl-1">
              {lines.map((l, j) => (
                <li key={j} className="flex gap-2.5">
                  <span className="text-purple-400 mt-1">•</span>
                  <span className="flex-1" dangerouslySetInnerHTML={{ __html: inlineFmt(l.replace(/^\s*[-*•]\s+/, '')) }} />
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} dangerouslySetInnerHTML={{ __html: inlineFmt(block) }} />
        );
      })}
    </div>
  );
}

function inlineFmt(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-white">$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="font-mono-data text-xs bg-white/5 px-1.5 py-0.5 rounded">$1</code>');
}

function JobCardInline({ job, onSave, onOpen, saved }) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="bg-black/40 backdrop-blur-2xl border border-blue-500/20 hover:border-purple-500/50 rounded-2xl p-4 transition-colors"
      data-testid={`job-card-${job.id}`}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-white/10 flex items-center justify-center shrink-0">
            <Briefcase className="w-4 h-4 text-purple-300" />
          </div>
          <div className="min-w-0">
            <p className="font-display font-semibold text-white truncate">{job.title}</p>
            <p className="text-xs text-slate-400 truncate">{job.company}</p>
          </div>
        </div>
        <span className="text-[10px] font-mono-data text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded-full whitespace-nowrap">{job.type}</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] text-slate-400 mb-3">
        <span className="flex items-center gap-1.5"><MapPin className="w-3 h-3" />{job.location}</span>
        {job.salary && <span className="flex items-center gap-1.5"><Banknote className="w-3 h-3" />{job.salary}</span>}
        {job.experience && <span className="flex items-center gap-1.5"><Clock className="w-3 h-3" />{job.experience}</span>}
      </div>

      {job.skills?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {job.skills.slice(0, 6).map((s) => (
            <span key={s} className="text-[10px] font-medium px-2 py-1 bg-white/5 border border-white/10 rounded-full text-slate-300">{s}</span>
          ))}
        </div>
      )}

      {job.description && (
        <p className="text-xs text-slate-400 mb-3">{job.description}</p>
      )}

      <div className="flex gap-2">
        <button
          onClick={onOpen}
          data-testid={`open-workspace-${job.id}`}
          className="flex-1 btn-primary text-white text-xs font-semibold rounded-xl py-2 flex items-center justify-center gap-1.5"
        >
          <Sparkles className="w-3.5 h-3.5" /> Open AI Workspace
        </button>
        <button
          onClick={onSave}
          data-testid={`save-job-${job.id}`}
          className={`text-xs font-medium rounded-xl px-3 py-2 border transition-colors flex items-center gap-1.5 ${
            saved
              ? 'bg-purple-500/15 border-purple-500/40 text-purple-200'
              : 'bg-white/5 border-white/10 hover:border-purple-500/40 text-slate-300'
          }`}
        >
          <Bookmark className="w-3.5 h-3.5" /> {saved ? 'Saved' : 'Save'}
        </button>
        {job.apply_url && (
          <a
            href={job.apply_url} target="_blank" rel="noreferrer"
            className="text-xs font-medium rounded-xl px-3 py-2 bg-white/5 border border-white/10 hover:border-purple-500/40 text-slate-300 flex items-center gap-1.5"
          >
            <ExternalLink className="w-3.5 h-3.5" /> Apply
          </a>
        )}
        {job.apply_urls && job.apply_urls.length > 1 && (
          <div className="flex items-center gap-2 text-[11px] text-slate-400 ml-2">
            {job.apply_urls.slice(1).map((u, i) => (
              <a key={i} href={u} target="_blank" rel="noreferrer" className="underline text-xs truncate">Link {i + 2}</a>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function ActionPlan({ steps }) {
  return (
    <ol className="mt-4 space-y-2.5">
      {steps.map((step, i) => (
        <li key={i} className="flex gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/5">
          <div className="shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-purple-500/30 flex items-center justify-center font-mono-data text-[11px] text-purple-200">
            {i + 1}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white">{step.title}</p>
            {step.detail && <p className="text-xs text-slate-400 mt-0.5">{step.detail}</p>}
            <div className="flex gap-3 mt-1.5 text-[10px] font-mono-data text-slate-500">
              {step.duration_min && <span>{step.duration_min} min</span>}
              {step.category && <span className="text-purple-400">#{step.category}</span>}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}
