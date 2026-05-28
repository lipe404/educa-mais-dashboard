import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Tuple
from datetime import date
import datetime
import base64
import os
import streamlit.components.v1 as components
import constants as C


@st.cache_data(show_spinner=False)
def _get_sound_b64() -> str:
    paths_to_try = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "foguete.mp3"),
        "foguete.mp3"
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass
    return ""


def _render_celebration_banner(sound_b64: str = ""):
    """Renders the animated META DO MÊS BATIDA banner with SVG icons and a replay button."""
    audio_tag = ""
    if sound_b64:
        audio_tag = f'<audio id="cel-audio" src="data:audio/mp3;base64,{sound_b64}" preload="auto"></audio>'

    banner_html = f"""<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ background:transparent; font-family:'Inter','Segoe UI',sans-serif; overflow:hidden; }}

@keyframes slide-in {{
  0% {{ opacity:0; transform:translateY(-36px) scale(0.85); }}
  60% {{ transform:translateY(6px) scale(1.03); }}
  100% {{ opacity:1; transform:translateY(0) scale(1); }}
}}
@keyframes pulse-glow {{
  0%,100% {{ filter: drop-shadow(0 0 12px #ff2d95) drop-shadow(0 0 28px #ff2d95); transform:scale(1); }}
  50% {{ filter: drop-shadow(0 0 24px #ff2d95) drop-shadow(0 0 55px #ff2d95); transform:scale(1.05); }}
}}
@keyframes shimmer {{
  0% {{ background-position:-200% center; }}
  100% {{ background-position:200% center; }}
}}
@keyframes spin-slow {{
  from {{ transform:rotate(0deg); }}
  to {{ transform:rotate(360deg); }}
}}
@keyframes float-icon {{
  0%,100% {{ transform:translateY(0px); }}
  50% {{ transform:translateY(-6px); }}
}}
@keyframes btn-pulse {{
  0%,100% {{ box-shadow:0 0 0 0 rgba(255,45,149,0.7); }}
  60% {{ box-shadow:0 0 0 12px rgba(255,45,149,0); }}
}}

.banner {{
  animation: slide-in 0.75s cubic-bezier(0.34,1.56,0.64,1) forwards;
  background: linear-gradient(135deg, #130820 0%, #2a0050 50%, #130820 100%);
  border: 2px solid #ff2d95;
  border-radius: 20px;
  padding: 28px 36px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 50px rgba(255,45,149,0.45), inset 0 0 60px rgba(255,45,149,0.04);
}}
.banner::before {{
  content:'';
  position:absolute; top:0; left:0; right:0; bottom:0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,45,149,0.12) 50%, transparent 100%);
  background-size:200% 100%;
  animation: shimmer 2.8s infinite linear;
  pointer-events:none;
}}
.icon-row {{
  display:flex; align-items:center; justify-content:center;
  gap:18px; margin-bottom:12px;
}}
.icon-trophy {{
  animation: float-icon 2.4s ease-in-out infinite;
}}
.icon-star {{
  animation: spin-slow 4s linear infinite;
  opacity:0.85;
}}
.title {{
  font-size:2.2rem; font-weight:900; letter-spacing:3px;
  color:#ff2d95;
  animation: pulse-glow 2s ease-in-out infinite;
  line-height:1.1; margin-bottom:10px;
}}
.subtitle {{
  display:flex; align-items:center; justify-content:center;
  gap:10px;
  font-size:0.95rem; color:rgba(255,255,255,0.82);
  letter-spacing:1.5px; text-transform:uppercase; margin-bottom:20px;
}}
.launch-btn {{
  display:inline-flex; align-items:center; gap:10px;
  background: linear-gradient(135deg,#ff2d95,#c4007a);
  color:#fff; border:none; border-radius:50px;
  padding:13px 32px; font-size:0.95rem; font-weight:700;
  letter-spacing:1.5px; cursor:pointer; text-transform:uppercase;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  animation: btn-pulse 2.2s ease-out infinite;
  position:relative; z-index:1;
}}
.launch-btn:hover {{
  transform:scale(1.06); box-shadow:0 0 30px rgba(255,45,149,0.7);
}}
.launch-btn:active {{ transform:scale(0.97); }}
.btn-icon {{ flex-shrink:0; }}
</style>
</head>
<body>
{audio_tag}

<div class="banner">
  <!-- Trophy + star icons -->
  <div class="icon-row">
    <!-- Trophy SVG -->
    <svg class="icon-trophy" width="52" height="52" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M24 34c-7.18 0-13-5.82-13-13V8h26v13c0 7.18-5.82 13-13 13z" fill="#ff2d95" opacity="0.9"/>
      <path d="M11 12H7a4 4 0 0 0 0 8h4M37 12h4a4 4 0 0 1 0 8h-4" stroke="#ff2d95" stroke-width="2.5" stroke-linecap="round"/>
      <rect x="18" y="34" width="12" height="4" rx="2" fill="#ff2d95" opacity="0.8"/>
      <rect x="14" y="38" width="20" height="4" rx="2" fill="#ff2d95"/>
      <path d="M18 21l2.4 1.8L24 19l3.6 3.8L30 21" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
    </svg>
    <!-- Sparkle SVG -->
    <svg class="icon-star" width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2l2.09 6.26L20.18 9l-5.09 4.14L16.73 20 12 16.27 7.27 20l1.64-6.86L3.82 9l6.09-.74L12 2z" fill="#fffb00" stroke="#ffcc00" stroke-width="0.5"/>
    </svg>
    <!-- Trophy SVG (mirrored) -->
    <svg class="icon-trophy" width="52" height="52" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" style="animation-delay:0.6s">
      <path d="M24 34c-7.18 0-13-5.82-13-13V8h26v13c0 7.18-5.82 13-13 13z" fill="#ff2d95" opacity="0.9"/>
      <path d="M11 12H7a4 4 0 0 0 0 8h4M37 12h4a4 4 0 0 1 0 8h-4" stroke="#ff2d95" stroke-width="2.5" stroke-linecap="round"/>
      <rect x="18" y="34" width="12" height="4" rx="2" fill="#ff2d95" opacity="0.8"/>
      <rect x="14" y="38" width="20" height="4" rx="2" fill="#ff2d95"/>
      <path d="M18 21l2.4 1.8L24 19l3.6 3.8L30 21" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
    </svg>
  </div>

  <p class="title">META DO MÊS BATIDA!</p>

  <div class="subtitle">
    <!-- Checkmark SVG -->
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00ff9f" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M20 6L9 17l-5-5"/>
    </svg>
    Melhor mês de todos os tempos — continue assim!
    <!-- Rocket SVG -->
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="m3.29 15 1.79-1.79m7-7-1.79 1.79"/>
      <path d="M13 4c5.33 5.33 5.33 10.67 0 16C7.67 14.67 7.67 9.33 13 4z"/>
    </svg>
  </div>

  <!-- Launch button -->
  <button class="launch-btn" id="launch-btn" onclick="launchCelebration()">
    <svg class="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="M13 4c5.33 5.33 5.33 10.67 0 16C7.67 14.67 7.67 9.33 13 4z"/>
    </svg>
    Lançar Fogos
    <svg class="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="M13 4c5.33 5.33 5.33 10.67 0 16C7.67 14.67 7.67 9.33 13 4z"/>
    </svg>
  </button>
</div>

<script>
function launchCelebration() {{
  // ---- Play real audio (user gesture allows it) ----
  var audio = document.getElementById('cel-audio');
  if (audio) {{
    audio.currentTime = 0;
    audio.volume = 0.85;
    audio.play().catch(function() {{ synthSound(); }});
  }} else {{
    synthSound();
  }}

  // ---- Inject canvas into parent Streamlit window ----
  var pd = window.parent.document;
  var old = pd.getElementById('educa-fireworks-canvas');
  if (old) old.remove();
  var canvas = pd.createElement('canvas');
  canvas.id = 'educa-fireworks-canvas';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483647;';
  pd.body.appendChild(canvas);
  var ctx = canvas.getContext('2d');

  function resize() {{ canvas.width=window.parent.innerWidth; canvas.height=window.parent.innerHeight; }}
  resize();
  window.parent.addEventListener('resize', resize);

  var COLORS=['#ff2d95','#ff69b4','#00d4ff','#fffb00','#00ff9f','#ff6600','#bf00ff','#ffffff','#aaffee'];

  function Pt(x,y,col) {{
    this.x=x; this.y=y; this.color=col;
    var a=Math.random()*Math.PI*2, sp=Math.random()*9+2;
    this.vx=Math.cos(a)*sp; this.vy=Math.sin(a)*sp;
    this.grav=0.13; this.fr=0.95; this.alpha=1;
    this.dec=Math.random()*0.013+0.007; this.sz=Math.random()*3.5+1; this.tr=[];
  }}
  Pt.prototype.upd=function() {{
    this.tr.push({{x:this.x,y:this.y,a:this.alpha}});
    if(this.tr.length>6) this.tr.shift();
    this.vx*=this.fr; this.vy*=this.fr; this.vy+=this.grav;
    this.x+=this.vx; this.y+=this.vy; this.alpha-=this.dec;
  }};
  Pt.prototype.drw=function() {{
    for(var i=0;i<this.tr.length;i++) {{
      var t=this.tr[i]; ctx.save(); ctx.globalAlpha=t.a*0.22;
      ctx.beginPath(); ctx.arc(t.x,t.y,this.sz*0.5,0,Math.PI*2);
      ctx.fillStyle=this.color; ctx.fill(); ctx.restore();
    }}
    ctx.save(); ctx.globalAlpha=this.alpha;
    ctx.beginPath(); ctx.arc(this.x,this.y,this.sz,0,Math.PI*2);
    ctx.fillStyle=this.color; ctx.shadowBlur=14; ctx.shadowColor=this.color;
    ctx.fill(); ctx.restore();
  }};

  function Rkt() {{
    this.x=Math.random()*canvas.width*0.8+canvas.width*0.1;
    this.y=canvas.height+10;
    this.tx=Math.random()*canvas.width*0.8+canvas.width*0.1;
    this.ty=Math.random()*canvas.height*0.5+canvas.height*0.05;
    var a=Math.atan2(this.ty-this.y,this.tx-this.x), sp=Math.random()*7+13;
    this.vx=Math.cos(a)*sp; this.vy=Math.sin(a)*sp;
    this.color=COLORS[Math.floor(Math.random()*COLORS.length)];
    this.sz=4; this.tr=[];
  }}
  Rkt.prototype.upd=function() {{
    this.tr.push({{x:this.x,y:this.y}});
    if(this.tr.length>14) this.tr.shift();
    this.x+=this.vx; this.y+=this.vy;
    if(this.vy>=-1||this.y<=this.ty) {{ this.exp(); return false; }}
    return true;
  }};
  Rkt.prototype.exp=function() {{
    var n=Math.floor(Math.random()*70)+90;
    for(var i=0;i<n;i++) pts.push(new Pt(this.x,this.y,this.color));
    for(var j=0;j<24;j++) {{
      var aa=(j/24)*Math.PI*2, p=new Pt(this.x,this.y,'#ffffff');
      p.vx=Math.cos(aa)*5; p.vy=Math.sin(aa)*5; pts.push(p);
    }}
  }};
  Rkt.prototype.drw=function() {{
    for(var i=0;i<this.tr.length;i++) {{
      var t=this.tr[i], r=i/this.tr.length; ctx.save(); ctx.globalAlpha=r*0.65;
      ctx.beginPath(); ctx.arc(t.x,t.y,this.sz*r*0.8,0,Math.PI*2);
      ctx.fillStyle=this.color; ctx.shadowBlur=10; ctx.shadowColor=this.color;
      ctx.fill(); ctx.restore();
    }}
    ctx.save(); ctx.beginPath(); ctx.arc(this.x,this.y,this.sz,0,Math.PI*2);
    ctx.fillStyle='#ffffff'; ctx.shadowBlur=22; ctx.shadowColor=this.color;
    ctx.fill(); ctx.restore();
  }};

  var pts=[], rkts=[], active=true, st=Date.now(), DUR=12000;

  function launch() {{
    if(Date.now()-st<DUR-2500) {{
      rkts.push(new Rkt());
      if(Math.random()<0.35) setTimeout(function(){{rkts.push(new Rkt());}},180);
    }}
  }}
  launch(); launch(); launch();
  var iv=setInterval(function() {{
    if(Date.now()-st>=DUR-2500){{clearInterval(iv);return;}}
    launch(); if(Math.random()<0.2) launch();
  }},550);

  function loop() {{
    if(!active) return;
    ctx.clearRect(0,0,canvas.width,canvas.height);
    var el=Date.now()-st, fp=Math.max(0,(el-(DUR-2500))/2500);
    if(fp<1) {{ ctx.fillStyle='rgba(0,0,0,'+(0.15*(1-fp))+')'; ctx.fillRect(0,0,canvas.width,canvas.height); }}
    for(var i=rkts.length-1;i>=0;i--) {{
      if(!rkts[i].upd()) rkts.splice(i,1); else rkts[i].drw();
    }}
    for(var j=pts.length-1;j>=0;j--) {{
      pts[j].upd();
      if(pts[j].alpha>0) pts[j].drw(); else pts.splice(j,1);
    }}
    if(el>DUR&&rkts.length===0&&pts.length===0) {{ canvas.remove(); active=false; return; }}
    requestAnimationFrame(loop);
  }}
  loop();
}}

function synthSound() {{
  try {{
    var AC=window.AudioContext||window.webkitAudioContext||window.parent.AudioContext||window.parent.webkitAudioContext;
    var ac=new AC();
    function rkt(t) {{
      var o=ac.createOscillator(), g=ac.createGain();
      o.connect(g); g.connect(ac.destination);
      o.frequency.setValueAtTime(900,t); o.frequency.exponentialRampToValueAtTime(120,t+0.7);
      g.gain.setValueAtTime(0.45,t); g.gain.exponentialRampToValueAtTime(0.001,t+0.8);
      o.start(t); o.stop(t+0.8);
    }}
    function boom(t) {{
      var b=ac.createBuffer(1,ac.sampleRate*0.5,ac.sampleRate), d=b.getChannelData(0);
      for(var i=0;i<d.length;i++) d[i]=(Math.random()*2-1)*Math.pow(1-i/d.length,1.5);
      var s=ac.createBufferSource(); s.buffer=b;
      var g=ac.createGain();
      g.gain.setValueAtTime(0.6,t); g.gain.exponentialRampToValueAtTime(0.001,t+0.55);
      s.connect(g); g.connect(ac.destination); s.start(t);
    }}
    var t=ac.currentTime;
    rkt(t); boom(t+0.75); rkt(t+1.6); boom(t+2.35);
    rkt(t+3.2); boom(t+3.95); rkt(t+4.8); boom(t+5.55);
  }} catch(e) {{}}
}}
</script>
</body>
</html>"""
    components.html(banner_html, height=230, scrolling=False)



def _render_celebration_fireworks(sound_b64: str):
    """Renders fireworks by injecting canvas into parent Streamlit window."""
    audio_tag = ""
    if sound_b64:
        audio_tag = f'<audio id="celebration-audio" src="data:audio/mp3;base64,{sound_b64}"></audio>'

    html_code = f"""<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin:0; padding:0; }}
html, body {{ width:100%; height:1px; overflow:hidden; background:transparent; }}
</style>
</head>
<body>
{audio_tag}
<script>
(function() {{
    // Inject canvas into parent (Streamlit) window - not confined to iframe
    var pd = window.parent.document;
    var old = pd.getElementById('educa-fireworks-canvas');
    if (old) old.remove();
    var canvas = pd.createElement('canvas');
    canvas.id = 'educa-fireworks-canvas';
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483647;';
    pd.body.appendChild(canvas);
    var ctx = canvas.getContext('2d');

    function resize() {{
        canvas.width = window.parent.innerWidth;
        canvas.height = window.parent.innerHeight;
    }}
    resize();
    window.parent.addEventListener('resize', resize);

    // ---- Audio ----
    var audio = document.getElementById('celebration-audio');
    function trySound() {{
        if (audio) {{ audio.volume = 0.7; audio.play().catch(synthSound); }}
        else {{ synthSound(); }}
    }}
    function synthSound() {{
        try {{
            var AC = window.AudioContext || window.webkitAudioContext
                  || window.parent.AudioContext || window.parent.webkitAudioContext;
            var ac = new AC();
            function rkt(t) {{
                var o=ac.createOscillator(), g=ac.createGain();
                o.connect(g); g.connect(ac.destination);
                o.frequency.setValueAtTime(900,t);
                o.frequency.exponentialRampToValueAtTime(120,t+0.7);
                g.gain.setValueAtTime(0.45,t);
                g.gain.exponentialRampToValueAtTime(0.001,t+0.8);
                o.start(t); o.stop(t+0.8);
            }}
            function boom(t) {{
                var b=ac.createBuffer(1,ac.sampleRate*0.5,ac.sampleRate), d=b.getChannelData(0);
                for(var i=0;i<d.length;i++) d[i]=(Math.random()*2-1)*Math.pow(1-i/d.length,1.5);
                var s=ac.createBufferSource(); s.buffer=b;
                var g=ac.createGain();
                g.gain.setValueAtTime(0.6,t); g.gain.exponentialRampToValueAtTime(0.001,t+0.55);
                s.connect(g); g.connect(ac.destination); s.start(t);
            }}
            var t=ac.currentTime;
            rkt(t); boom(t+0.75); rkt(t+1.6); boom(t+2.35);
            rkt(t+3.2); boom(t+3.95); rkt(t+4.8); boom(t+5.55);
        }} catch(e) {{}}
    }}
    trySound();

    // ---- Fireworks ----
    var COLORS=['#ff2d95','#ff69b4','#00d4ff','#fffb00','#00ff9f','#ff6600','#bf00ff','#ffffff','#aaffee'];

    function Pt(x,y,col) {{
        this.x=x; this.y=y; this.color=col;
        var a=Math.random()*Math.PI*2, sp=Math.random()*9+2;
        this.vx=Math.cos(a)*sp; this.vy=Math.sin(a)*sp;
        this.grav=0.13; this.fr=0.95; this.alpha=1;
        this.dec=Math.random()*0.013+0.007;
        this.sz=Math.random()*3.5+1; this.tr=[];
    }}
    Pt.prototype.upd=function() {{
        this.tr.push({{x:this.x,y:this.y,a:this.alpha}});
        if(this.tr.length>6) this.tr.shift();
        this.vx*=this.fr; this.vy*=this.fr; this.vy+=this.grav;
        this.x+=this.vx; this.y+=this.vy; this.alpha-=this.dec;
    }};
    Pt.prototype.drw=function() {{
        for(var i=0;i<this.tr.length;i++) {{
            var t=this.tr[i];
            ctx.save(); ctx.globalAlpha=t.a*0.22;
            ctx.beginPath(); ctx.arc(t.x,t.y,this.sz*0.5,0,Math.PI*2);
            ctx.fillStyle=this.color; ctx.fill(); ctx.restore();
        }}
        ctx.save(); ctx.globalAlpha=this.alpha;
        ctx.beginPath(); ctx.arc(this.x,this.y,this.sz,0,Math.PI*2);
        ctx.fillStyle=this.color; ctx.shadowBlur=14; ctx.shadowColor=this.color;
        ctx.fill(); ctx.restore();
    }};

    function Rkt() {{
        this.x=Math.random()*canvas.width*0.8+canvas.width*0.1;
        this.y=canvas.height+10;
        this.tx=Math.random()*canvas.width*0.8+canvas.width*0.1;
        this.ty=Math.random()*canvas.height*0.5+canvas.height*0.05;
        var a=Math.atan2(this.ty-this.y,this.tx-this.x), sp=Math.random()*7+13;
        this.vx=Math.cos(a)*sp; this.vy=Math.sin(a)*sp;
        this.color=COLORS[Math.floor(Math.random()*COLORS.length)];
        this.sz=4; this.tr=[];
    }}
    Rkt.prototype.upd=function() {{
        this.tr.push({{x:this.x,y:this.y}});
        if(this.tr.length>14) this.tr.shift();
        this.x+=this.vx; this.y+=this.vy;
        if(this.vy>=-1||this.y<=this.ty) {{ this.exp(); return false; }}
        return true;
    }};
    Rkt.prototype.exp=function() {{
        var n=Math.floor(Math.random()*70)+90;
        for(var i=0;i<n;i++) pts.push(new Pt(this.x,this.y,this.color));
        for(var j=0;j<24;j++) {{
            var a=(j/24)*Math.PI*2, p=new Pt(this.x,this.y,'#ffffff');
            p.vx=Math.cos(a)*5; p.vy=Math.sin(a)*5; pts.push(p);
        }}
    }};
    Rkt.prototype.drw=function() {{
        for(var i=0;i<this.tr.length;i++) {{
            var t=this.tr[i], r=i/this.tr.length;
            ctx.save(); ctx.globalAlpha=r*0.65;
            ctx.beginPath(); ctx.arc(t.x,t.y,this.sz*r*0.8,0,Math.PI*2);
            ctx.fillStyle=this.color; ctx.shadowBlur=10; ctx.shadowColor=this.color;
            ctx.fill(); ctx.restore();
        }}
        ctx.save(); ctx.beginPath(); ctx.arc(this.x,this.y,this.sz,0,Math.PI*2);
        ctx.fillStyle='#ffffff'; ctx.shadowBlur=22; ctx.shadowColor=this.color;
        ctx.fill(); ctx.restore();
    }};

    var pts=[], rkts=[], active=true, st=Date.now(), DUR=12000;

    function launch() {{
        if(Date.now()-st<DUR-2500) {{
            rkts.push(new Rkt());
            if(Math.random()<0.35) setTimeout(function(){{rkts.push(new Rkt());}},180);
        }}
    }}
    launch(); launch(); launch();
    var iv=setInterval(function() {{
        if(Date.now()-st>=DUR-2500){{clearInterval(iv);return;}}
        launch(); if(Math.random()<0.2) launch();
    }},550);

    function loop() {{
        if(!active) return;
        ctx.clearRect(0,0,canvas.width,canvas.height);
        var el=Date.now()-st, fp=Math.max(0,(el-(DUR-2500))/2500);
        if(fp<1) {{ ctx.fillStyle='rgba(0,0,0,'+(0.15*(1-fp))+')'; ctx.fillRect(0,0,canvas.width,canvas.height); }}
        for(var i=rkts.length-1;i>=0;i--) {{
            if(!rkts[i].upd()) rkts.splice(i,1); else rkts[i].drw();
        }}
        for(var j=pts.length-1;j>=0;j--) {{
            pts[j].upd();
            if(pts[j].alpha>0) pts[j].drw(); else pts.splice(j,1);
        }}
        if(el>DUR&&rkts.length===0&&pts.length===0) {{ canvas.remove(); active=false; return; }}
        requestAnimationFrame(loop);
    }}
    loop();
}})();
</script>
</body>
</html>"""
    components.html(html_code, height=1, scrolling=False)


def _calculate_kpis(df: pd.DataFrame) -> dict:
    total = df[C.COL_INT_VALOR].sum()
    parceiros = (df[C.COL_INT_VALOR] * df[C.COL_INT_COMISSAO]).sum()
    equipe = C.COMMISSION_RATE_TEAM * (total - parceiros)
    liquido = total - parceiros - equipe

    # Novos KPIs
    today = date.today()
    fat_hoje = df[df[C.COL_INT_DATA].dt.date == today][C.COL_INT_VALOR].sum()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    fat_semana = df[
        (df[C.COL_INT_DATA].dt.date >= start_of_week)
        & (df[C.COL_INT_DATA].dt.date <= end_of_week)
    ][C.COL_INT_VALOR].sum()
    start_of_month = today.replace(day=1)
    fat_mes = df[df[C.COL_INT_DATA].dt.date >= start_of_month][C.COL_INT_VALOR].sum()

    return {
        "total": total,
        "parceiros": parceiros,
        "equipe": equipe,
        "liquido": liquido,
        "fat_hoje": fat_hoje,
        "fat_semana": fat_semana,
        "fat_mes": fat_mes,
    }


def _render_kpis(kpis: dict):
    new_k1, new_k2, new_k3 = st.columns(3)
    new_k1.metric(C.UI_LABEL_REVENUE_TODAY, f"R$ {kpis['fat_hoje']:,.2f}")
    new_k2.metric(C.UI_LABEL_REVENUE_WEEK, f"R$ {kpis['fat_semana']:,.2f}")
    new_k3.metric(C.UI_LABEL_REVENUE_MONTH, f"R$ {kpis['fat_mes']:,.2f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(C.UI_LABEL_TOTAL_REVENUE, f"R$ {kpis['total']:,.2f}")
    c2.metric(C.UI_LABEL_PARTNER_COMMISSION, f"R$ {kpis['parceiros']:,.2f}")
    c3.metric(
        f"{C.UI_LABEL_TEAM_COMMISSION_BASE} ({int(C.COMMISSION_RATE_TEAM*100)}%)",
        f"R$ {kpis['equipe']:,.2f}",
    )
    c4.metric(C.UI_LABEL_NET_REVENUE, f"R$ {kpis['liquido']:,.2f}")


def _render_day_record_banner(full_df: pd.DataFrame) -> None:
    """
    Shows an insight banner when today's cumulative faturamento (up to today's
    day-of-month) is a historical record for that day number, and projects
    how close we are to beating the all-time best month.
    """
    today = date.today()
    current_day = today.day
    current_month = today.month
    current_year = today.year

    tmp = full_df.dropna(subset=[C.COL_INT_DATA]).copy()
    tmp["_year"] = tmp[C.COL_INT_DATA].dt.year
    tmp["_month"] = tmp[C.COL_INT_DATA].dt.month
    tmp["_day"] = tmp[C.COL_INT_DATA].dt.day

    # --- 1. Acumulado até o dia X em cada mês ---
    # For each (year, month), sum all transactions where day <= current_day
    up_to_day = tmp[tmp["_day"] <= current_day]
    cum_by_month = (
        up_to_day.groupby(["_year", "_month"])[C.COL_INT_VALOR]
        .sum()
        .reset_index()
        .rename(columns={C.COL_INT_VALOR: "acum_ate_dia"})
    )

    if cum_by_month.empty:
        return

    # Current month's cumulative up to today
    curr_row = cum_by_month[
        (cum_by_month["_year"] == current_year)
        & (cum_by_month["_month"] == current_month)
    ]
    if curr_row.empty:
        return
    curr_acum = float(curr_row["acum_ate_dia"].iloc[0])

    # Historical months (exclude current month)
    hist = cum_by_month[
        ~(
            (cum_by_month["_year"] == current_year)
            & (cum_by_month["_month"] == current_month)
        )
    ]

    if hist.empty:
        return

    best_hist_acum = float(hist["acum_ate_dia"].max())
    best_hist_row = hist.loc[hist["acum_ate_dia"].idxmax()]
    best_hist_month = int(best_hist_row["_month"])
    best_hist_year = int(best_hist_row["_year"])
    best_hist_month_name = C.MONTH_NAMES.get(best_hist_month, f"{best_hist_month:02d}")

    is_record_day = curr_acum > best_hist_acum

    # --- 2. Projection: pace-based end-of-month forecast ---
    # Daily average for current month up to today
    days_elapsed = current_day  # days 1..today
    if days_elapsed > 0:
        daily_avg = curr_acum / days_elapsed
        import calendar
        days_in_month = calendar.monthrange(current_year, current_month)[1]
        projected_total = daily_avg * days_in_month
    else:
        projected_total = 0.0
        days_in_month = 31

    # Best month total (full month)
    monthly_totals = (
        tmp.groupby(["_year", "_month"])[C.COL_INT_VALOR]
        .sum()
        .reset_index()
        .rename(columns={C.COL_INT_VALOR: "total_mes"})
    )
    hist_totals = monthly_totals[
        ~(
            (monthly_totals["_year"] == current_year)
            & (monthly_totals["_month"] == current_month)
        )
    ]
    if hist_totals.empty:
        return

    best_month_total = float(hist_totals["total_mes"].max())
    best_month_row = hist_totals.loc[hist_totals["total_mes"].idxmax()]
    best_total_month_name = C.MONTH_NAMES.get(
        int(best_month_row["_month"]), f"{int(best_month_row['_month']):02d}"
    )
    best_total_year = int(best_month_row["_year"])

    gap_to_best = best_month_total - projected_total
    pct_of_best = (projected_total / best_month_total * 100) if best_month_total > 0 else 0.0

    # --- 3. Render banner ---
    st.markdown("---")

    if is_record_day:
        st.success(
            f"""**Recorde no Dia {current_day}!**  
            Até o dia **{current_day}**, este mês acumulou **R$ {curr_acum:,.2f}** — o maior valor já registrado 
            neste dia entre todos os meses históricos  
            *(melhor anterior: {best_hist_month_name}/{best_hist_year} com R$ {best_hist_acum:,.2f})*"""
        )
    else:
        diff_to_day_record = best_hist_acum - curr_acum
        st.info(
            f"""**Pace do Dia {current_day}**  
            Acumulado até hoje: **R$ {curr_acum:,.2f}**  
            Melhor acumulado no dia {current_day}: **R$ {best_hist_acum:,.2f}** 
            *({best_hist_month_name}/{best_hist_year})* — faltam **R$ {diff_to_day_record:,.2f}** para o recorde do dia."""
        )

    # Projection sub-banner
    if gap_to_best <= 0:
        st.success(
            f"""**Projeção de Recorde Mensal!**  
            Com o ritmo atual (**R$ {daily_avg:,.2f}/dia**), a projeção para o mês é **R$ {projected_total:,.2f}** 
            — isso **superaria** o melhor mês histórico 
            *(R$ {best_month_total:,.2f} em {best_total_month_name}/{best_total_year})* em 
            **R$ {abs(gap_to_best):,.2f}**!"""
        )
    else:
        st.warning(
            f"""**Projeção de Fim de Mês** *(ritmo atual: R$ {daily_avg:,.2f}/dia)*  
            Projeção: **R$ {projected_total:,.2f}** 
            ({pct_of_best:.1f}% do melhor mês histórico — {best_total_month_name}/{best_total_year}: R$ {best_month_total:,.2f})  
            Faltam **R$ {gap_to_best:,.2f}** para bater o recorde mensal."""
        )


def _render_sankey_chart(kpis: dict):
    total = float(kpis.get("total", 0.0) or 0.0)
    parceiros = float(kpis.get("parceiros", 0.0) or 0.0)
    equipe_total = float(kpis.get("equipe", 0.0) or 0.0)
    liquido = float(kpis.get("liquido", 0.0) or 0.0)

    base_equipe = max(0.0, total - parceiros)

    equipe_fixa = max(0.0, min(equipe_total, base_equipe))
    equipe_variavel = max(0.0, base_equipe - equipe_fixa - liquido)
    liquido_sankey = max(0.0, base_equipe - equipe_fixa - equipe_variavel)

    labels = [
        "Faturamento Bruto",
        "Comissão Parceiros",
        "Base Equipe",
        "Comissão Equipe (Fixa)",
        "Comissão Equipe (Variável)",
        "Resultado Líquido",
    ]
    idx = {label: i for i, label in enumerate(labels)}

    sources = [
        idx["Faturamento Bruto"],
        idx["Faturamento Bruto"],
        idx["Base Equipe"],
        idx["Base Equipe"],
        idx["Base Equipe"],
    ]
    targets = [
        idx["Comissão Parceiros"],
        idx["Base Equipe"],
        idx["Comissão Equipe (Fixa)"],
        idx["Comissão Equipe (Variável)"],
        idx["Resultado Líquido"],
    ]
    values = [parceiros, base_equipe, equipe_fixa, equipe_variavel, liquido_sankey]

    link_colors = [
        "rgba(239,85,59,0.55)",
        "rgba(45,159,255,0.35)",
        "rgba(239,85,59,0.55)",
        "rgba(239,85,59,0.35)",
        "rgba(0,204,150,0.55)",
    ]
    node_colors = [
        "rgba(45,159,255,0.9)",
        "rgba(239,85,59,0.9)",
        "rgba(45,159,255,0.6)",
        "rgba(239,85,59,0.8)",
        "rgba(239,85,59,0.55)",
        "rgba(0,204,150,0.9)",
    ]

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=18,
                    thickness=18,
                    line=dict(color="rgba(0,0,0,0.15)", width=1),
                    label=labels,
                    color=node_colors,
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color=link_colors,
                    hovertemplate="R$ %{value:,.2f}<extra></extra>",
                ),
            )
        ]
    )

    fig.update_layout(
        title="Fluxo de Receita (Sankey)",
        font=dict(size=12),
        margin=dict(l=20, r=20, t=50, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)


def _find_best_month(full_df: pd.DataFrame, exclude_year: int, exclude_month: int):
    """Returns (best_year, best_month, best_total) from the full dataset, excluding the focus month."""
    tmp = full_df.dropna(subset=[C.COL_INT_DATA]).copy()
    tmp["_year"] = tmp[C.COL_INT_DATA].dt.year
    tmp["_month"] = tmp[C.COL_INT_DATA].dt.month
    monthly = tmp.groupby(["_year", "_month"])[C.COL_INT_VALOR].sum().reset_index()
    # Exclude the current focus month from the candidates
    monthly = monthly[
        ~((monthly["_year"] == exclude_year) & (monthly["_month"] == exclude_month))
    ]
    if monthly.empty:
        return None, None, 0.0
    best_row = monthly.loc[monthly[C.COL_INT_VALOR].idxmax()]
    return int(best_row["_year"]), int(best_row["_month"]), float(best_row[C.COL_INT_VALOR])


def _build_comparison_data(
    full_df: pd.DataFrame,
    focus_year: int, focus_month: int,
    cmp_year: int, cmp_month: int,
):
    """Builds merged day-level data for focus month vs a comparison month."""
    curr_mask = (
        (full_df[C.COL_INT_DATA].dt.year == focus_year)
        & (full_df[C.COL_INT_DATA].dt.month == focus_month)
    )
    df_curr = full_df[curr_mask].copy()

    cmp_mask = (
        (full_df[C.COL_INT_DATA].dt.year == cmp_year)
        & (full_df[C.COL_INT_DATA].dt.month == cmp_month)
    )
    df_cmp = full_df[cmp_mask].copy()

    daily_curr = (
        df_curr.groupby(df_curr[C.COL_INT_DATA].dt.day)[C.COL_INT_VALOR]
        .sum()
        .reset_index()
    )
    daily_curr.columns = ["Dia", "Valor"]

    daily_cmp = (
        df_cmp.groupby(df_cmp[C.COL_INT_DATA].dt.day)[C.COL_INT_VALOR]
        .sum()
        .reset_index()
    )
    daily_cmp.columns = ["Dia", "Valor"]

    all_days = pd.DataFrame({"Dia": range(1, 32)})
    merged = all_days.merge(daily_curr, on="Dia", how="left").rename(
        columns={"Valor": "Atual"}
    )
    merged = merged.merge(daily_cmp, on="Dia", how="left").rename(
        columns={"Valor": "Anterior"}
    )
    merged_calc = merged.fillna(0)

    total_cmp = df_cmp[C.COL_INT_VALOR].sum()
    milestone_day = None
    current_cumulative_series = merged_calc["Atual"].cumsum()
    surpassed_mask = current_cumulative_series > total_cmp
    if surpassed_mask.any():
        idx = surpassed_mask.idxmax()
        milestone_day = merged_calc.iloc[idx]["Dia"]

    return merged, merged_calc, milestone_day


def _render_daily_comparison_chart(
    full_df: pd.DataFrame, df: pd.DataFrame, focus_year: int, focus_month: int, prev_year: int, prev_month: int
):
    show_comparison = st.toggle("Comparar com Mês Anterior (Mês vs Mês)", value=False)

    if show_comparison:
        show_cumulative = st.toggle("Comparativo de Cumulativo", value=False)
        show_best = st.toggle("Comparar com Melhor Mês", value=False)

        if show_best:
            # --- Best Month Comparison ---
            best_year, best_month, best_total = _find_best_month(
                full_df, focus_year, focus_month
            )
            if best_year is None:
                st.warning("Não há dados históricos suficientes para determinar o melhor mês.")
            else:
                best_month_name = C.MONTH_NAMES.get(best_month, f"{best_month:02d}")
                st.info(
                    f"**Melhor Mês de Referência:** {best_month_name}/{best_year} "
                    f"— Faturamento total: **R$ {best_total:,.2f}**"
                )
                merged, merged_calc, milestone_day = _build_comparison_data(
                    full_df, focus_year, focus_month, best_year, best_month
                )
                if show_cumulative:
                    _render_cumulative_chart(
                        merged, merged_calc,
                        focus_month, focus_year,
                        best_month, best_year,
                        milestone_day,
                        label_ref="Melhor Mês",
                    )
                else:
                    _render_daily_bar_chart(
                        merged_calc,
                        focus_month, focus_year,
                        best_month, best_year,
                        milestone_day,
                        label_ref="Melhor Mês",
                    )
        else:
            # --- Previous Month Comparison (original behavior) ---
            merged, merged_calc, milestone_day = _build_comparison_data(
                full_df, focus_year, focus_month, prev_year, prev_month
            )
            if show_cumulative:
                _render_cumulative_chart(
                    merged, merged_calc,
                    focus_month, focus_year,
                    prev_month, prev_year,
                    milestone_day,
                )
            else:
                _render_daily_bar_chart(
                    merged_calc,
                    focus_month, focus_year,
                    prev_month, prev_year,
                    milestone_day,
                )

        st.divider()

    else:
        daily = (
            df.groupby(df[C.COL_INT_DATA].dt.date)[C.COL_INT_VALOR].sum().reset_index()
        )
        daily.columns = [C.COL_INT_DATA, C.COL_INT_VALOR]
        st.plotly_chart(
            px.line(
                daily,
                x=C.COL_INT_DATA,
                y=C.COL_INT_VALOR,
                title=C.UI_LABEL_DAILY_REVENUE,
            ),
            width="stretch",
        )
        st.divider()


def _render_cumulative_chart(
    merged, merged_calc, focus_month, focus_year, prev_month, prev_year, milestone_day,
    label_ref: str = "Mês Anterior",
):
    # --- CUMULATIVE: LINE CHART ---
    ref_label = f"{label_ref} ({prev_month:02d}/{prev_year})"
    chart_title = f"Comparativo Cumulativo: {focus_month:02d}/{focus_year} vs {ref_label}"

    # Prepare Cumulative Data
    # For Current month: We want cumulative sum up to the last valid day, then NaN
    # Identify last valid index for current month
    last_valid_idx = merged["Atual"].last_valid_index()

    cum_atual = merged_calc["Atual"].cumsum()
    cum_anterior = merged_calc["Anterior"].cumsum()

    # Mask future days for Current Month
    if last_valid_idx is not None:
        cum_atual[last_valid_idx + 1 :] = None
    else:
        # If no data at all for current month
        cum_atual[:] = None

    # Choose reference line color based on context
    ref_color = "gold" if label_ref == "Melhor Mês" else "gray"

    fig = go.Figure()

    # Reference Month Line
    fig.add_trace(
        go.Scatter(
            x=merged["Dia"],
            y=cum_anterior,
            mode="lines",
            name=ref_label,
            line=dict(color=ref_color, dash="dot", width=2),
            hovertemplate="Dia %{x}: R$ %{y:,.2f}<extra></extra>",
        )
    )

    # Current Month Line
    fig.add_trace(
        go.Scatter(
            x=merged["Dia"],
            y=cum_atual,
            mode="lines+markers",
            name=f"Mês Atual ({focus_month:02d}/{focus_year})",
            line=dict(color=C.COLOR_PRIMARY, width=3),
            marker=dict(size=6),
            hovertemplate="Dia %{x}: R$ %{y:,.2f}<extra></extra>",
        )
    )

    # Milestone Annotation
    if milestone_day:
        fig.add_vline(
            x=milestone_day,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Meta Batida (Dia {int(milestone_day)})",
            annotation_position="top left",
        )
        if label_ref == "Melhor Mês":
            st.success(
                f"Melhor mês histórico superado no dia **{int(milestone_day)}**! Recorde batido!"
            )
        else:
            st.success(
                f"Faturamento do mês anterior superado no dia **{int(milestone_day)}**!"
            )

    # Equivalence Indicator
    if last_valid_idx is not None:
        current_val = cum_atual[last_valid_idx]
        current_day = merged.iloc[last_valid_idx]["Dia"]

        equiv_mask = cum_anterior >= current_val
        if equiv_mask.any():
            equiv_idx = equiv_mask.idxmax()
            equiv_day = merged.iloc[equiv_idx]["Dia"]

            fig.add_shape(
                type="line",
                x0=current_day,
                y0=current_val,
                x1=equiv_day,
                y1=current_val,
                line=dict(color="orange", width=1, dash="dot"),
            )

            equiv_label = (
                f"Mesmo fat. no dia {int(equiv_day)} ({label_ref})"
                if label_ref == "Melhor Mês"
                else f"Mesmo fat. no dia {int(equiv_day)}"
            )
            fig.add_annotation(
                x=equiv_day,
                y=current_val,
                text=equiv_label,
                showarrow=True,
                arrowhead=1,
                ax=0,
                ay=-20,
                bgcolor="rgba(255, 165, 0, 0.2)",
            )

    fig.update_layout(
        title=chart_title,
        xaxis_title="Dia",
        yaxis_title="Valor Acumulado (R$)",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig.update_xaxes(range=[0.5, 31.5], dtick=1)
    st.plotly_chart(fig, width="stretch")


def _render_daily_bar_chart(
    merged_plot, focus_month, focus_year, prev_month, prev_year, milestone_day,
    label_ref: str = "Mês Anterior",
):
    # --- DAILY: BAR CHART ---
    ref_label = f"{label_ref} ({prev_month:02d}/{prev_year})"
    chart_title = f"Comparativo Diário: {focus_month:02d}/{focus_year} vs {ref_label}"

    # Reference bar color: golden for best month, gray otherwise
    ref_bar_color = "rgba(255, 215, 0, 0.55)" if label_ref == "Melhor Mês" else "lightgray"

    fig = go.Figure()

    # Reference Month (Bar)
    fig.add_trace(
        go.Bar(
            x=merged_plot["Dia"],
            y=merged_plot["Anterior"],
            name=ref_label,
            marker_color=ref_bar_color,
            opacity=0.75,
        )
    )

    # Current Month (Bar - Colored)
    fig.add_trace(
        go.Bar(
            x=merged_plot["Dia"],
            y=merged_plot["Atual"],
            name=f"Mês Atual ({focus_month:02d}/{focus_year})",
            marker_color=C.COLOR_PRIMARY,
            textposition="auto",
        )
    )

    # Add "Winner" indicators
    winning_days = merged_plot[merged_plot["Atual"] > merged_plot["Anterior"]]
    winner_label = (
        "Superou Melhor Mês (dia)" if label_ref == "Melhor Mês" else "Superou Mês Anterior"
    )
    if not winning_days.empty:
        fig.add_trace(
            go.Scatter(
                x=winning_days["Dia"],
                y=winning_days["Atual"],
                mode="markers",
                marker=dict(
                    symbol="star",
                    size=10,
                    color="gold",
                    line=dict(width=1, color="darkorange"),
                ),
                name=winner_label,
                hoverinfo="skip",
            )
        )

    # Add Milestone Annotation
    if milestone_day:
        fig.add_vline(
            x=milestone_day,
            line_width=2,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Meta Batida (Dia {int(milestone_day)})",
            annotation_position="top right",
        )
        if label_ref == "Melhor Mês":
            st.success(
                f"Melhor mês histórico superado no dia **{int(milestone_day)}**! Recorde batido!"
            )
        else:
            st.success(
                f"Faturamento do mês anterior superado no dia **{int(milestone_day)}**!"
            )

    fig.update_layout(
        title=chart_title,
        xaxis_title="Dia",
        yaxis_title="Valor (R$)",
        barmode="group",
        hovermode="x unified",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
    )
    fig.update_xaxes(range=[0.5, 31.5], dtick=1)
    st.plotly_chart(fig, width="stretch")


def _render_monthly_chart(df: pd.DataFrame):
    m = df.dropna(subset=[C.COL_INT_DATA]).copy()
    m["_ano"] = m[C.COL_INT_DATA].dt.year
    m["_mes"] = m[C.COL_INT_DATA].dt.month
    monthly = m.groupby(["_ano", "_mes"])[C.COL_INT_VALOR].sum().reset_index()
    if not monthly.empty:
        monthly[C.UI_LABEL_MONTH] = monthly.apply(
            lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
            axis=1,
        )
    else:
        monthly[C.UI_LABEL_MONTH] = pd.Series(dtype="string")

    show_ranking = st.toggle("Visualizar como Ranking (Ordenado por Maior Faturamento)", value=False)

    if show_ranking:
        monthly = monthly.sort_values(C.COL_INT_VALOR, ascending=False)
        chart_title = "Ranking de Faturamento por Mês (Melhores Meses)"
    else:
        monthly = monthly.sort_values(["_ano", "_mes"])
        chart_title = C.UI_LABEL_MONTHLY_REVENUE

    st.plotly_chart(
        px.bar(
            monthly,
            x=C.UI_LABEL_MONTH,
            y=C.COL_INT_VALOR,
            title=chart_title,
            color_discrete_sequence=[C.COLOR_PRIMARY],
        ),
        width="stretch",
    )
    st.divider()


def _render_month_vs_month_kpis(
    full_df: pd.DataFrame, focus_year: int, focus_month: int, prev_year: int, prev_month: int
) -> Tuple[float, float]:
    cur_mask = (full_df[C.COL_INT_DATA].dt.year == focus_year) & (
        full_df[C.COL_INT_DATA].dt.month == focus_month
    )
    prev_mask = (full_df[C.COL_INT_DATA].dt.year == prev_year) & (
        full_df[C.COL_INT_DATA].dt.month == prev_month
    )
    cur_total_month = float(full_df.loc[cur_mask, C.COL_INT_VALOR].sum())
    prev_total_month = float(full_df.loc[prev_mask, C.COL_INT_VALOR].sum())
    diff = cur_total_month - prev_total_month
    progress_pct = (
        (cur_total_month / prev_total_month * 100.0) if prev_total_month > 0 else None
    )

    # Find historically best month to calculate comparison KPIs
    best_year, best_month, best_total = _find_best_month(full_df, focus_year, focus_month)
    if best_year is not None:
        diff_best = cur_total_month - best_total
        progress_best_pct = (
            (cur_total_month / best_total * 100.0) if best_total > 0 else None
        )
        label_best = "Acima do melhor mês" if diff_best > 0 else "Falta para igualar melhor mês"
        best_value = abs(diff_best)
    else:
        best_value = 0.0
        progress_best_pct = None
        label_best = "Falta para igualar melhor mês"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(C.UI_LABEL_REVENUE_CURRENT_MONTH, f"R$ {cur_total_month:,.2f}")
    k2.metric(C.UI_LABEL_GOAL_LAST_MONTH, f"R$ {prev_total_month:,.2f}")
    k3.metric(
        (
            C.UI_LABEL_VS_LAST_MONTH_REV_UP
            if diff > 0
            else C.UI_LABEL_VS_LAST_MONTH_REV_DOWN
        ),
        f"R$ {abs(diff):,.2f}",
        delta=(f"{progress_pct:.1f}%" if progress_pct is not None else None),
    )
    if best_year is not None:
        k4.metric(
            label_best,
            f"R$ {best_value:,.2f}",
            delta=(f"{progress_best_pct:.1f}%" if progress_best_pct is not None else None),
        )
    else:
        k4.metric(label_best, "N/A")

    st.divider()
    return cur_total_month, prev_total_month


def _render_simulator(
    kpis: dict, cur_total_month: float, prev_total_month: float
):
    total = kpis["total"]
    parceiros = kpis["parceiros"]
    
    st.markdown(C.UI_LABEL_SIMULATOR_TITLE)
    sim_add = st.number_input(
        C.UI_LABEL_SIMULATOR_INPUT, min_value=0.0, step=100.0, value=0.0
    )
    avg_comissao = (parceiros / total) if total > 0 else 0.0
    sim_total = total + sim_add
    sim_parceiros = parceiros + sim_add * avg_comissao
    sim_equipe = C.COMMISSION_RATE_TEAM * (sim_total - sim_parceiros)
    sim_liquido = sim_total - sim_parceiros - sim_equipe
    s1, s2, s3, s4 = st.columns(4)
    s1.metric(C.UI_LABEL_SIMULATOR_TOTAL, f"R$ {sim_total:,.2f}")
    s2.metric(C.UI_LABEL_SIMULATOR_PARTNER, f"R$ {sim_parceiros:,.2f}")
    s3.metric(
        f"{C.UI_LABEL_SIMULATOR_TEAM} ({int(C.COMMISSION_RATE_TEAM*100)}%) (simulado)",
        f"R$ {sim_equipe:,.2f}",
    )
    s4.metric(C.UI_LABEL_SIMULATOR_NET, f"R$ {sim_liquido:,.2f}")
    cur_total_month_sim = cur_total_month + sim_add
    diff_sim = cur_total_month_sim - prev_total_month
    progress_pct_sim = (
        (cur_total_month_sim / prev_total_month * 100.0)
        if prev_total_month > 0
        else None
    )
    st.metric(
        (
            C.UI_LABEL_SIMULATOR_VS_LAST_UP
            if diff_sim > 0
            else C.UI_LABEL_SIMULATOR_VS_LAST_DOWN
        ),
        f"R$ {abs(diff_sim):,.2f}",
        delta=(f"{progress_pct_sim:.1f}%" if progress_pct_sim is not None else None),
    )


def _render_revenue_waterfall(kpis: dict) -> None:
    total = float(kpis.get("total", 0.0) or 0.0)
    parceiros = float(kpis.get("parceiros", 0.0) or 0.0)
    equipe = float(kpis.get("equipe", 0.0) or 0.0)
    liquido = float(kpis.get("liquido", 0.0) or 0.0)

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Bruto", "Comissão Parceiros", "Comissão Equipe", "Líquido"],
            y=[total, -parceiros, -equipe, liquido],
            text=[
                f"R$ {total:,.2f}",
                f"- R$ {parceiros:,.2f}",
                f"- R$ {equipe:,.2f}",
                f"R$ {liquido:,.2f}",
            ],
            textposition="outside",
            connector={"line": {"color": "rgba(255,255,255,0.25)"}},
            increasing={"marker": {"color": C.COLOR_PRIMARY}},
            decreasing={"marker": {"color": "rgba(239,85,59,0.9)"}},
            totals={"marker": {"color": "rgba(0,204,150,0.9)"}},
        )
    )
    fig.update_layout(
        title="Waterfall: Composição do Faturamento",
        yaxis_title="R$",
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
    )
    fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
    st.plotly_chart(fig, width="stretch")


def _render_monthly_ticket_boxplot(df: pd.DataFrame) -> None:
    base = df.dropna(subset=[C.COL_INT_DATA, C.COL_INT_VALOR]).copy()
    if base.empty:
        return

    base["_ano"] = base[C.COL_INT_DATA].dt.year
    base["_mes"] = base[C.COL_INT_DATA].dt.month
    base[C.UI_LABEL_MONTH] = base.apply(
        lambda r: f"{C.MONTH_NAMES.get(int(r['_mes']), str(int(r['_mes'])))} {int(r['_ano'])}",
        axis=1,
    )
    month_order = (
        base[["_ano", "_mes", C.UI_LABEL_MONTH]]
        .drop_duplicates()
        .sort_values(["_ano", "_mes"])[C.UI_LABEL_MONTH]
        .tolist()
    )

    st.markdown("### Boxplot: Ticket por Mês (dispersão de vendas)")
    fig = px.box(
        base,
        x=C.UI_LABEL_MONTH,
        y=C.COL_INT_VALOR,
        points="outliers",
        category_orders={C.UI_LABEL_MONTH: month_order},
        title="Distribuição do valor de cada venda por mês",
        color_discrete_sequence=[C.COLOR_PRIMARY],
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Valor (R$)", tickprefix="R$ ", tickformat=",.2f")
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), height=520)
    st.plotly_chart(fig, width="stretch")


def render(
    df: pd.DataFrame, full_df: pd.DataFrame, end_date: date, selected_month: int | None
):
    # --- Pre-compute month context (needed for banner before KPIs section) ---
    now = date.today()
    focus_year = end_date.year if isinstance(end_date, date) else now.year
    focus_month = (
        selected_month
        if selected_month is not None
        else end_date.month if isinstance(end_date, date) else now.month
    )
    prev_year = focus_year if focus_month > 1 else focus_year - 1
    prev_month = focus_month - 1 if focus_month > 1 else 12

    # Pre-calculate month totals for the celebration condition
    _cur_mask = (full_df[C.COL_INT_DATA].dt.year == focus_year) & (
        full_df[C.COL_INT_DATA].dt.month == focus_month
    )
    _prev_mask = (full_df[C.COL_INT_DATA].dt.year == prev_year) & (
        full_df[C.COL_INT_DATA].dt.month == prev_month
    )
    _cur_total = float(full_df.loc[_cur_mask, C.COL_INT_VALOR].sum())
    _prev_total = float(full_df.loc[_prev_mask, C.COL_INT_VALOR].sum())
    _best_year, _best_month, _best_total = _find_best_month(full_df, focus_year, focus_month)
    _beats_last = _cur_total > _prev_total and _prev_total > 0
    _beats_best = _best_year is not None and _cur_total > _best_total and _best_total > 0
    _show_celebration = _beats_last and _beats_best

    # 1. Calculate and Render Main KPIs
    kpis = _calculate_kpis(df)
    _render_kpis(kpis)

    # 1a. Celebration banner — shown right after KPIs, above Sankey
    if _show_celebration:
        sound_b64 = _get_sound_b64()
        _render_celebration_banner(sound_b64)


    with st.expander("Ver Detalhes do Resultado (Sankey)", expanded=False):
        _render_sankey_chart(kpis)

    # 1b. Day-record & pace banner (only when viewing the current real month)
    _is_current_month = (
        selected_month is None or selected_month == now.month
    ) and (
        isinstance(end_date, date) and end_date.month == now.month and end_date.year == now.year
        or not isinstance(end_date, date)
    )
    if _is_current_month:
        _render_day_record_banner(full_df)

    st.divider()

    # 2. Daily Revenue Comparison
    _render_daily_comparison_chart(
        full_df, df, focus_year, focus_month, prev_year, prev_month
    )

    # 3. Monthly Revenue Chart
    _render_monthly_chart(df)

    # 4. Month vs Month KPIs
    cur_total_month, prev_total_month = _render_month_vs_month_kpis(
        full_df, focus_year, focus_month, prev_year, prev_month
    )

    _render_revenue_waterfall(kpis)
    _render_monthly_ticket_boxplot(df)

    # 5. Simulator
    _render_simulator(kpis, cur_total_month, prev_total_month)
