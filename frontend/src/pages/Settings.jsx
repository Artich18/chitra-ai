import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [settings, setSettings] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/settings').then(({ data }) => setSettings(data)).catch(() => {});
  }, []);

  if (!settings) {
    return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-7 h-7 animate-spin text-purple-400" /></div>;
  }

  const save = async (patch) => {
    setSaving(true);
    try {
      const { data } = await api.patch('/settings', patch);
      setSettings(data);
      toast.success('Saved');
    } catch { toast.error('Failed'); }
    setSaving(false);
  };

  return (
    <div className="min-h-screen px-4 md:px-10 py-8" data-testid="settings-page">
      <div className="max-w-3xl mx-auto">
        <button onClick={() => navigate('/')} data-testid="settings-back" className="flex items-center gap-2 text-xs text-slate-400 hover:text-white mb-6">
          <ArrowLeft className="w-4 h-4" /> Back to chat
        </button>

        <h1 className="text-3xl font-display font-bold mb-1">Settings</h1>
        <p className="text-sm text-slate-400 mb-8">Tune how Chitra works for you.</p>

        <div className="glass-strong rounded-3xl p-6 md:p-8 space-y-7">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500 mb-2">Account</p>
            <div className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/5">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500/40 to-purple-500/40 border border-white/10 flex items-center justify-center font-semibold uppercase">
                {user?.picture ? <img src={user.picture} alt="" className="w-full h-full rounded-full object-cover" /> : (user?.name?.[0] || 'U')}
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold">{user?.name}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>
              <span className="text-[10px] uppercase tracking-[0.18em] text-purple-300 bg-purple-500/10 border border-purple-500/20 px-2 py-1 rounded-full">{user?.auth_provider}</span>
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500 mb-2">AI Provider</p>
            <p className="text-xs text-slate-500 mb-3">Chitra automatically falls back to OpenAI if Gemini fails. You can pin a provider here.</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { id: 'auto', label: 'Auto', detail: 'Smart routing' },
                { id: 'gemini', label: 'Gemini 2.5', detail: 'Fast & analytical' },
                { id: 'openai', label: 'GPT-5.5', detail: 'Writing & persona' },
              ].map((p) => (
                <button
                  key={p.id} onClick={() => save({ preferred_provider: p.id })} disabled={saving}
                  data-testid={`provider-${p.id}`}
                  className={`p-3 rounded-xl text-left border transition-colors ${
                    settings.preferred_provider === p.id ? 'bg-purple-500/15 border-purple-500/40' : 'bg-white/[0.03] border-white/5 hover:border-purple-500/30'
                  }`}
                >
                  <p className="text-sm font-semibold">{p.label}</p>
                  <p className="text-[10px] text-slate-500">{p.detail}</p>
                </button>
              ))}
            </div>
          </div>

          <div className="pt-6 border-t border-white/5 flex items-center justify-between">
            <p className="text-xs text-slate-500">Sign out from this device</p>
            <button onClick={async () => { await logout(); navigate('/login'); }} data-testid="settings-logout" className="text-xs font-medium px-4 py-2 rounded-full bg-red-500/10 border border-red-500/20 text-red-300 hover:bg-red-500/20">Sign out</button>
          </div>
        </div>
      </div>
    </div>
  );
}
