// Browser workflows use the same local API as the tree. Saved text is inserted as text.
const workspaceBody = document.querySelector('#workspaceBody');
const workspaceTabs = [...document.querySelectorAll('[data-view]')];
const workspace = { view: 'import', topicId: null, documentId: null, documents: [], timer: null, request: 0 };

function ui(tag, className = '', value) {
  const node = document.createElement(tag);
  node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function add(parent, ...children) { parent.append(...children); return parent; }
function button(label, action, className = '') {
  const node = ui('button', className, label);
  node.type = 'button';
  node.addEventListener('click', action);
  return node;
}
function note(parent, value, kind = '') { return add(parent, ui('p', `work-note ${kind}`, value)); }
function heading(title, description) {
  workspaceBody.replaceChildren(ui('h3', '', title), ui('p', 'work-intro', description));
}
function errorText(error) { return error instanceof Error ? error.message : 'Error desconocido'; }
async function api(path, options) {
  const response = await fetch(path, { cache: 'no-store', ...options });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Error HTTP ${response.status}`);
  return data;
}
function post(path, data) {
  return api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
}
function safePath(value) { return encodeURIComponent(value); }
function topicLink(topicId, title) {
  return button(title, () => openTopic(topicId), 'work-link');
}
function documentLink(documentId, label) {
  const link = ui('a', 'work-link', label);
  link.href = `/api/documents/${safePath(documentId)}/file`;
  return link;
}
function field(label, value = '', multiline = false) {
  const wrapper = ui('label', 'work-field');
  const control = ui(multiline ? 'textarea' : 'input');
  if (multiline) control.rows = 4;
  control.value = value || '';
  wrapper.append(ui('span', '', label), control);
  return { wrapper, control };
}
function setView(view) {
  clearTimeout(workspace.timer);
  workspace.view = view;
  workspace.request += 1;
  workspaceTabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.view === view)));
  const views = { import: renderImport, reader: renderReader, sources: renderSources,
    search: renderSearch, study: renderStudy, duplicates: renderDuplicates };
  views[view]();
}

async function renderImport() {
  heading('Importar teoría', 'Añade un DOCX. La extracción y el análisis se ejecutan en segundo plano.');
  const form = ui('form', 'work-form');
  const file = ui('input');
  file.type = 'file'; file.accept = '.docx'; file.required = true;
  const submit = ui('button', 'work-primary', 'Importar documento'); submit.type = 'submit';
  const feedback = ui('div');
  form.append(file, submit);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!file.files.length) return;
    submit.disabled = true;
    feedback.replaceChildren(ui('p', 'work-note', 'Enviando documento…'));
    try {
      const result = await api('/api/documents', { method: 'POST',
        headers: { 'X-Filename': encodeURIComponent(file.files[0].name) }, body: file.files[0] });
      workspace.documentId = result.document.id;
      feedback.replaceChildren(ui('p', 'work-note', result.created ? 'Importación iniciada.' : 'Este archivo ya estaba importado. Se muestra el registro existente.'));
      await loadDocuments();
    } catch (error) { feedback.replaceChildren(ui('p', 'work-note error', errorText(error))); }
    finally { submit.disabled = false; }
  });
  workspaceBody.append(form, feedback);
  const list = ui('div', 'work-list');
  workspaceBody.append(list);
  async function loadDocuments() {
    try {
      workspace.documents = (await api('/api/documents')).documents;
      list.replaceChildren();
      if (!workspace.documents.length) note(list, 'Todavía no hay documentos importados.');
      for (const doc of workspace.documents) {
        const card = ui('article', 'work-card');
        const top = add(card, ui('strong', '', doc.filename), ui('span', 'work-status', doc.state));
        if (doc.error) note(card, doc.error, 'error');
        for (const warning of doc.warnings || []) note(card, warning);
        const actions = ui('div', 'work-actions');
        card.append(actions);
        actions.append(documentLink(doc.id, 'Original'), button('Ver fuentes', () => openDocument(doc.id)));
        if (doc.state === 'awaiting_model' || doc.state === 'extracted') {
          actions.append(button('Analizar', () => runDocumentAction(doc.id, 'analyze')));
        }
        if (doc.state === 'failed') actions.append(button('Reintentar', () => runDocumentAction(doc.id, 'retry')));
        if (doc.state === 'completed') {
          actions.append(button('Ver temas', async () => {
            try {
              const data = await api(`/api/documents/${safePath(doc.id)}/topics`);
              if (data.topics.length) openTopic(data.topics[0].id);
              else note(card, 'Este documento no tiene temas asociados.');
            } catch (error) { note(card, errorText(error), 'error'); }
          }));
        }
        list.append(top);
      }
      if (workspace.view === 'import' && workspace.documents.some(doc => ['queued', 'extracting', 'analyzing'].includes(doc.state))) {
        workspace.timer = setTimeout(loadDocuments, 1800);
      }
    } catch (error) { list.replaceChildren(ui('p', 'work-note error', errorText(error))); }
  }
  async function runDocumentAction(id, action) {
    try { await post(`/api/documents/${safePath(id)}/${action}`, {}); await loadDocuments(); }
    catch (error) { feedback.replaceChildren(ui('p', 'work-note error', errorText(error))); }
  }
  await loadDocuments();
}

function openTopic(topicId) {
  workspace.topicId = topicId;
  const topic = state.topics.find(item => item.id === topicId);
  if (topic) focusTopic(topicId);
  setView('reader');
  document.querySelector('.workspace').scrollIntoView({ block: 'start' });
}
function openDocument(documentId) { workspace.documentId = documentId; setView('sources'); }

async function renderReader() {
  heading('Tema y corrección', 'Lee el contenido guardado y corrige sus campos y relaciones en un solo guardado.');
  const picker = ui('select', 'work-select');
  picker.append(ui('option', '', 'Selecciona un tema'));
  for (const topic of state.topics) {
    const option = ui('option', '', topic.title); option.value = topic.id; picker.append(option);
  }
  picker.value = workspace.topicId || '';
  picker.addEventListener('change', () => { workspace.topicId = picker.value || null; renderReader(); });
  workspaceBody.append(picker);
  if (!workspace.topicId) { note(workspaceBody, 'Abre un tema del árbol o selecciónalo aquí.'); return; }
  const version = workspace.request;
  const area = ui('div');
  workspaceBody.append(area);
  note(area, 'Cargando tema…');
  try {
    const topic = await api(`/api/topics/${safePath(workspace.topicId)}`);
    if (version !== workspace.request) return;
    area.replaceChildren();
    const form = ui('form', 'work-editor');
    const controls = {};
    for (const [key, label, multiline] of [
      ['title', 'Título'], ['summary', 'Resumen', true], ['explanation', 'Explicación', true],
      ['conditions', 'Condiciones', true], ['tags', 'Etiquetas (separadas por comas)'],
      ['examples', 'Ejemplos (uno por línea)', true], ['facets', 'Facetas (nombre: valor, una por línea)', true]]) {
      const value = key === 'tags' ? topic.tags.join(', ') : key === 'examples' ?
        topic.examples.map(example => typeof example === 'string' ? example : JSON.stringify(example)).join('\n') :
        key === 'facets' ? Object.entries(topic.facets).map(([name, value]) => `${name}: ${value}`).join('\n') : topic[key];
      const item = field(label, value, multiline); controls[key] = item.control; form.append(item.wrapper);
    }
    for (const [key, label, values] of [
      ['difficulty', 'Dificultad', ['basic', 'intermediate', 'advanced']],
      ['review_status', 'Revisión', ['proposed', 'reviewed', 'approved']]]) {
      const wrapper = ui('label', 'work-field');
      const select = ui('select');
      for (const value of [...new Set([...values, topic[key]])]) {
        const option = ui('option', '', value); option.value = value; select.append(option);
      }
      select.value = topic[key]; controls[key] = select;
      wrapper.append(ui('span', '', label), select); form.append(wrapper);
    }
    const relations = ui('div', 'work-relations');
    for (const [key, label, items, selected] of [
      ['placements', 'Ramas', state.branches, topic.placements],
      ['prerequisites', 'Prerrequisitos', state.topics.filter(item => item.id !== topic.id), topic.prerequisites]]) {
      const group = ui('fieldset'); group.append(ui('legend', '', label));
      for (const item of items) {
        const row = ui('label', 'work-check');
        const input = ui('input'); input.type = 'checkbox'; input.value = item.id; input.checked = selected.includes(item.id);
        row.append(input, ui('span', '', item.name || item.title)); group.append(row);
      }
      relations.append(group); controls[key] = group;
    }
    form.append(relations);
    const feedback = ui('p', 'work-note');
    const save = ui('button', 'work-primary', 'Guardar cambios'); save.type = 'submit';
    form.append(save, feedback);
    form.addEventListener('submit', async event => {
      event.preventDefault(); save.disabled = true; feedback.textContent = 'Guardando…';
      const facets = {};
      for (const line of controls.facets.value.split('\n').filter(line => line.trim())) {
        const split = line.indexOf(':');
        if (split < 1) { feedback.textContent = 'Cada faceta necesita «nombre: valor».'; save.disabled = false; return; }
        facets[line.slice(0, split).trim()] = line.slice(split + 1).trim() || null;
      }
      const payload = {
        title: controls.title.value, summary: controls.summary.value, explanation: controls.explanation.value,
        conditions: controls.conditions.value, difficulty: controls.difficulty.value,
        review_status: controls.review_status.value,
        tags: controls.tags.value.split(',').map(value => value.trim()).filter(Boolean),
        examples: controls.examples.value.split('\n').map(value => value.trim()).filter(Boolean).map(value => {
          if (!value.startsWith('{')) return value;
          try { return JSON.parse(value); } catch { return value; }
        }), facets,
        placements: [...controls.placements.querySelectorAll('input:checked')].map(item => item.value),
        prerequisites: [...controls.prerequisites.querySelectorAll('input:checked')].map(item => item.value),
      };
      try {
        await api(`/api/topics/${safePath(topic.id)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        await loadTree();
        await renderReader();
        note(workspaceBody, 'Cambios guardados.', 'success');
      } catch (error) { feedback.textContent = `No se guardó: ${errorText(error)}`; feedback.classList.add('error'); }
      finally { save.disabled = false; }
    });
    area.append(form);
    const evidence = ui('div', 'work-list');
    evidence.append(ui('h4', '', 'Referencias y revisión'));
    area.append(evidence);
    if (!topic.evidence.length) note(evidence, 'Este tema no tiene fragmentos fuente asociados.');
    for (const item of topic.evidence) evidence.append(button(`${item.role} · ${item.fragment_id.slice(0, 10)}`, () => openSourceFragment(item.fragment_id)));
    if (topic.unknowns.length) note(evidence, `Datos desconocidos: ${topic.unknowns.join(', ')}`);
    if (topic.contradictions.length) note(evidence, `Contradicciones registradas: ${topic.contradictions.length}`);
    if (topic.similar_candidates.length) evidence.append(button(`${topic.similar_candidates.length} posibles similares`, () => setView('duplicates')));
  } catch (error) { area.replaceChildren(ui('p', 'work-note error', errorText(error))); }
}

async function openSourceFragment(fragmentId) {
  workspace.fragmentId = fragmentId;
  try {
    const documents = (await api('/api/documents')).documents;
    for (const doc of documents) {
      const fragments = (await api(`/api/documents/${safePath(doc.id)}/fragments`)).fragments;
      if (fragments.some(item => item.id === fragmentId)) { workspace.documentId = doc.id; break; }
    }
  } catch { /* Source view will show the loading error. */ }
  setView('sources');
}
async function renderSources() {
  heading('Fuentes originales', 'Consulta el archivo conservado y sus fragmentos extraídos en orden.');
  const area = ui('div');
  workspaceBody.append(area);
  note(area, 'Cargando fuentes…');
  try {
    const documents = (await api('/api/documents')).documents;
    workspace.documents = documents;
    area.replaceChildren();
    if (!documents.length) { note(area, 'Importa un documento para consultar sus fuentes.'); return; }
    const picker = ui('select', 'work-select');
    for (const doc of documents) { const option = ui('option', '', doc.filename); option.value = doc.id; picker.append(option); }
    workspace.documentId = documents.some(doc => doc.id === workspace.documentId) ? workspace.documentId : documents[0].id;
    picker.value = workspace.documentId;
    picker.addEventListener('change', () => { workspace.documentId = picker.value; workspace.fragmentId = null; renderSources(); });
    area.append(picker, documentLink(workspace.documentId, 'Descargar original'));
    const list = ui('div', 'work-list');
    area.append(list);
    const fragments = (await api(`/api/documents/${safePath(workspace.documentId)}/fragments`)).fragments;
    if (!fragments.length) note(list, 'Aún no hay fragmentos extraídos.');
    for (const fragment of fragments) {
      const card = ui('article', 'work-card'); card.id = `fragment-${fragment.id}`;
      card.append(ui('strong', '', `${fragment.ordinal + 1}. ${fragment.kind} · ${fragment.locator}`));
      if (fragment.content) card.append(ui('p', 'work-source-text', fragment.content));
      if (fragment.image_name) {
        const image = ui('img', 'work-image'); image.alt = fragment.content || 'Imagen extraída del documento';
        image.src = `/api/documents/${safePath(fragment.document_id)}/images/${safePath(fragment.image_name)}`;
        card.append(image);
      }
      list.append(card);
    }
    if (workspace.fragmentId) {
      const target = document.getElementById(`fragment-${workspace.fragmentId}`);
      if (target) target.scrollIntoView({ block: 'center' });
      else note(area, 'El fragmento referenciado no aparece en este documento.', 'error');
    }
  } catch (error) { area.replaceChildren(ui('p', 'work-note error', errorText(error))); }
}

function renderSearch() {
  heading('Buscar en tu teoría', 'Pregunta al modelo local; la respuesta debe citar fragmentos de tus documentos.');
  const form = ui('form', 'work-form'); const query = ui('input');
  query.type = 'search'; query.placeholder = 'Ej. BB vs BTN en flop Axx'; query.required = true;
  const submit = ui('button', 'work-primary', 'Buscar'); submit.type = 'submit';
  const result = ui('div', 'work-list'); form.append(query, submit); workspaceBody.append(form, result);
  form.addEventListener('submit', async event => {
    event.preventDefault(); submit.disabled = true;
    result.replaceChildren(ui('p', 'work-note', 'Buscando en la biblioteca…'));
    try { showSearchResult(result, await post('/api/search', { query: query.value })); }
    catch (error) { result.replaceChildren(ui('p', 'work-note error', errorText(error))); }
    finally { submit.disabled = false; }
  });
}
function showSearchResult(area, data) {
  area.replaceChildren();
  if (data.status === 'answered') add(area, ui('h4', '', 'Respuesta con fuentes'), ui('p', 'work-answer', data.answer));
  else if (data.status === 'clarification') note(area, data.question || 'La pregunta necesita una aclaración.');
  else note(area, data.message || 'No hay evidencia suficiente para responder.');
  for (const warning of data.retrieval_warnings || []) note(area, warning);
  if (data.topics?.length) {
    area.append(ui('h4', '', 'Temas relacionados'));
    for (const topic of data.topics) area.append(topicLink(topic.id, topic.title));
  }
  if (data.sources?.length) {
    area.append(ui('h4', '', 'Fragmentos consultados'));
    for (const source of data.sources) {
      const card = ui('article', 'work-card');
      card.append(ui('strong', '', source.locator), ui('p', 'work-source-text', source.content));
      card.append(button('Abrir fuente', () => { workspace.documentId = source.document_id; openSourceFragment(source.id); }));
      area.append(card);
    }
  }
}

function renderStudy() {
  heading('Ruta de estudio', 'Ordena temas disponibles según sus prerrequisitos y fuentes de apoyo.');
  const form = ui('form', 'work-form'); const goal = ui('input');
  goal.type = 'search'; goal.placeholder = 'Ej. principiante o Axx'; goal.required = true;
  const submit = ui('button', 'work-primary', 'Crear ruta'); submit.type = 'submit';
  const result = ui('div', 'work-list'); form.append(goal, submit); workspaceBody.append(form, result);
  form.addEventListener('submit', async event => {
    event.preventDefault(); submit.disabled = true;
    result.replaceChildren(ui('p', 'work-note', 'Preparando ruta…'));
    try {
      const data = await post('/api/study-path', { goal: goal.value });
      result.replaceChildren();
      if (!data.steps.length) note(result, 'No hay una ruta respaldada por fuentes para este objetivo.');
      data.steps.forEach((step, index) => {
        const card = ui('article', 'work-card');
        card.append(ui('strong', '', `${index + 1}. ${step.title}`), ui('p', '', step.reason), topicLink(step.topic_id, 'Abrir tema'));
        for (const source of step.sources) card.append(documentLink(source.document_id, `Fuente · ${source.locator}`));
        result.append(card);
      });
      if (data.excluded.length) {
        result.append(ui('h4', '', 'Fuera de la ruta por falta de evidencia'));
        for (const item of data.excluded) note(result, `${item.title}: ${item.reason}`);
      }
    } catch (error) { result.replaceChildren(ui('p', 'work-note error', errorText(error))); }
    finally { submit.disabled = false; }
  });
}

async function renderDuplicates() {
  heading('Revisar similares', 'Compara propuestas similares antes de decidir si conservas ambos temas. No se fusionan automáticamente.');
  const area = ui('div', 'work-list');
  workspaceBody.append(area);
  try {
    const topics = (await api('/api/topics')).topics;
    const byId = new Map(topics.map(topic => [topic.id, topic]));
    let count = 0;
    const seen = new Set();
    for (const topic of topics) for (const candidate of topic.similar_candidates) {
      const other = byId.get(candidate.candidate_id);
      if (!other) continue;
      const pair = [topic.id, other.id].sort().join(':');
      if (seen.has(pair)) continue;
      seen.add(pair);
      count += 1;
      const card = ui('article', 'work-card');
      card.append(ui('strong', '', `${topic.title} ↔ ${other.title}`),
        ui('p', '', `${topic.summary || 'Sin resumen'} / ${other.summary || 'Sin resumen'}`),
        ui('span', 'work-status', `Similitud ${Math.round(candidate.score * 100)} %`),
        topicLink(topic.id, 'Primer tema'), topicLink(other.id, 'Segundo tema'));
      area.append(card);
    }
    if (!count) note(area, 'No hay candidatos similares pendientes de revisión.');
  } catch (error) { note(area, errorText(error), 'error'); }
}

workspaceTabs.forEach(tab => tab.addEventListener('click', () => setView(tab.dataset.view)));
setView('import');
