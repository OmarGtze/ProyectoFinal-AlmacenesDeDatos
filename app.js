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
    $('bar-chart').textContent = error.message;
  }
}
load();
