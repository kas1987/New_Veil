// Generator — checkpoint picker, prompt panels, primary action, progress, history.
const { useState: useStateG } = React;

const CHECKPOINTS = [
  { ckpt: 'CyberRealisticPonyV16.safetensors', label: 'CyberRealistic Pony V16' },
  { ckpt: 'ponyDiffusionV6XL_v6.safetensors', label: 'Pony Diffusion V6 XL' },
  { ckpt: 'auroraV2_pony.safetensors', label: 'Aurora V2 (Pony)' },
];

const CHIPS = [
  { id: 'body', label: 'Body', items: ['slim', 'athletic', 'curvy'], color: '#facc15' },
  { id: 'mood', label: 'Mood', items: ['serene', 'fierce', 'playful', 'dreamy'], color: '#a78bfa' },
  { id: 'light', label: 'Light', items: ['golden hour', 'neon', 'studio', 'moonlit'], color: '#22d3ee' },
];

function ChipRow({ label, items, color, selected, onToggle }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ fontSize: 10, color: MC.fg3 }}>{label}</div>
      <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 2 }}>
        {items.map(i => {
          const on = selected === i;
          return (
            <button key={i} onClick={() => onToggle(on ? null : i)} style={{
              flexShrink: 0, fontSize: 12, padding: '4px 10px', borderRadius: 8,
              background: `${color}22`, color: color,
              border: on ? `1px solid ${color}` : '1px solid transparent',
              opacity: on ? 1 : 0.7,
              cursor: 'pointer', fontFamily: "'Prompt', sans-serif",
              transition: 'all 150ms ease',
            }}>{i}</button>
          );
        })}
      </div>
    </div>
  );
}

function Generator() {
  const [ckpt, setCkpt] = useStateG(CHECKPOINTS[0].ckpt);
  const [pos, setPos] = useStateG('');
  const [neg, setNeg] = useStateG('');
  const [submitting, setSubmitting] = useStateG(false);
  const [progress, setProgress] = useStateG(null);
  const [chips, setChips] = useStateG({});

  function handleGenerate() {
    if (!pos.trim()) return;
    setSubmitting(true);
    setProgress(0);
    let v = 0;
    const id = setInterval(() => {
      v += 6 + Math.random() * 10;
      if (v >= 100) {
        v = 100;
        clearInterval(id);
        setTimeout(() => { setSubmitting(false); setProgress(null); }, 600);
      }
      setProgress(Math.round(v));
    }, 180);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'auto' }}>
      <div style={{ padding: '20px 16px 4px' }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em', color: MC.fg1, textShadow: MC.textGlow, fontFamily: "'Prompt', sans-serif" }}>Generate</h1>
        <p style={{ margin: '2px 0 0', fontSize: 12, color: MC.fg3 }}>832 × 1216 · Pony XL</p>
      </div>

      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <GlassPanel style={{ padding: 12 }}>
          <Label style={{ padding: '0 0 4px' }}>Checkpoint</Label>
          <select value={ckpt} onChange={e => setCkpt(e.target.value)} style={{
            width: '100%', padding: '10px 14px', borderRadius: 12,
            background: 'rgba(255,255,255,0.05)', color: MC.fg1,
            border: '1px solid rgba(255,255,255,0.1)', fontSize: 14,
            fontFamily: "'Prompt', sans-serif", outline: 'none',
          }}>
            {CHECKPOINTS.map(c => <option key={c.ckpt} value={c.ckpt} style={{ background: '#0d1117' }}>{c.label}</option>)}
          </select>
        </GlassPanel>

        <GlassPanel style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ fontSize: 12, color: MC.fg3 }}>▼  Character</div>
            {CHIPS.map(c => (
              <ChipRow key={c.id} label={c.label} items={c.items} color={c.color}
                selected={chips[c.id]} onToggle={v => setChips(s => ({ ...s, [c.id]: v }))} />
            ))}
          </div>
          <div>
            <Label style={{ padding: '0 0 6px', display: 'block' }}>Positive prompt</Label>
            <Input rows={3} value={pos} onChange={setPos} placeholder="Describe what you want to generate…" />
          </div>
          <div>
            <Label style={{ padding: '0 0 6px', display: 'block' }}>Negative prompt</Label>
            <Input rows={2} value={neg} onChange={setNeg} placeholder="What to avoid…" />
          </div>
        </GlassPanel>

        <Button size="lg" disabled={submitting || !pos.trim()} onClick={handleGenerate} style={{ width: '100%', borderRadius: MC.radius }}>
          {submitting ? 'Generating…' : '✦  Generate'}
        </Button>

        {progress !== null && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <ProgressBar value={progress} />
            <div style={{ fontSize: 12, color: MC.fg3, textAlign: 'right' }}>{progress}%</div>
          </div>
        )}
      </div>
    </div>
  );
}

window.Generator = Generator;


Object.assign(window, { Generator });
