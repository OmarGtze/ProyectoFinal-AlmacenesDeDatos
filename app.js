const fmt = new Intl.NumberFormat('es-MX');
const $ = (id) => document.getElementById(id);
let complexes = [];
let selectedState = '';
let searchText = '';

function render() {
  const byState = selectedState ? complexes.filter(item => item.state === selectedState) : complexes;
  const filtered = byState.filter(item => (item.name + ' ' + item.city).toLocaleLowerCase('es-MX').includes(searchText));
  $('complex-count').textContent = fmt.format(byState.length);
  $('screen-count').textContent = fmt.format(byState.reduce((sum, item) => sum + item.screens, 0));
  $('state-count').textContent = fmt.format(new Set(byState.map(item => item.state)).size);
  $('metric-area').textContent = selectedState || 'Directorio SIC · México';
  $('result-count').textContent = fmt.format(filtered.length) + ' REGISTROS';
  $('complex-table').replaceChildren();
  if (!filtered.length) {
    const tr = document.createElement('tr'), td = document.createElement('td');
    td.colSpan = 3; td.textContent = 'No se encontraron complejos.'; tr.append(td); $('complex-table').append(tr);
  } else {
    const fragment = document.createDocumentFragment();
    filtered.forEach(item => {
      const tr = document.createElement('tr');
      [item.name, item.state, fmt.format(item.screens)].forEach(value => { const td = document.createElement('td'); td.textContent = value; tr.append(td); });
      fragment.append(tr);
    });
    $('complex-table').append(fragment);
  }
  const counts = new Map();
  complexes.forEach(item => counts.set(item.state, (counts.get(item.state) || 0) + 1));
  const top = [...counts.entries()].sort((a,b) => b[1] - a[1]).slice(0,8);
  const max = top[0]?.[1] || 1;
  $('bar-chart').replaceChildren();
  top.forEach(([state, count]) => {
    const row = document.createElement('div'); row.className = 'bar-row';
    const label = document.createElement('span'); label.textContent = state;
    const track = document.createElement('div'); track.className = 'bar-track';
    const fill = document.createElement('div'); fill.className = 'bar-fill'; fill.style.width = (count / max * 100) + '%';
    const number = document.createElement('b'); number.textContent = fmt.format(count);
    track.append(fill); row.append(label, track, number); $('bar-chart').append(row);
  });
  $('bar-chart').setAttribute('aria-label', 'Complejos por entidad, top 8 nacional: ' + top.map(([state, count]) => state + ' ' + fmt.format(count)).join(', '));
}

async function load() {
  try {
    const response = await fetch('./data/complejos.json');
    if (!response.ok) throw new Error('No se pudo abrir el archivo de datos.');
    complexes = await response.json();
    complexes.sort((a,b) => a.name.localeCompare(b.name, 'es-MX'));
    [...new Set(complexes.map(item => item.state))].sort((a,b) => a.localeCompare(b,'es-MX')).forEach(state => {
      const option = document.createElement('option'); option.value = option.textContent = state; $('state-filter').append(option);
    });
    $('state-filter').addEventListener('change', event => { selectedState = event.target.value; render(); });
    $('search-filter').addEventListener('input', event => { searchText = event.target.value.trim().toLocaleLowerCase('es-MX'); render(); });
    render();
  } catch(error) {
    $('complex-table').innerHTML = '<tr><td colspan="3">No se pudo cargar el directorio. Abre el sitio mediante un servidor local.</td></tr>';
    const status = document.createElement('p'); status.className = 'chart-status is-error'; status.textContent = error.message;
    $('bar-chart').replaceChildren(status);
  }
}
load();

const MONTHS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
async function loadSynthetic() {
  try {
    const response = await fetch('./data/resumen_sintetico.json');
    if (!response.ok) throw new Error('No se pudo abrir el resumen sintético.');
    const model = await response.json();
    if (model.tipo_dato !== 'sintetico') throw new Error('Tipo de datos inesperado.');
    const months = model.meses;
    const sum = key => months.reduce((total, month) => total + month[key], 0);
    $('synthetic-functions').textContent = fmt.format(sum('funciones'));
    $('synthetic-tickets').textContent = fmt.format(sum('boletos'));
    $('synthetic-occupancy').textContent = (100 * sum('boletos') / sum('capacidad')).toLocaleString('es-MX', {maximumFractionDigits: 1}) + ' %';
    function draw() {
      const key = $('synthetic-view').value;
      const title = {boletos: 'Boletos simulados por mes', taquilla_mxn: 'Taquilla simulada por mes', dulceria_mxn: 'Dulcería simulada por mes'}[key];
      $('synthetic-chart-title').textContent = title;
      const max = Math.max(...months.map(month => month[key]));
      $('synthetic-chart').replaceChildren();
      months.forEach((month, index) => {
        const column = document.createElement('div'); column.className = 'synthetic-month';
        const bar = document.createElement('div'); bar.className = 'synthetic-bar';
        bar.style.height = (month[key] / max * 165) + 'px';
        bar.title = MONTHS[index] + ': ' + (key === 'boletos' ? fmt.format(month[key]) + ' boletos' : '$' + fmt.format(month[key]) + ' MXN') + ' · dato sintético';
        const label = document.createElement('span'); label.textContent = MONTHS[index];
        column.append(bar, label); $('synthetic-chart').append(column);
      });
      $('synthetic-chart').setAttribute('aria-label', title + '. ' + months.map((month, index) => MONTHS[index] + ' ' + fmt.format(month[key])).join(', '));
    }
    $('synthetic-view').addEventListener('change', draw);
    draw();
  } catch (error) {
    $('synthetic-chart').textContent = 'No se pudo cargar el resumen sintético. Abre el sitio mediante un servidor local.';
  }
}
loadSynthetic();
