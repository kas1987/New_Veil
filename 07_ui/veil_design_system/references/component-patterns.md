# VEIL Component Patterns

Copy-paste templates for every recurring UI component in the VEIL system.

---

## Glass Card

```html
<div class="card">
  <div class="card-label">Section Title</div>
  <!-- content -->
</div>
```

```css
.card {
  background: var(--glass-bg);
  backdrop-filter: blur(22px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  padding: 14px;
  box-shadow: var(--card-shadow);
}
.card-label {
  font-family: 'Cinzel', serif;
  font-size: 8.5px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-label::before {
  content: '';
  display: block;
  width: 14px;
  height: 1px;
  background: var(--veil-bright);
  opacity: 0.65;
}
```

---

## Rail (Ghost Container)

```html
<aside class="rail rail-left">
  <div class="card">...</div>
</aside>
```

```css
.rail {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  /* Ghost state — overridden by ghost/reveal CSS */
}
.rail-left  { border-right: 1px solid var(--glass-border); }
.rail-right { border-left:  1px solid var(--glass-border); }
```

Ghost/reveal rules applied automatically via `_ghost_reveal.py` patch CSS.

---

## Provider Row

```html
<div class="provider">
  <div class="dot-status dot-online"></div>
  <div>
    <div class="provider-name">Ollama</div>
    <div class="provider-model">llama3.2:3b · local</div>
    <span class="tag tag-primary">Primary</span>
  </div>
</div>
<div class="fallback-arrow">↓ fallback</div>
```

Dot variants: `.dot-online` (green, animated blink), `.dot-standby` (amber, static)
Tag variants: `.tag-primary`, `.tag-standby`, `.tag-tts`

---

## Latency Bar Row

```html
<div class="latency-row">
  <span class="lat-label">LLM</span>
  <div class="lat-track">
    <div class="lat-fill lat-fill-llm" id="lat-llm" style="width:55%">
      <span class="lat-val" id="lat-llm-v">1.84s</span>
    </div>
  </div>
</div>
```

Fill variants: `.lat-fill-llm` (purple), `.lat-fill-tts` (cyan), `.lat-fill-rag` (bloom)
Health modifiers on `.latency-row`: `.lat-health-ok`, `.lat-health-warn`, `.lat-health-slow`

---

## Invoke Button — Standard (Footer)

```html
<button class="invoke-btn btn-bloom" id="btn-bloom" onclick="invokeBloom()">
  ◎ Invoke Bloom
</button>
```

```css
.invoke-btn {
  font-family: 'Cinzel', serif;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  padding: 11px 20px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  transition: transform 0.14s ease, box-shadow 0.25s ease;
}
.btn-bloom  { background: linear-gradient(135deg, rgba(232,121,249,0.16), rgba(124,58,237,0.26)); border: 1px solid var(--bloom); color: var(--bloom); }
.btn-quasar { background: linear-gradient(135deg, rgba(6,182,212,0.14), rgba(34,211,238,0.10)); border: 1px solid var(--quasar); color: var(--quasar-bright); }
```

---

## Invoke Button — Compact Pill (Header)

Add `.invoke-btn-compact` alongside `.invoke-btn`:

```html
<button class="invoke-btn btn-bloom invoke-btn-compact" id="btn-bloom" onclick="invokeBloom()">
  ◎ Bloom
</button>
```

```css
.invoke-btn-compact {
  padding: 5px 14px;
  font-size: 8.5px;
  letter-spacing: 0.16em;
  border-radius: 9999px;
}
```

---

## Header Pill

```html
<div class="pill pill-active"><span class="pulse-dot"></span>ACTIVE</div>
<div class="pill pill-mood" id="mood-pill" onclick="cycleMood()">⊙ DORMANT</div>
<div class="clock" id="clock">00:00:00</div>
```

Pill variants: `.pill-active`, `.pill-mode`, `.pill-mood`, `.pill-conn`

---

## Token (Modifier Toggle)

```html
<div class="token token-on" data-t="whisper-veil">
  <span class="token-pip"></span>Whisper Veil
</div>
```

State classes: `.token-on`, `.token-off`
Toggle via JS: `t.classList.toggle('token-on', !on); t.classList.toggle('token-off', on)`

---

## Stat Cell (2x2 Grid)

```html
<div class="stat-grid">
  <div class="stat-cell" style="background:rgba(124,58,237,0.08)">
    <div class="stat-num" id="s-queries" style="color:var(--veil-bright)">47</div>
    <div class="stat-lbl">Queries</div>
  </div>
</div>
```

```css
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.stat-num  { font-family: 'Cinzel Decorative', serif; font-size: 19px; }
.stat-lbl  { font-size: 7.5px; letter-spacing: 0.16em; text-transform: uppercase; }
```

---

## Snap Toast

```javascript
function snap(msg, color = '#e2e8f0') {
  const el = document.getElementById('snap-toast')
  el.textContent       = msg
  el.style.color       = color
  el.style.borderColor = color + '55'
  el.style.boxShadow   = `0 0 18px ${color}22`
  el.classList.add('visible')
  clearTimeout(_snapTid)
  _snapTid = setTimeout(() => el.classList.remove('visible'), 2800)
}
```
