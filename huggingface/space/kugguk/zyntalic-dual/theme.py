"""Visual system for the Zyntalic intent laboratory."""

CSS = r"""
:root {
  --zy-bg: #070912;
  --zy-panel: rgba(17, 21, 38, .82);
  --zy-line: rgba(154, 178, 255, .17);
  --zy-text: #eef2ff;
  --zy-muted: #9ca8c7;
  --zy-a: #50e3c2;
  --zy-b: #ad7cff;
  --zy-warn: #ffca66;
}
.gradio-container { background: radial-gradient(circle at 14% 0%, #171d3a 0, var(--zy-bg) 38%); color: var(--zy-text); }
.zy-hero { border: 1px solid var(--zy-line); border-radius: 24px; padding: 22px 26px; margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(80,227,194,.10), rgba(173,124,255,.10)); overflow: hidden; }
.zy-kicker { color: var(--zy-a); letter-spacing: .16em; text-transform: uppercase; font-size: .75rem; font-weight: 800; }
.zy-hero h1 { margin: 6px 0 7px; font-size: clamp(2rem, 4vw, 3.5rem); line-height: .95; }
.zy-hero p { max-width: 780px; color: var(--zy-muted); font-size: 1.03rem; }
.zy-flow { display:flex; gap:9px; flex-wrap:wrap; margin-top:17px; }
.zy-flow span { border:1px solid var(--zy-line); border-radius:999px; padding:7px 11px; color:#cbd5f5; font-size:.78rem; }
.zy-flow b { color:var(--zy-a); }
.zy-card { border:1px solid var(--zy-line); border-radius:18px; padding:18px; background:var(--zy-panel); min-height: 230px; }
.zy-card.a { box-shadow: inset 0 3px 0 var(--zy-a); }
.zy-card.b { box-shadow: inset 0 3px 0 var(--zy-b); }
.zy-card h3 { margin:0 0 4px; }
.zy-thesis { color:var(--zy-muted); margin-bottom:14px; font-size:.88rem; }
.zy-adaptation { border:1px solid var(--zy-line); border-radius:10px; padding:10px; color:#cbd5f5; font-size:.84rem; margin-bottom:8px; }
.zy-candidate { border-top:1px solid var(--zy-line); padding:14px 0 4px; }
.zy-surface { font-size:1.25rem; line-height:1.55; overflow-wrap:anywhere; }
.zy-output-shell { border:1px solid var(--zy-line); border-radius:18px; padding:18px; min-height:150px;
  background:linear-gradient(145deg,rgba(80,227,194,.05),rgba(8,11,24,.92)); }
.zy-output-shell.b { background:linear-gradient(145deg,rgba(173,124,255,.06),rgba(8,11,24,.92)); }
.zy-cinematic-surface { position:relative; margin-top:8px; color:var(--zy-text); font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:clamp(1.05rem,2vw,1.35rem); line-height:1.7; overflow-wrap:anywhere; isolation:isolate; }
.zy-space { white-space:pre; }
.zy-morph-char { position:relative; display:inline-block; min-width:.15em; color:transparent;
  animation:zy-character-settle 640ms cubic-bezier(.2,.75,.2,1) forwards; animation-delay:var(--zy-delay); }
.zy-morph-char::before { content:attr(data-morph); position:absolute; inset:0; color:var(--zy-a);
  text-shadow:0 0 13px rgba(80,227,194,.5); animation:zy-glyph-dissolve 640ms ease forwards; animation-delay:var(--zy-delay); }
.zy-b .zy-morph-char::before { color:var(--zy-b); text-shadow:0 0 13px rgba(173,124,255,.5); }
@keyframes zy-character-settle {
  0%,45% { color:transparent; transform:translateY(3px) scale(.92); filter:blur(1px); }
  70% { color:#fff; text-shadow:0 0 12px currentColor; }
  100% { color:inherit; transform:none; filter:none; text-shadow:none; }
}
@keyframes zy-glyph-dissolve {
  0%,35% { opacity:.95; transform:scale(1.08) rotate(-2deg); }
  68% { opacity:.4; transform:scale(.95) rotate(2deg); }
  100% { opacity:0; transform:scale(.75); }
}
.zy-tail { color:var(--zy-warn); font-size:.86rem; margin-top:7px; }
.zy-strategy { color:#c6d0eb; font-size:.88rem; margin-top:8px; }
.zy-detail { display:grid; grid-template-columns:110px 1fr; gap:8px; color:var(--zy-muted); font-size:.80rem; margin-top:6px; }
.zy-detail b { color:#c6d0eb; }
.zy-id { color:var(--zy-muted); font-size:.68rem; letter-spacing:.1em; text-transform:uppercase; }
.zy-score { display:grid; grid-template-columns: minmax(110px,1fr) 3fr 45px; align-items:center; gap:9px; margin:7px 0; }
.zy-meter { background:#1d2441; height:7px; border-radius:8px; overflow:hidden; }
.zy-meter i { display:block; height:100%; background:linear-gradient(90deg,var(--zy-a),var(--zy-b)); }
.zy-verdict { border:1px solid var(--zy-line); border-radius:18px; padding:20px; background:linear-gradient(135deg,rgba(80,227,194,.08),rgba(173,124,255,.08)); }
.zy-verdict h2 { margin:0 0 8px; }
.zy-receiver { display:grid; gap:10px; }
.zy-duel { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; margin:14px 0; }
.zy-reading { border-left:3px solid var(--zy-a); padding:7px 12px; background:rgba(255,255,255,.025); }
.zy-reading b { color:#dce4ff; }
.zy-attack { color:var(--zy-warn); font-size:.80rem; margin-top:6px; }
.zy-error { border:1px solid #ff6b7a; color:#ffd9de; background:rgba(255,70,90,.08); border-radius:14px; padding:16px; }
.zy-empty { border:1px dashed var(--zy-line); color:var(--zy-muted); border-radius:14px; padding:18px; text-align:center; }
.zy-note { color:var(--zy-muted); font-size:.82rem; }
@media (max-width: 800px) { .zy-duel { grid-template-columns:1fr; } .zy-detail { grid-template-columns:1fr; gap:2px; } }
@media (prefers-reduced-motion: reduce) {
  .zy-morph-char { animation:none; color:inherit; }
  .zy-morph-char::before { display:none; animation:none; }
}
footer { display:none !important; }
"""

HERO = """
<section class="zy-hero">
  <div class="zy-kicker">two editions · one public laboratory</div>
  <h1>Zyntalic Dual</h1>
  <p>Use the OpenAI-powered v1.1 machine duel or the local deterministic v0.1
  comparison in one Space. Model-generated and rule-generated outputs are labeled
  separately so their authorship and operating cost remain clear.</p>
  <div class="zy-flow">
    <span><b>01</b> intent state</span><span><b>02</b> ASCI ∥ ASCI2</span>
    <span><b>03</b> cross-decode</span><span><b>04</b> cross-attack</span>
    <span><b>05</b> neutral judge</span>
  </div>
</section>
"""
