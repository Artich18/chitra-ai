import { motion } from 'framer-motion';

export default function SuccessRing({ value = 0, size = 120 }) {
  const v = Math.max(0, Math.min(100, value));
  const r = (size - 14) / 2;
  const c = 2 * Math.PI * r;
  const stroke = c - (v / 100) * c;
  const id = `ring-grad-${size}`;
  return (
    <div className="relative" style={{ width: size, height: size }} data-testid="success-ring">
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#2563eb" />
            <stop offset="50%" stopColor="#7c3aed" />
            <stop offset="100%" stopColor="#c026d3" />
          </linearGradient>
        </defs>
        <circle cx={size / 2} cy={size / 2} r={r} stroke="rgba(255,255,255,0.06)" strokeWidth="8" fill="none" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r}
          stroke={`url(#${id})`} strokeWidth="8" fill="none" strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: stroke }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono-data text-3xl font-semibold gradient-text">{v}%</span>
        <span className="text-[10px] uppercase tracking-[0.18em] text-slate-500 mt-0.5">Success</span>
      </div>
    </div>
  );
}
