/* Utilities */
function clamp01(v){ v = Number(v) || 0; return Math.max(0, Math.min(1, v)); }
function scale10(v){ return Math.round(clamp01(v)*10*10)/10; } // 1 decimal
function pctFrom10(v){ return Math.round(Math.max(0, Math.min(10, v))*10); }
function format1(v){ return (Number(v).toFixed(1)); }

/* Render overall: supports showing zeros when overall is null/empty */
function renderOverall(overall){
  const container = document.getElementById('overallScores');
  container.innerHTML = '';

  // when overall falsy -> zeros
  const ethos = overall ? scale10(overall?.ethos?.score ?? 0) : 0;
  const logos = overall ? scale10(overall?.logos ?? 0) : 0;
  const pathos = overall ? scale10(overall?.pathos ?? 0) : 0;

  const items = [
    {key:'Ethos', val:ethos, css:'ethos', grad:'background:var(--ethos);'},
    {key:'Pathos', val:pathos, css:'pathos', grad:'background:var(--pathos);'},
    {key:'Logos', val:logos, css:'logos', grad:'background:var(--logos);'}
  ];

  items.forEach(item=>{
    const div = document.createElement('div');
    div.className = 'score-item';
    div.innerHTML = `
      <div class="score-left">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div class="score-label">${item.key}</div>
          <div class="muted" style="font-weight:600">${format1(item.val)}/10</div>
        </div>
        <div class="score-bar" aria-hidden="true">
          <div class="score-fill ${item.css}" style="width:0; ${item.grad}"></div>
        </div>
      </div>
    `;
    container.appendChild(div);

    // animate fill width next frame (if zero, stays 0)
    window.requestAnimationFrame(()=> {
      const fill = div.querySelector('.score-fill');
      fill.style.width = pctFrom10(item.val) + '%';
    });
  });
}

/* Draw quadrilateral: when overall falsy -> all zeros */
function drawQuadrilateral(overall){
  const svg = document.getElementById('quadSVG');
  const w = 360, h = 300;
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  svg.innerHTML = '';

  const cx = w/2, cy = h/2;
  const maxR = Math.min(w,h) * 0.28;

  const factual = overall ? clamp01(overall?.ethos?.factual_consistency ?? 0) : 0;
  const formality = overall ? clamp01(overall?.ethos?.formality ?? 0) : 0;
  const logos = overall ? clamp01(overall?.logos ?? 0) : 0;
  const pathos = overall ? clamp01(overall?.pathos ?? 0) : 0;

  const axes = [
    {name:'Factual Consistency', v:factual, angle:-90},
    {name:'Formality', v:formality, angle:0},
    {name:'Logos', v:logos, angle:90},
    {name:'Pathos', v:pathos, angle:180}
  ];

  function polar(angleDeg, fraction){
    const rad = angleDeg * Math.PI/180;
    const r = fraction * maxR;
    return {x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad)};
  }

  for(let layer = 4; layer >= 1; layer--){
    const f = layer/4;
    const pts = axes.map(a=>{
      const p = polar(a.angle, f);
      return `${p.x},${p.y}`;
    }).join(' ');
    const poly = document.createElementNS('http://www.w3.org/2000/svg','polygon');
    poly.setAttribute('points', pts);
    poly.setAttribute('fill','none');
    poly.setAttribute('stroke','#9aa4b2');
    poly.setAttribute('stroke-opacity','0.12');
    poly.setAttribute('stroke-dasharray', layer===4 ? '6,6' : '4,6');
    poly.setAttribute('stroke-width','0.8');
    svg.appendChild(poly);
  }

  axes.forEach(a=>{
    const end = polar(a.angle, 1.02);
    const inner = polar(a.angle, 0.05);
    const line = document.createElementNS('http://www.w3.org/2000/svg','line');
    line.setAttribute('x1', cx);
    line.setAttribute('y1', cy);
    line.setAttribute('x2', inner.x);
    line.setAttribute('y2', inner.y);
    line.setAttribute('stroke','#0f1724');
    line.setAttribute('stroke-opacity','0.06');
    line.setAttribute('stroke-width','1');
    svg.appendChild(line);

    const dot = document.createElementNS('http://www.w3.org/2000/svg','circle');
    dot.setAttribute('cx', end.x);
    dot.setAttribute('cy', end.y);
    dot.setAttribute('r', 4);
    dot.setAttribute('fill','#334155');
    dot.setAttribute('fill-opacity','0.9');
    svg.appendChild(dot);

    const perc = Math.round(a.v * 100) + '%';
    const txt = document.createElementNS('http://www.w3.org/2000/svg','text');
    txt.setAttribute('x', end.x + (a.angle === 0 ? 18 : a.angle === 180 ? -18 : 0));
    txt.setAttribute('y', end.y + (a.angle === 90 ? 18 : a.angle === -90 ? -10 : 4));
    txt.setAttribute('text-anchor', a.angle === 180 ? 'end' : a.angle === 0 ? 'start' : 'middle');
    txt.setAttribute('font-size','13');
    txt.setAttribute('fill','#0f1724');
    txt.setAttribute('opacity','0.9');
    txt.textContent = perc;
    svg.appendChild(txt);

    const lab = document.createElementNS('http://www.w3.org/2000/svg','text');
    const labelPos = polar(a.angle, 0.72);
    lab.setAttribute('x', labelPos.x);
    lab.setAttribute('y', labelPos.y + 4);
    lab.setAttribute('text-anchor','middle');
    lab.setAttribute('font-size','11');
    lab.setAttribute('fill','#374151');
    lab.setAttribute('opacity','0.9');
    lab.textContent = a.name;
    svg.appendChild(lab);
  });

  const polyPoints = axes.map(a=>{
    const p = polar(a.angle, a.v);
    return `${p.x},${p.y}`;
  }).join(' ');

  const defs = document.createElementNS('http://www.w3.org/2000/svg','defs');
  const grad = document.createElementNS('http://www.w3.org/2000/svg','linearGradient');
  grad.setAttribute('id','quadGrad');
  grad.setAttribute('x1','0%'); grad.setAttribute('y1','0%'); grad.setAttribute('x2','100%'); grad.setAttribute('y2','100%');
  const stop1 = document.createElementNS('http://www.w3.org/2000/svg','stop'); stop1.setAttribute('offset','0%'); stop1.setAttribute('stop-color','#c7b3ff'); stop1.setAttribute('stop-opacity','0.28');
  const stop2 = document.createElementNS('http://www.w3.org/2000/svg','stop'); stop2.setAttribute('offset','100%'); stop2.setAttribute('stop-color','#a7f3d0'); stop2.setAttribute('stop-opacity','0.18');
  grad.appendChild(stop1); grad.appendChild(stop2); defs.appendChild(grad);
  svg.appendChild(defs);

  const poly = document.createElementNS('http://www.w3.org/2000/svg','polygon');
  poly.setAttribute('points', polyPoints);
  poly.setAttribute('fill','url(#quadGrad)');
  poly.setAttribute('stroke','#6b46ff');
  poly.setAttribute('stroke-opacity','0.18');
  poly.setAttribute('stroke-width','1.2');
  poly.setAttribute('fill-opacity','0.9');
  svg.appendChild(poly);

  axes.forEach(a=>{
    const p = polar(a.angle, a.v);
    const g = document.createElementNS('http://www.w3.org/2000/svg','g');
    const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx', p.x);
    c.setAttribute('cy', p.y);
    c.setAttribute('r', 6);
    c.setAttribute('fill','#fff');
    c.setAttribute('stroke','#6b46ff');
    c.setAttribute('stroke-width','1');
    g.appendChild(c);
    const t = document.createElementNS('http://www.w3.org/2000/svg','title');
    t.textContent = `${a.name}: ${Math.round(a.v*100)}%`;
    g.appendChild(t);
    svg.appendChild(g);
  });
}

/* Render sentences: initially empty */
function renderSentences(list){
  const container = document.getElementById('sentencesList');
  container.innerHTML = '';
  if(!list || list.length === 0){
    // show placeholder message
    const p = document.createElement('div');
    p.className = 'muted';
    p.style.padding = '12px';
    p.textContent = 'No analysis yet. Paste your text or upload a document and click Analyze Text.';
    container.appendChild(p);
    return;
  }

  list.forEach((s, idx)=>{
    const ethos = scale10(s.ethos?.score ?? 0);
    const factual = scale10(s.ethos?.factual_consistency ?? 0);
    const formality = scale10(s.ethos?.formality ?? 0);
    const logos = scale10(s.logos ?? 0);
    const pathos = scale10(s.pathos ?? 0);

    const wrap = document.createElement('div');
    wrap.className = 'sentence-item';
    wrap.innerHTML = `
      <div class="s-text"><strong>•</strong> <em style="font-weight:600">"${escapeHtml(s.sentence)}"</em></div>
      <div class="s-stats">
        <div style="display:flex;justify-content:space-between"><div class="muted">Ethos</div><div style="font-weight:700;color:#047857">${format1(ethos)}/10</div></div>
        <div class="mini-bar"><div class="mini-fill" data-role="ethos" style="background:linear-gradient(90deg,#16a34a,#34d399);width:0%"></div></div>

        <div style="display:flex;justify-content:space-between;margin-top:6px"><div class="muted">Logos</div><div style="font-weight:700;color:#b45309">${format1(logos)}/10</div></div>
        <div class="mini-bar"><div class="mini-fill" data-role="logos" style="background:linear-gradient(90deg,#f59e0b,#fb923c);width:0%"></div></div>

        <div style="display:flex;justify-content:space-between;margin-top:6px"><div class="muted">Pathos</div><div style="font-weight:700;color:#b91c1c">${format1(pathos)}/10</div></div>
        <div class="mini-bar"><div class="mini-fill" data-role="pathos" style="background:linear-gradient(90deg,#ef4444,#fb7185);width:0%"></div></div>

        <div class="meta-row">
          <div class="badge">Factual: ${format1(factual)}/10</div>
          <div class="badge">Formality: ${format1(formality)}/10</div>
        </div>
      </div>
    `;
    container.appendChild(wrap);

    // animate mini fills
    requestAnimationFrame(()=>{
      wrap.querySelector('[data-role="ethos"]').style.width = pctFrom10(ethos) + '%';
      wrap.querySelector('[data-role="logos"]').style.width = pctFrom10(logos) + '%';
      wrap.querySelector('[data-role="pathos"]').style.width = pctFrom10(pathos) + '%';
    });
  });
}

/* small HTML escape */
function escapeHtml(s){
  if(!s) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

/* INITIAL EMPTY RENDER: zeros in all places */
function renderEmpty(){
  renderOverall(null);        // shows zeros
  drawQuadrilateral(null);    // shows quad at 0%
  renderSentences([]);        // shows placeholder
}

/* Render from actual data */
function renderAllFromData(d){
  renderOverall(d.overall || {});
  drawQuadrilateral(d.overall || {});
  renderSentences(d.sentencewise || []);
}

/* Initial load -> show zeros */
renderEmpty();

/* Analyze button behaviour — now connected to Flask backend */
document.getElementById('analyzeBtn').addEventListener('click', async ()=>{
  const btn = document.getElementById('analyzeBtn');
  const prev = btn.textContent;
  btn.textContent = 'Analyzing...';
  btn.disabled = true;

  const userText = document.getElementById('inputText').value.trim();
  if(!userText.length){
    alert("Please enter some text before analyzing.");
    btn.textContent = prev;
    btn.disabled = false;
    return;
  }

  try {
    const res = await fetch("http://127.0.0.1:5000/api/analyze", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    source_text: userText,
    candidate_text: userText
  })
});

    if (!res.ok) throw new Error("Backend error " + res.status);

    const data = await res.json();
    // Flask returns { analysis: {overall:..., sentencewise:...}}
    renderAllFromData(data.analysis);

  } catch (err) {
    console.error(err);
    alert("Error connecting to backend: " + err.message);
  }

  btn.textContent = prev;
  btn.disabled = false;
});

/* Upload button (simple .txt preview) */
document.getElementById('uploadBtn').addEventListener('click', ()=>{
  document.getElementById('fileInput').click();
});
document.getElementById('fileInput').addEventListener('change', (ev)=>{
  const f = ev.target.files && ev.target.files[0];
  if(!f) return;
  if(f.type === 'text/plain' || f.name.endsWith('.txt')){
    const reader = new FileReader();
    reader.onload = () => { document.getElementById('inputText').value = reader.result; };
    reader.readAsText(f);
  } else {
    alert('Upload supported for plain .txt in demo. For .docx/.doc, send file to backend to extract text.');
  }
});