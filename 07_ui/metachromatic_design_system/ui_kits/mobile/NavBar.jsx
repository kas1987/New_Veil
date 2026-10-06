// Bottom tab bar — 7 slots, cyan active state with underline, status dot.
function NavBar({ current, onChange, comfyOk = true }) {
  const tabs = [
    { id: 'models', label: 'Models', icon: '⊞' },
    { id: 'outputs', label: 'Outputs', icon: '▤' },
    { id: 'generate', label: 'Generate', icon: '✦' },
    { id: 'tag', label: 'Tag', icon: '◆' },
    { id: 'review', label: 'Review', icon: '✓' },
    { id: 'export', label: 'Export', icon: '↥' },
    { id: 'audio', label: 'Audio', icon: '♫' },
  ];
  return (
    <nav style={{
      position: 'absolute', bottom: 0, left: 0, right: 0,
      height: 64, background: 'rgba(5,8,18,0.82)',
      backdropFilter: 'blur(28px) saturate(200%)',
      WebkitBackdropFilter: 'blur(28px) saturate(200%)',
      borderTop: '1px solid rgba(255,255,255,0.06)',
      display: 'flex', zIndex: 50,
    }}>
      <span style={{
        position: 'absolute', top: 10, right: 14,
        width: 6, height: 6, borderRadius: 9999,
        background: comfyOk ? '#4ade80' : '#ef4444',
        boxShadow: comfyOk ? '0 0 6px rgba(52,211,153,.7)' : '0 0 6px rgba(239,68,68,.7)',
      }} />
      {tabs.map(t => {
        const active = current === t.id;
        return (
          <button key={t.id} onClick={() => onChange?.(t.id)} style={{
            flex: 1, background: 'none', border: 'none', cursor: 'pointer',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', gap: 2, position: 'relative',
            color: active ? MC.cyanLight : 'rgba(255,255,255,0.35)',
            textShadow: active ? MC.textGlow : 'none',
            fontFamily: "'Prompt', sans-serif",
            transition: 'color 150ms ease',
          }}>
            <span style={{ fontSize: 18, lineHeight: 1, transform: active ? 'scale(1.1)' : 'scale(1)', transition: 'transform 150ms ease' }}>{t.icon}</span>
            <span style={{ fontSize: 9, fontWeight: 500, letterSpacing: '.02em' }}>{t.label}</span>
            {active && <span style={{
              position: 'absolute', bottom: 4, width: 28, height: 2,
              borderRadius: 9999, background: MC.cyanLight, opacity: 0.8,
            }} />}
          </button>
        );
      })}
    </nav>
  );
}

window.NavBar = NavBar;


Object.assign(window, { NavBar });
