const statusEl = document.getElementById('meta');
const stepsEl = document.getElementById('steps');
const outputsEl = document.getElementById('outputs');

async function fetchJson(path) {
  try {
    const r = await fetch(path);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch (e) {
    return { _error: String(e) };
  }
}

function renderStatus(s) {
  if (!s || s.status === 'no-runner') {
    statusEl.innerText = 'No runner attached';
    stepsEl.innerHTML = '';
    outputsEl.innerText = '(none)';
    return;
  }
  statusEl.innerText = `run ${s.run_id} — ${s.completed_steps}/${s.total_steps} completed — current: ${s.current_step || '-'} `;
  // show parallel running info when available
  if (typeof s.running_count !== 'undefined') {
    statusEl.innerText += ` — running: ${s.running_count}`;
    if (Array.isArray(s.running_steps) && s.running_steps.length) {
      statusEl.innerText += ` (${s.running_steps.join(', ')})`;
    }
  }

  const steps = s.steps || {};
  stepsEl.innerHTML = '';
  Object.keys(steps).forEach(name => {
    const info = steps[name];
    const div = document.createElement('div');
    div.className = 'step ' + (info.state || 'pending');
    const title = document.createElement('div');
    title.innerHTML = `<strong>${name}</strong> — ${info.state}`;
    const times = document.createElement('div');
    times.style.fontSize = '90%';
    times.style.color = '#666';
    times.innerText = `started: ${info.started_at || '-'} ended: ${info.ended_at || '-'}`;
    const outputs = document.createElement('div');
    outputs.style.fontSize = '90%';
    outputs.style.color = '#333';
    outputs.innerText = 'outputs: ' + (info.outputs ? info.outputs.join(', ') : '(none)');
    div.appendChild(title);
    div.appendChild(times);
    div.appendChild(outputs);
    stepsEl.appendChild(div);
  });
}

async function tick() {
  const s = await fetchJson('/status');
  renderStatus(s);
  const outs = await fetchJson('/outputs');
  outputsEl.innerText = JSON.stringify(outs, null, 2);
}

setInterval(tick, 1000);
tick();
