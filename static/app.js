const $ = (selector) => document.querySelector(selector);
const dropzone = $('#dropzone'), fileInput = $('#file'), dashboard = $('#dashboard');
const steps = ['Validating image structure...', 'Parsing metadata signatures...', 'Performing Error Level Analysis...', 'Evaluating texture and lighting consistency...', 'Compiling forensic report...'];

$('#browse').onclick = () => fileInput.click();
fileInput.onchange = () => fileInput.files[0] && submit(fileInput.files[0]);
['dragenter','dragover'].forEach(event => dropzone.addEventListener(event, e => { e.preventDefault(); dropzone.classList.add('drag'); }));
['dragleave','drop'].forEach(event => dropzone.addEventListener(event, e => { e.preventDefault(); dropzone.classList.remove('drag'); }));
dropzone.addEventListener('drop', e => e.dataTransfer.files[0] && submit(e.dataTransfer.files[0]));
$('#again').onclick = () => { dashboard.classList.add('hidden'); dropzone.classList.remove('hidden'); fileInput.value = ''; window.scrollTo({top:0, behavior:'smooth'}); };
$('#slider').oninput = e => $('#heat-layer').style.width = `${e.target.value}%`;

function startProgress() { $('#progress').classList.remove('hidden'); let step = 0; $('#progress-label').textContent = steps[0]; $('.track i').style.width = '8%'; return setInterval(() => { step = Math.min(step + 1, steps.length - 1); $('#progress-label').textContent = steps[step]; $('.track i').style.width = `${20 + step * 20}%`; }, 450); }
function metric(name, value) { return `<div class="metric"><div><small>${name}</small><b>${value}%</b></div><div class="bar"><i style="width:${value}%"></i></div></div>`; }
function render(data) {
  $('#score').textContent = `${data.score}%`; $('#verdict').textContent = data.verdict;
  $('#gauge-ring').style.strokeDashoffset = 327 - (327 * data.score / 100);
  $('#metric-list').innerHTML = metric('ELA COMPRESSION', data.metrics.ela) + metric('TEXTURE VARIATION', data.metrics.texture) + metric('LIGHTING CONSISTENCY', data.metrics.lighting) + metric('METADATA SIGNALS', data.metrics.metadata);
  $('#alerts').innerHTML = data.alerts.map(a => `<div class="alert ${a.level}">${a.text}</div>`).join('');
  $('#original').src = data.original_url; $('#heatmap').src = data.heatmap_url;
  dashboard.classList.remove('hidden'); dashboard.scrollIntoView({behavior:'smooth', block:'start'});
}
async function submit(file) {
  if (!['image/jpeg','image/png','image/webp'].includes(file.type)) return alert('Please choose a JPEG, PNG, or WebP image.');
  dropzone.classList.add('hidden'); const timer = startProgress();
  const form = new FormData(); form.append('file', file);
  try { const response = await fetch('/api/analyze', {method:'POST', body:form}); const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Analysis failed'); clearInterval(timer); $('.track i').style.width='100%'; setTimeout(() => { $('#progress').classList.add('hidden'); render(data); }, 250); }
  catch (error) { clearInterval(timer); $('#progress').classList.add('hidden'); dropzone.classList.remove('hidden'); alert(error.message); }
}
