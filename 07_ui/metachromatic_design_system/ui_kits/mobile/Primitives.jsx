// MetaChromatic — primitive atoms
// GlassPanel · GlassCard · Button · Input · Label · Pill · ProgressBar · Skeleton
const { useState } = React;

function GlassPanel({ children, style, className, onClick }) {
  return (
    <div
      onClick={onClick}
      className={className}
      style={{
        background: 'rgba(10,14,26,0.65)',
        backdropFilter: 'blur(16px) saturate(180%)',
        WebkitBackdropFilter: 'blur(16px) saturate(180%)',
        border: `1px solid ${MC.glassBorder}`,
        borderRadius: MC.radius,
        boxShadow: MC.shadow,
        padding: 16,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function GlassCard({ children, style, onClick, active }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: active ? 'rgba(255,255,255,0.09)' : MC.glassBg,
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: `1px solid ${hover || active ? MC.glassBorderHover : MC.glassBorder}`,
        borderRadius: MC.radius,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 150ms ease',
        overflow: 'hidden',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function Button({ children, variant = 'primary', disabled, onClick, style, size = 'md' }) {
  const [press, setPress] = useState(false);
  const base = {
    border: 'none',
    fontFamily: "'Prompt', sans-serif",
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    transition: 'all 150ms ease',
    transform: press && !disabled ? 'scale(0.98)' : 'scale(1)',
    opacity: disabled ? 0.32 : 1,
  };
  const sizes = {
    sm: { height: 32, padding: '0 12px', borderRadius: 8, fontSize: 12 },
    md: { height: 44, padding: '0 18px', borderRadius: 12, fontSize: 14 },
    lg: { height: 56, padding: '0 24px', borderRadius: MC.radius, fontSize: 16 },
  };
  const variants = {
    primary: {
      background: MC.gradientPrimary,
      border: '1px solid rgba(6,182,212,0.45)',
      color: '#fff',
      boxShadow: disabled ? 'none' : `${MC.glowCyan}, inset 0 1px 0 rgba(255,255,255,0.15)`,
    },
    secondary: { background: 'rgba(255,255,255,0.06)', border: `1px solid ${MC.glassBorder}`, color: MC.fg2 },
    ghost: { background: 'transparent', border: `1px solid ${MC.glassBorder}`, color: MC.fg2 },
  };
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      onMouseDown={() => setPress(true)}
      onMouseUp={() => setPress(false)}
      onMouseLeave={() => setPress(false)}
      style={{ ...base, ...sizes[size], ...variants[variant], ...style }}
    >
      {children}
    </button>
  );
}

function Input({ value, onChange, placeholder, type = 'text', style, rows }) {
  const [focus, setFocus] = useState(false);
  const base = {
    background: 'rgba(255,255,255,0.05)',
    border: `1px solid ${focus ? 'rgba(6,182,212,0.55)' : 'rgba(255,255,255,0.1)'}`,
    color: MC.fg1,
    backdropFilter: 'blur(8px)',
    WebkitBackdropFilter: 'blur(8px)',
    outline: 'none',
    borderRadius: 12,
    padding: '10px 14px',
    fontSize: 14,
    fontFamily: "'Prompt', sans-serif",
    width: '100%',
    boxSizing: 'border-box',
    transition: 'all 150ms ease',
    boxShadow: focus ? '0 0 0 2px rgba(6,182,212,0.12), inset 0 0 12px rgba(6,182,212,0.04)' : 'none',
    resize: rows ? 'none' : undefined,
    ...style,
  };
  if (rows) {
    return (
      <textarea
        value={value} onChange={e => onChange?.(e.target.value)}
        placeholder={placeholder} rows={rows}
        onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        style={base}
      />
    );
  }
  return (
    <input
      type={type} value={value} onChange={e => onChange?.(e.target.value)}
      placeholder={placeholder}
      onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
      style={base}
    />
  );
}

function Label({ children, style }) {
  return (
    <span style={{
      fontSize: 11, fontWeight: 500, textTransform: 'uppercase',
      letterSpacing: '.08em', color: MC.fg3, padding: '0 4px',
      fontFamily: "'Prompt', sans-serif", ...style,
    }}>{children}</span>
  );
}

function Pill({ children, color = 'white' }) {
  const colors = {
    white: { bg: 'rgba(255,255,255,0.1)', fg: MC.fg2 },
    cyan: { bg: 'rgba(6,182,212,0.2)', fg: MC.cyanLight },
    purple: { bg: 'rgba(124,58,237,0.15)', fg: '#a78bfa' },
    emerald: { bg: 'rgba(34,197,94,0.15)', fg: '#4ade80' },
    rose: { bg: 'rgba(225,29,72,0.15)', fg: '#fb7185' },
    yellow: { bg: 'rgba(234,179,8,0.15)', fg: '#facc15' },
  };
  const c = colors[color];
  return (
    <span style={{
      fontSize: 11, padding: '4px 10px', borderRadius: 6, fontWeight: 500,
      background: c.bg, color: c.fg, display: 'inline-block',
    }}>{children}</span>
  );
}

function ProgressBar({ value }) {
  return (
    <div style={{ height: 6, borderRadius: 9999, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
      <div style={{
        height: '100%', width: `${value}%`, borderRadius: 9999,
        background: 'linear-gradient(90deg,#06b6d4,#0ea5e9)',
        boxShadow: '0 0 8px rgba(6,182,212,0.5)',
        transition: 'width 250ms ease',
      }} />
    </div>
  );
}

function Skeleton({ width = '100%', height = 14, style }) {
  return (
    <div style={{
      width, height, borderRadius: 6,
      background: 'linear-gradient(90deg,rgba(255,255,255,.04) 25%,rgba(255,255,255,.08) 50%,rgba(255,255,255,.04) 75%)',
      backgroundSize: '200% 100%',
      animation: 'mcShim 1.6s ease infinite',
      ...style,
    }} />
  );
}

Object.assign(window, { GlassPanel, GlassCard, Button, Input, Label, Pill, ProgressBar, Skeleton });
