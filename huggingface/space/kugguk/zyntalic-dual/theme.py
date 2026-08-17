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
.zy-card.a { box-shadow:inset 0 3px 0 var(--zy-a),0 0 0 1px rgba(80,227,194,.05),0 18px 55px rgba(0,0,0,.2); }
.zy-card.b { box-shadow:inset 0 3px 0 var(--zy-b),0 0 0 1px rgba(173,124,255,.05),0 18px 55px rgba(0,0,0,.2); }
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
  animation:zy-character-settle 1400ms cubic-bezier(.16,.72,.18,1) forwards; animation-delay:var(--zy-delay); }
.zy-morph-char::before { content:attr(data-morph); position:absolute; inset:0; color:var(--zy-a);
  text-shadow:0 0 13px rgba(80,227,194,.5); animation:zy-glyph-dissolve 1400ms ease forwards; animation-delay:var(--zy-delay); }
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
.zy-ring-stage { position:relative; min-height:340px; display:grid; place-items:center; overflow:hidden; border:1px solid var(--zy-line);
  border-radius:24px; background:radial-gradient(circle at center,rgba(80,227,194,.10),rgba(10,13,28,.96) 48%,#080a13 72%); }
.zy-ring-grid { position:absolute; inset:-30%; opacity:.28; transform:perspective(480px) rotateX(62deg);
  background-image:linear-gradient(rgba(154,178,255,.14) 1px,transparent 1px),linear-gradient(90deg,rgba(154,178,255,.14) 1px,transparent 1px);
  background-size:34px 34px; animation:zy-grid-drift 9s linear infinite; }
.zy-orbit { position:absolute; width:245px; height:245px; border:1px solid rgba(80,227,194,.5); border-radius:50%;
  box-shadow:0 0 32px rgba(80,227,194,.13),inset 0 0 26px rgba(80,227,194,.08); animation:zy-orbit 5.5s linear infinite; }
.zy-orbit.inner { width:175px; height:175px; border-color:rgba(173,124,255,.62); animation-direction:reverse; animation-duration:4.2s;
  box-shadow:0 0 32px rgba(173,124,255,.14),inset 0 0 24px rgba(173,124,255,.08); }
.zy-orbit span { position:absolute; left:50%; top:-13px; transform:translateX(-50%); border:1px solid currentColor; border-radius:999px;
  padding:4px 9px; color:var(--zy-a); background:#0a0d19; font-size:.65rem; font-weight:850; letter-spacing:.14em; }
.zy-orbit.inner span { color:var(--zy-b); }
.zy-ring-core { position:relative; z-index:2; width:120px; height:120px; display:flex; flex-direction:column; align-items:center; justify-content:center;
  text-align:center; border-radius:50%; background:rgba(9,12,24,.9); box-shadow:0 0 38px rgba(117,188,255,.16); }
.zy-ring-core b { letter-spacing:.18em; font-size:.72rem; color:#edf3ff; }
.zy-ring-core small { max-width:90px; margin-top:7px; color:var(--zy-muted); font-size:.58rem; line-height:1.4; }
.zy-ring-status { position:absolute; bottom:22px; color:var(--zy-muted); font-size:.78rem; letter-spacing:.03em; }
.zy-ring-status i { display:inline-block; width:7px; height:7px; margin-right:7px; border-radius:50%; background:var(--zy-a); box-shadow:0 0 12px var(--zy-a); animation:zy-status-pulse 1.6s ease-in-out infinite; }
.zy-pulse { animation:zy-status-pulse 1.8s ease-in-out infinite; }
@keyframes zy-orbit { to { transform:rotate(360deg); } }
@keyframes zy-grid-drift { to { transform:perspective(480px) rotateX(62deg) translateY(34px); } }
@keyframes zy-status-pulse { 50% { opacity:.4; } }
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
  .zy-orbit,.zy-ring-grid,.zy-ring-status i,.zy-pulse { animation:none; }
}
footer { display:none !important; }
"""

HERO = """
<section class="zy-hero">
  <div class="zy-kicker">two editions · one public laboratory</div>
  <h1>Zyntalic Dual</h1>
  <p>Use the hosted v1.1 machine duel or the local deterministic v0.1
  comparison in one Space. Model-generated and rule-generated outputs are labeled
  separately so their authorship and operating cost remain clear.</p>
  <div class="zy-flow">
    <span><b>01</b> intent state</span><span><b>02</b> ASCI ∥ ASCI2</span>
    <span><b>03</b> cross-decode</span><span><b>04</b> cross-attack</span>
    <span><b>05</b> neutral judge</span>
  </div>
</section>
"""
