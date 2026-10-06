// Review queue — stack of items with star ratings + pass/reject.
const { useState: useStateRQ } = React;

const ITEMS = [
  { id: 1, title: 'aurora_s2_014.png', sub: 'Aurora V2 · seed 441209', hue: '#7c3aed' },
  { id: 2, title: 'cyber_neon_007.png', sub: 'CyberRealistic · seed 998120', hue: '#06b6d4' },
  { id: 3, title: 'solstice_091.png', sub: 'Solstice · seed 221014', hue: '#f97316' },
];

function Thumb({ hue }) {
  return <div style={{
    width: 80, height: 80, borderRadius: 12, flexShrink: 0,
    background: `radial-gradient(circle at 30% 30%, ${hue}aa, transparent 60%), radial-gradient(circle at 70% 70%, ${hue}44, #0a0e1a 70%)`,
  }} />;
}

function ReviewQueue() {
  const [idx, setIdx] = useStateRQ(0);
  const [rating, setRating] = useStateRQ(0);
  const [done, setDone] = useStateRQ([]);

  if (idx >= ITEMS.length) {
    return (
      <div style={{ padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>✓</div>
        <h2 style={{ margin: 0, fontSize: 20, color: MC.fg1, fontFamily: "'Prompt', sans-serif" }}>Queue cleared</h2>
        <p style={{ color: MC.fg3, fontSize: 13 }}>{done.length} reviewed</p>
      </div>
    );
  }
  const it = ITEMS[idx];

  function advance(keep) {
    setDone(d => [...d, { ...it, rating, keep }]);
    setIdx(i => i + 1);
    setRating(0);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'auto' }}>
      <div style={{ padding: '20px 16px 12px' }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, color: MC.fg1, textShadow: MC.textGlow, fontFamily: "'Prompt', sans-serif", letterSpacing: '-0.02em' }}>Review</h1>
        <p style={{ margin: '2px 0 0', fontSize: 12, color: MC.fg3 }}>{idx + 1} of {ITEMS.length} · {ITEMS.length - idx} remaining</p>
      </div>

      <div style={{ padding: '0 16px 16px', flex: 1 }}>
        <GlassPanel style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            height: 260, width: '100%',
            background: `radial-gradient(circle at 30% 30%, ${it.hue}aa, transparent 60%), radial-gradient(circle at 70% 70%, ${it.hue}44, #0a0e1a 70%)`,
          }} />
          <div style={{ padding: 14 }}>
            <div style={{ fontSize: 14, fontWeight: 500, color: MC.fg1, fontFamily: "'JetBrains Mono', monospace" }}>{it.title}</div>
            <div style={{ fontSize: 12, color: MC.fg3, marginTop: 2 }}>{it.sub}</div>
            <div style={{ display: 'flex', gap: 6, marginTop: 12 }}>
              {[1,2,3,4,5].map(s => (
                <button key={s} onClick={() => setRating(s)} style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 22, color: s <= rating ? MC.yellow : MC.fg4,
                  textShadow: s <= rating ? '0 0 12px rgba(234,179,8,0.4)' : 'none',
                  transition: 'all 150ms ease',
                }}>★</button>
              ))}
            </div>
          </div>
        </GlassPanel>

        <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
          <Button variant="ghost" size="lg" onClick={() => advance(false)} style={{ flex: 1 }}>✕  Reject</Button>
          <Button size="lg" onClick={() => advance(true)} style={{ flex: 1 }}>✓  Keep</Button>
        </div>
      </div>
    </div>
  );
}

window.ReviewQueue = ReviewQueue;


Object.assign(window, { ReviewQueue });
