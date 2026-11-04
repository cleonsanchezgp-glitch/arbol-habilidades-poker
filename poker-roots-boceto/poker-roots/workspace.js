// Browser workflows use the same local API as the tree. Saved text is inserted as text.
const workspaceBody = document.querySelector('#workspaceBody');
const workspaceTabs = [...document.querySelectorAll('[data-view]')];
const navigationButtons = [...document.querySelectorAll('[data-nav]')];
const workspace = { view: 'import', topicId: null, documentId: null, documents: [],
  documentStates: new Map(), timer: null, request: 0, creating: false, editing: false, modelConfigured: null };

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
const importStates = {
  stored: 'Guardado', queued: 'En cola', extracting: 'Extrayendo',
  extracted: 'Extraído', awaiting_model: 'Pendiente de modelo local',
  analyzing: 'Analizando', completed: 'Completado', failed: 'Falló',
};
function importHelp(doc) {
  if (doc.state === 'awaiting_model') return 'La extracción terminó. Ya puedes leer las fuentes y crear temas manualmente.';
  if (doc.state === 'failed') return 'La importación falló. Revisa el error y pulsa Reintentar.';
  if (doc.state === 'completed') return 'Los temas están guardados y listos para revisar.';
  if (['queued', 'extracting', 'analyzing'].includes(doc.state)) return 'Puedes seguir navegando mientras se procesa el documento.';
  return '';
}
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
function setNavigation(target) {
  navigationButtons.forEach(item => {
    if (item.dataset.nav === target) item.setAttribute('aria-current', 'page');
    else item.removeAttribute('aria-current');
  });
}
function setView(view) {
  clearTimeout(workspace.timer);
  workspace.view = view;
  if (view !== 'reader') workspace.creating = false;
  workspace.request += 1;
  workspaceTabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.view === view)));
  setNavigation(view);
  const views = { import: renderImport, reader: renderReader, sources: renderSources,
    search: renderSearch, study: renderStudy, duplicates: renderDuplicates };
  views[view]();
}

async function renderImport() {
  const version = workspace.request;
  heading('Tus documentos', 'Guarda el DOCX original y consulta sus fragmentos. Puedes crear temas manualmente mientras no haya modelo local.');
  const modelBanner = ui('p', 'work-note model-banner', 'Comprobando el estado del análisis automático…');
  workspaceBody.append(modelBanner);
  try {
    const health = await api('/api/health');
    workspace.modelConfigured = Boolean(health.model_configured);
    modelBanner.textContent = workspace.modelConfigured ?
      'El análisis automático está configurado. También puedes crear y corregir temas manualmente.' :
      'Modo manual: tus documentos y fuentes están disponibles. El análisis automático se activará cuando configures un modelo local.';
  } catch {
    modelBanner.textContent = 'No se pudo consultar el estado del análisis. La importación manual sigue disponible.';
  }
  if (version !== workspace.request) return;
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
      workspace.documentStates.set(result.document.id, result.document.state);
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
      const newlyCompleted = workspace.documents.some(doc => doc.state === 'completed' &&
        workspace.documentStates.has(doc.id) && workspace.documentStates.get(doc.id) !== 'completed');
      for (const doc of workspace.documents) workspace.documentStates.set(doc.id, doc.state);
      if (newlyCompleted) await loadTree();
      list.replaceChildren();
      if (!workspace.documents.length) note(list, 'Todavía no hay documentos importados.');
      for (const doc of workspace.documents) {
        const card = ui('article', 'work-card');
        const top = add(card, ui('strong', '', doc.filename), ui('span', 'work-status', importStates[doc.state] || doc.state));
        if (importHelp(doc)) note(card, importHelp(doc));
        if (doc.error && doc.state !== 'awaiting_model') note(card, doc.error, 'error');
        for (const warning of doc.warnings || []) note(card, warning);
        const actions = ui('div', 'work-actions');
        card.append(actions);
        actions.append(documentLink(doc.id, 'Original'), button('Ver fuentes', () => openDocument(doc.id)));
        if ((doc.state === 'awaiting_model' || doc.state === 'extracted') && workspace.modelConfigured) {
          actions.append(button('Analizar', () => runDocumentAction(doc.id, 'analyze')));
        }
        if (doc.state === 'awaiting_model' || doc.state === 'extracted') {
          actions.append(button('Crear tema con esta fuente', () => {
            workspace.documentId = doc.id; workspace.creating = true; setView('reader');
            document.querySelector('.workspace').scrollIntoView({ block: 'start' });
          }, 'work-action-emphasis'));
        }
        if (doc.state === 'failed') actions.append(button('Reintentar', () => runDocumentAction(doc.id, 'retry')));
        actions.append(button('Ver temas', async () => {
          try {
            const data = await api(`/api/documents/${safePath(doc.id)}/topics`);
            if (data.topics.length) openTopic(data.topics[0].id);
            else note(card, 'Este documento aún no tiene temas. Puedes crear uno con una de sus fuentes.');
          } catch (error) { note(card, errorText(error), 'error'); }
        }));
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
  workspace.creating = false;
  workspace.editing = false;
  const topic = state.topics.find(item => item.id === topicId);
  if (topic) focusTopic(topicId);
  setView('reader');
  document.querySelector('.workspace').scrollIntoView({ block: 'start' });
}
function openDocument(documentId) { workspace.documentId = documentId; setView('sources'); }

async function renderCreateTopic() {
  const version = workspace.request;
  heading('Crear un tema', 'Escribe tu teoría y, si procede de un documento, enlaza un fragmento. El tema aparecerá en el mapa al guardarlo.');
  const cancel = button('← Volver a mis temas', () => { workspace.creating = false; setView('reader'); }, 'work-quiet');
  workspaceBody.append(cancel);
  const form = ui('form', 'work-editor work-create');
  const title = field('Título del tema'); title.control.required = true;
  const summary = field('Idea principal', '', true);
  const explanation = field('Explicación', '', true);
  const conditions = field('Cuándo se aplica', '', true);
  form.append(title.wrapper, summary.wrapper, explanation.wrapper, conditions.wrapper);
  const difficulty = ui('select');
  for (const [value, label] of [['basic', 'Básico'], ['intermediate', 'Intermedio'], ['advanced', 'Avanzado']]) {
    const option = ui('option', '', label); option.value = value; difficulty.append(option);
  }
  const difficultyLabel = add(ui('label', 'work-field'), ui('span', '', 'Dificultad'), difficulty);
  const branch = ui('select');
  const noBranch = ui('option', '', 'Sin rama por ahora'); noBranch.value = ''; branch.append(noBranch);
  for (const item of state.branches) {
    const option = ui('option', '', item.name); option.value = item.id; branch.append(option);
  }
  const branchLabel = add(ui('label', 'work-field'), ui('span', '', 'Lugar en el mapa'), branch);
  form.append(difficultyLabel, branchLabel);
  const sourceGroup = ui('div', 'work-source-picker');
  sourceGroup.append(ui('h4', '', 'Fuente de apoyo'), ui('p', 'work-note', 'Elige un fragmento si el tema procede de un DOCX. Puedes dejarlo vacío para completar la fuente más adelante.'));
  const documentPicker = ui('select', 'work-select');
  const noDocument = ui('option', '', 'Sin documento'); noDocument.value = ''; documentPicker.append(noDocument);
  const fragmentPicker = ui('select', 'work-select');
  const noFragment = ui('option', '', 'Sin fragmento'); noFragment.value = ''; fragmentPicker.append(noFragment);
  sourceGroup.append(add(ui('label', 'work-field'), ui('span', '', 'Documento'), documentPicker),
    add(ui('label', 'work-field'), ui('span', '', 'Fragmento'), fragmentPicker));
  form.append(sourceGroup);
  const feedback = ui('p', 'work-note');
  const save = ui('button', 'work-primary', 'Guardar tema en el mapa'); save.type = 'submit';
  form.append(save, feedback);
  workspaceBody.append(form);
  try {
    const documents = (await api('/api/documents')).documents;
    if (version !== workspace.request) return;
    for (const doc of documents) {
      const option = ui('option', '', doc.filename); option.value = doc.id; documentPicker.append(option);
    }
    documentPicker.value = documents.some(doc => doc.id === workspace.documentId) ? workspace.documentId : '';
    async function loadFragments() {
      const documentId = documentPicker.value;
      const emptyFragment = ui('option', '', 'Sin fragmento'); emptyFragment.value = '';
      fragmentPicker.replaceChildren(emptyFragment);
      fragmentPicker.disabled = !documentId;
      if (!documentId) return;
      try {
        const fragments = (await api(`/api/documents/${safePath(documentId)}/fragments`)).fragments;
        if (version !== workspace.request || documentId !== documentPicker.value) return;
        for (const fragment of fragments.filter(item => item.kind !== 'image')) {
          const preview = fragment.content.replace(/\s+/g, ' ').slice(0, 100);
          const option = ui('option', '', `${fragment.ordinal + 1}. ${preview || fragment.kind}`);
          option.value = fragment.id; fragmentPicker.append(option);
        }
      } catch (error) { feedback.textContent = `No se cargaron los fragmentos: ${errorText(error)}`; }
    }
    documentPicker.addEventListener('change', loadFragments);
    await loadFragments();
  } catch (error) { feedback.textContent = `No se cargaron los documentos: ${errorText(error)}`; }
  form.addEventListener('submit', async event => {
    event.preventDefault(); save.disabled = true; feedback.textContent = 'Guardando tema…';
    try {
      const topic = await post('/api/topics', {
        title: title.control.value.trim(), summary: summary.control.value.trim(),
        explanation: explanation.control.value.trim(), conditions: conditions.control.value.trim(),
        difficulty: difficulty.value, review_status: 'proposed',
        branch_id: branch.value || null, source_fragment_id: fragmentPicker.value || null,
      });
      workspace.topicId = topic.id; workspace.creating = false;
      await loadTree(); setView('reader');
      note(workspaceBody, 'Tema guardado. Puedes corregirlo y completar sus relaciones.', 'success');
    } catch (error) { feedback.textContent = `No se guardó: ${errorText(error)}`; feedback.classList.add('error'); }
    finally { save.disabled = false; }
  });
}

async function renderReader() {
  if (workspace.creating) return renderCreateTopic();
  heading('Leer un tema', 'Consulta primero el contenido y sus fuentes. Puedes abrir la edición cuando necesites corregirlo.');
  workspaceBody.append(button('＋ Crear tema', () => { workspace.creating = true; setView('reader'); }, 'work-primary'));
  const picker = ui('select', 'work-select');
  picker.append(ui('option', '', 'Selecciona un tema'));
  for (const topic of state.topics) {
    const option = ui('option', '', topic.title); option.value = topic.id; picker.append(option);
  }
  picker.value = workspace.topicId || '';
  picker.addEventListener('change', () => { workspace.topicId = picker.value || null; workspace.editing = false; renderReader(); });
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
    if (!workspace.editing) {
      const reading = ui('article', 'topic-reading');
      reading.append(ui('div', 'eyebrow', 'TEMA GUARDADO'), ui('h4', '', topic.title));
      const summary = ui('p', 'topic-reading-summary', topic.summary || 'Este tema aún no tiene una idea principal.');
      reading.append(summary);
      if (topic.explanation) reading.append(ui('h5', '', 'Explicación'), ui('p', 'work-source-text', topic.explanation));
      if (topic.conditions) reading.append(ui('h5', '', 'Cuándo se aplica'), ui('p', 'work-source-text', topic.conditions));
      if (topic.tags.length) reading.append(ui('p', 'topic-reading-tags', `Etiquetas: ${topic.tags.join(' · ')}`));
      reading.append(ui('p', 'subtle', `Dificultad: ${{ basic: 'básico', intermediate: 'intermedio', advanced: 'avanzado' }[topic.difficulty] || topic.difficulty} · Revisión: ${topic.review_status}`));
      area.append(reading, button('Editar este tema', () => { workspace.editing = true; renderReader(); }, 'work-primary'));
    } else {
    area.append(button('← Volver a lectura', () => { workspace.editing = false; renderReader(); }, 'work-quiet'));
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
        workspace.editing = false;
        await renderReader();
        note(workspaceBody, 'Cambios guardados.', 'success');
      } catch (error) { feedback.textContent = `No se guardó: ${errorText(error)}`; feedback.classList.add('error'); }
      finally { save.disabled = false; }
    });
    area.append(form);
    }
    const evidence = ui('div', 'work-list');
    evidence.append(ui('h4', '', 'Referencias y revisión'));
    area.append(evidence);
    if (!topic.evidence.length) note(evidence, 'Este tema no tiene fragmentos fuente asociados.');
    for (const [index, item] of topic.evidence.entries()) {
      const role = { supports: 'apoya', context: 'da contexto', contradicts: 'contradice' }[item.role] || item.role;
      evidence.append(button(`Abrir fuente ${index + 1} · ${role}`, () => openSourceFragment(item.fragment_id)));
    }
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
    else note(list, `${fragments.length} ${fragments.length === 1 ? 'fragmento' : 'fragmentos'} conservados en el orden del documento.`);
    for (const fragment of fragments) {
      const card = ui('article', 'work-card'); card.id = `fragment-${fragment.id}`;
      const kind = { paragraph: 'Párrafo', table: 'Tabla', image: 'Imagen' }[fragment.kind] || fragment.kind;
      card.append(ui('strong', '', `${fragment.ordinal + 1}. ${kind}`),
        ui('p', 'source-locator', `Referencia: ${fragment.locator}`));
      if (fragment.kind === 'table') {
        try {
          const rows = JSON.parse(fragment.content);
          if (!Array.isArray(rows)) throw new Error('Invalid table');
          const table = ui('table', 'source-table');
          for (const row of rows) {
            if (!Array.isArray(row)) throw new Error('Invalid table row');
            const tr = ui('tr');
            for (const cell of row) tr.append(ui('td', '', String(cell)));
            table.append(tr);
          }
          const tableScroll = ui('div', 'source-table-scroll'); tableScroll.append(table); card.append(tableScroll);
        } catch { card.append(ui('p', 'work-source-text', fragment.content)); }
      } else if (fragment.content) card.append(ui('p', 'work-source-text', fragment.content));
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

async function renderSearch() {
  const version = workspace.request;
  heading('Buscar en tu teoría', 'La respuesta generada necesita un modelo local y debe citar fragmentos de tus documentos.');
  try {
    const health = await api('/api/health');
    if (version !== workspace.request) return;
    workspace.modelConfigured = Boolean(health.model_configured);
    if (!workspace.modelConfigured) {
      note(workspaceBody, 'La búsqueda con respuestas todavía no está disponible. Mientras tanto, puedes recorrer el árbol y leer los fragmentos originales.');
      workspaceBody.append(button('Ver fuentes originales', () => setView('sources'), 'work-primary'));
      return;
    }
  } catch {
    if (version !== workspace.request) return;
    note(workspaceBody, 'No se pudo consultar el estado del modelo local. Comprueba que el servidor esté disponible.', 'error');
    return;
  }
  const form = ui('form', 'work-form'); const query = ui('input');
  query.type = 'search'; query.placeholder = 'Ej. BB vs BTN en flop Axx'; query.required = true;
  const submit = ui('button', 'work-primary', 'Buscar'); submit.type = 'submit';
  const result = ui('div', 'work-list'); form.append(query, submit); workspaceBody.append(form, result);
  form.addEventListener('submit', async event => {
    event.preventDefault(); submit.disabled = true;
    result.replaceChildren(ui('p', 'work-note', 'Buscando en la biblioteca…'));
    try { showSearchResult(result, await post('/api/search', { query: query.value })); }
    catch (error) {
      const message = /POKER_ROOTS_MODEL|local model/i.test(errorText(error)) ?
        'El modelo local no está disponible. Configura POKER_ROOTS_MODEL y vuelve a buscar.' :
        `La búsqueda falló: ${errorText(error)}. Puedes volver a intentarlo.`;
      result.replaceChildren(ui('p', 'work-note error', message));
    }
    finally { submit.disabled = false; }
  });
}
function showSearchResult(area, data) {
  area.replaceChildren();
  if (data.status === 'answered') add(area, ui('h4', '', 'Respuesta con fuentes'), ui('p', 'work-answer', data.answer));
  else if (data.status === 'clarification') note(area, data.question || 'La pregunta necesita una aclaración. Añade la condición que falta y vuelve a buscar.');
  else if (data.status === 'empty_index') note(area, 'Todavía no hay contenido indexado. Importa un DOCX para empezar a buscar.');
  else note(area, 'No hay evidencia suficiente para responder con seguridad. Prueba otra consulta o importa una fuente que cubra el caso.');
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
      if (!data.steps.length) note(result, 'No hay una ruta respaldada por fuentes para este objetivo. Importa teoría relacionada o prueba un objetivo más concreto.');
      data.steps.forEach((step, index) => {
        const card = ui('article', 'work-card');
        const reason = step.reason === 'Matches the study goal' ? 'Coincide con el objetivo de estudio' :
          step.reason === 'Available basic topic for a beginner path' ? 'Tema básico disponible' :
          step.reason.startsWith('Prerequisite for ') ? `Prerrequisito de ${step.reason.slice(17)}` : step.reason;
        card.append(ui('strong', '', `${index + 1}. ${step.title}`), ui('p', '', reason), topicLink(step.topic_id, 'Abrir tema'));
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

workspaceTabs.forEach(tab => tab.addEventListener('click', () => {
  workspace.creating = false;
  setView(tab.dataset.view);
}));
navigationButtons.forEach(item => item.addEventListener('click', () => {
  const target = item.dataset.nav;
  if (target === 'map') {
    setNavigation('map');
    document.querySelector('.map-shell').scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  workspace.creating = false;
  setView(target);
  document.querySelector('.workspace').scrollIntoView({ behavior: 'smooth', block: 'start' });
}));
document.querySelectorAll('[data-quick]').forEach(action => action.addEventListener('click', () => {
  if (action.dataset.quick === 'map') {
    setNavigation('map');
    document.querySelector('.map-shell').scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }
  if (action.dataset.quick === 'create') workspace.creating = true;
  setView(action.dataset.quick === 'create' ? 'reader' : 'import');
  document.querySelector('.workspace').scrollIntoView({ behavior: 'smooth', block: 'start' });
}));
setView('import');
setNavigation('map');
