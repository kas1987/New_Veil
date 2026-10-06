// ModelGallery — title, search, grid of bio-image cards with overlay labels.
const { useState: useStateMG } = React;

const SAMPLE_MODELS = [
  { slug: 'aurora', name: 'Aurora V2', tier: 'S+', tag: 'Pony XL', hue: '#7c3aed' },
  { slug: 'cyber', name: 'CyberRealistic', tier: 'S', tag: 'Pony', hue: '#06b6d4' },
  { slug: 'solstice', name: 'Solstice', tier: 'A', tag: 'XL', hue: '#f97316' },
  { slug: 'meridian', name: 'Meridian', tier: 'A', tag: 'SDXL', hue: '#22c55e' },
  { slug: 'verdant', name: 'Verdant', tier: 'B', tag: 'SD1.5', hue: '#4ade80' },
  { slug: 'prism', name: 'Prism Core', tier: 'S+', tag: 'XL', hue: '#e11d48' },
  { slug: 'halcyon', name: 'Halcyon', tier: 'A', tag: 'Pony', hue: '#c026d3' },
  { slug: 'nimbus', name: 'Nimbus', tier: 'B', tag: 'XL', hue: '#3b82f6' },
];

function ModelThumb({ hue }) {
  return (
    <div style={{
      width: '100%', aspectRatio: '1', position: 'relative',
      background: `radial-gradient(circle at 30% 30%, ${hue}aa, transparent 60%), radial-gradient(circle at 70% 70%, ${hue}44, #0a0e1a 70%)`,
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 55%)',
      }} />
    </div>
  );
}

function ModelGallery({ onOpen }) {
  const [search, setSearch] = useStateMG('');
  const filtered = SAMPLE_MODELS.filter(m => m.name.toLowerCase().includes(search.toLowerCase()));
  const tierColor = t => t === 'S+' ? 'emerald' : t === 'S' ? 'cyan' : t === 'A' ? 'cyan' : 'white';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'auto' }}>
      <div style={{ padding: '20px 16px 12px' }}>
        <h1 style={{
          margin: 0, fontSize: 22, fontWeight: 600, letterSpacing: '-0.02em',
          color: MC.fg1, textShadow: MC.textGlow, fontFamily: "'Prompt', sans-serif",
        }}>Models</h1>
        <p style={{ margin: '2px 0 0', fontSize: 12, color: MC.fg3 }}>{SAMPLE_MODELS.length} available</p>
      </div>
      <div style={{ padding: '4px 16px 12px', position: 'sticky', top: 0, backdropFilter: 'blur(20px)', zIndex: 5 }}>
        <Input value={search} onChange={setSearch} placeholder="Search models…" />
      </div>
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8,
        padding: '0 12px 12px',
      }}>
        {filtered.map(m => (
          <GlassCard key={m.slug} onClick={() => onOpen?.(m)} style={{ borderRadius: 12 }}>
            <div style={{ position: 'relative' }}>
              <ModelThumb hue={m.hue} />
              <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, padding: 8 }}>
                <div style={{ fontSize: 12, fontWeight: 500, color: MC.fg1, lineHeight: 1.2, marginBottom: 4 }}>{m.name}</div>
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  <Pill color={tierColor(m.tier)}>{m.tier}</Pill>
                  <Pill color="white">{m.tag}</Pill>
                </div>
              </div>
            </div>
          </GlassCard>
        ))}
        {filtered.length === 0 && (
          <div style={{ gridColumn: '1 / -1', padding: '32px 16px', textAlign: 'center', color: MC.fg4, fontSize: 13 }}>
            No models match <span style={{ color: MC.fg3 }}>"{search}"</span>
          </div>
        )}
      </div>
    </div>
  );
}

window.ModelGallery = ModelGallery;


Object.assign(window, { ModelGallery, ModelThumb });
