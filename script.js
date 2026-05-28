// ── STATE ──────────────────────────────────────────────
let requirements = [];

// ── TAB SWITCHING ──────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tool-panel').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
}
document.getElementById('heroArchBtn').addEventListener('click', function(e) {
  e.preventDefault();
  switchTab('architect', document.querySelectorAll('.tab-btn')[1]);
  setTimeout(() => document.getElementById('tools').scrollIntoView({behavior:'smooth'}), 50);
});

// ── TOAST ──────────────────────────────────────────────
function showToast(msg, type = 'error') {
  const t = document.getElementById('toast');
  t.textContent = (type === 'error' ? '⚠ ' : '✓ ') + msg;
  t.className = `toast ${type} visible`;
  setTimeout(() => t.classList.remove('visible'), 4500);
}

// ── URL EXAMPLES ───────────────────────────────────────
function setUrl(url) {
  document.getElementById('urlInput').value = url;
  document.getElementById('urlInput').focus();
}

// ── REQUIREMENTS ──────────────────────────────────────
function renderReqs() {
  document.getElementById('reqTags').innerHTML = requirements.map((r, i) =>
    `<div class="req-tag">${esc(r)}<span class="remove-tag" onclick="removeReq(${i})">✕</span></div>`
  ).join('');
}
function addReq() {
  const v = document.getElementById('reqInput').value.trim();
  if (!v || requirements.includes(v)) return;
  requirements.push(v);
  document.getElementById('reqInput').value = '';
  renderReqs();
}
function removeReq(i) { requirements.splice(i, 1); renderReqs(); }
function reqKeydown(e) { if (e.key === 'Enter') { e.preventDefault(); addReq(); } }

// ── RENDER URL ANALYSIS ────────────────────────────────
function renderAnalysis(data) {
  const hasAnswer = data.answer && data.answer !== 'null' && data.answer !== null;

  const keyPoints = (data.key_points || []).map(p =>
    `<div class="key-point"><span class="kp-arrow">→</span><span>${esc(p)}</span></div>`
  ).join('');

  const topicTags = (data.topics || []).map(t =>
    `<span class="topic-tag">${esc(t)}</span>`
  ).join('');

  const answerBlock = hasAnswer ? `
    <div class="answer-box">
      <div class="answer-label">YOUR ANSWER</div>
      <div class="answer-text">${esc(data.answer)}</div>
    </div>` : '';

  document.getElementById('analyzeResults').innerHTML = `
    <div class="analysis-result">
      <div class="analysis-header">
        <div class="analysis-meta">
          <span class="type-chip">${esc(data.type || 'webpage')}</span>
          <span class="read-time">${esc(data.read_time || '')}</span>
        </div>
        <div class="analysis-title">${esc(data.title || 'Page Analysis')}</div>
        <a class="analysis-url" href="${esc(data.url)}" target="_blank">${esc(data.url)}</a>
      </div>
      <div class="analysis-body">
        ${hasAnswer ? `<div class="arch-section">${answerBlock}</div>` : ''}
        <div class="arch-section">
          <div class="analysis-section-title">Summary</div>
          <div class="summary-text">${esc(data.summary || '')}</div>
        </div>
        ${keyPoints ? `<div class="arch-section">
          <div class="analysis-section-title">Key Points</div>
          <div class="key-points">${keyPoints}</div>
        </div>` : ''}
        ${topicTags ? `<div class="arch-section">
          <div class="analysis-section-title">Topics</div>
          <div class="topic-tags">${topicTags}</div>
        </div>` : ''}
      </div>
    </div>`;
}

// ── RUN URL ANALYSIS ───────────────────────────────────
async function runAnalyze() {
  const url = document.getElementById('urlInput').value.trim();
  const query = document.getElementById('urlQuery').value.trim();
  if (!url) return showToast('Please enter a URL.');

  const btn = document.getElementById('analyzeBtn');
  const loader = document.getElementById('analyzeLoader');
  const loadText = document.getElementById('analyzeLoadText');
  btn.disabled = true;
  document.getElementById('analyzeBtnText').textContent = 'Analyzing...';
  loader.classList.add('visible');

  // Cycle loading messages
  const msgs = ['Fetching page...', 'Cleaning content...', 'Analyzing with AI...', 'Extracting insights...'];
  let mi = 0;
  const msgInterval = setInterval(() => { loadText.textContent = msgs[++mi % msgs.length]; }, 1800);

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, query: query || 'summarize' })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
    renderAnalysis(data);
  } catch (err) {
    showToast(err.message || 'Something went wrong.');
    document.getElementById('analyzeResults').innerHTML = `<div class="result-empty"><div class="icon">⚠️</div><p>${esc(err.message)}</p></div>`;
  } finally {
    clearInterval(msgInterval);
    btn.disabled = false;
    document.getElementById('analyzeBtnText').textContent = '🔭 Analyze URL';
    loader.classList.remove('visible');
  }
}

// ── RENDER AWS ARCHITECTURE ────────────────────────────
function renderArch(data) {
  const services = (data.services || []).map(s => {
    const tierClass = s.tier === 'free' ? 'free' : s.tier === 'low-cost' ? 'low-cost' : 'paid';
    const tierLabel = s.tier === 'free' ? '✓ Free' : s.tier === 'low-cost' ? '~ Low Cost' : '$ Paid';
    return `<div class="service-card">
      <div>
        <div class="service-name">${esc(s.name)}</div>
        <div class="service-purpose">${esc(s.purpose)}</div>
        ${s.free_tier && s.free_tier !== 'N/A' ? `<div class="service-free">Free tier: ${esc(s.free_tier)}</div>` : ''}
      </div>
      <div class="service-cost">
        <div class="cost-badge ${tierClass}">${tierLabel}</div>
        <div style="font-family:var(--fm);font-size:.67rem;color:var(--muted2);margin-top:.3rem;text-align:right">${esc(s.monthly_estimate)}</div>
      </div>
    </div>`;
  }).join('');

  const flowSteps = (data.diagram_steps || []).map((step, i) => `
    ${i > 0 ? '<div class="flow-connector"></div>' : ''}
    <div class="flow-step">
      <div class="flow-num">${i + 1}</div>
      <span>${esc(step)}</span>
    </div>`).join('');

  const warnings = (data.warnings || []).map(w =>
    `<div class="warning-item"><span class="warning-icon">⚠</span><span>${esc(w)}</span></div>`
  ).join('');

  const freeSafe = data.free_tier_safe;

  document.getElementById('archResults').innerHTML = `
    <div class="arch-result">
      <div class="arch-header">
        <div class="arch-name">${esc(data.architecture_name || 'AWS Architecture')}</div>
        <div class="arch-overview">${esc(data.overview || '')}</div>
      </div>
      <div class="arch-body">
        <div class="total-row">
          <div>
            <div class="total-label">ESTIMATED MONTHLY COST</div>
            <div class="total-val">${esc(data.total_estimate || 'See breakdown')}</div>
          </div>
          <span class="free-safe-badge ${freeSafe ? 'yes' : 'no'}">
            ${freeSafe ? '✓ Free Tier Safe' : '⚠ May exceed free tier'}
          </span>
        </div>
        <div class="arch-section">
          <div class="arch-section-title">AWS Services</div>
          ${services}
        </div>
        <div class="arch-section">
          <div class="arch-section-title">Data Flow</div>
          <div class="flow-steps">${flowSteps}</div>
        </div>
        ${warnings ? `<div class="arch-section">
          <div class="arch-section-title">⚠ Watch Out</div>
          ${warnings}
        </div>` : ''}
        ${data.iac_hint ? `<div class="arch-section">
          <div class="iac-box">
            <div class="iac-label">TERRAFORM / CLOUDFORMATION TIP</div>
            <div class="iac-text">${esc(data.iac_hint)}</div>
          </div>
        </div>` : ''}
      </div>
    </div>`;
}

// ── RUN AWS ARCHITECT ──────────────────────────────────
async function runArchitect() {
  const description = document.getElementById('archDesc').value.trim();
  if (!description) return showToast('Please describe your project.');

  const btn = document.getElementById('archBtn');
  const loader = document.getElementById('archLoader');
  btn.disabled = true;
  btn.textContent = 'Designing...';
  loader.classList.add('visible');

  try {
    const res = await fetch('/api/architect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        description,
        requirements,
        budget: document.getElementById('archBudget').value,
        scale: document.getElementById('archScale').value
      })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
    renderArch(data);
  } catch (err) {
    showToast(err.message || 'Something went wrong.');
    document.getElementById('archResults').innerHTML = `<div class="result-empty"><div class="icon">⚠️</div><p>${esc(err.message)}</p></div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = '☁️ Design Architecture';
    loader.classList.remove('visible');
  }
}

// ── UTILITY ────────────────────────────────────────────
function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
