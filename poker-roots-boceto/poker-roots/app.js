const scenes = [
  { title: 'La timba del barrio', subtitle: 'El origen', text: 'La raíz de tu biblioteca y sus primeras ramas.' },
  { title: 'Casino de barrio', subtitle: 'Las ramas', text: 'Cada rama organiza una forma de recorrer tus temas.' },
  { title: 'Gran casino', subtitle: 'Los temas', text: 'Abre un tema para ver sus relaciones y volver a su lugar en el mapa.' },
  { title: 'Royal Privé', subtitle: 'Más profundidad', text: 'Las ramas más profundas conservan las mismas fuentes y relaciones.' },
];

const state = { branches: [], topics: [], selected: { kind: 'root' }, selectionVersion: 0 };
const region = document.querySelector('#treeRegion');
const reloadButton = document.querySelector('#reloadButton');

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setScene(depth) {
  const index = Math.max(0, Math.min(3, depth));
  const scene = scenes[index];
  document.querySelector('#background').style.backgroundImage = `url('/assets/drawn-${index}.jpg')`;
  document.querySelector('#sceneNumber').textContent = `0${index + 1}`;
  document.querySelector('#sceneTitle').textContent = scene.title;
  document.querySelector('#sceneText').textContent = scene.text;
}

function message(text, action) {
  const box = element('div', 'tree-message');
  box.setAttribute('role', 'status');
  box.append(element('p', '', text));
  if (action) {
    const button = element('button', 'text-button', 'Reintentar');
    button.type = 'button';
    button.addEventListener('click', action);
    box.append(button);
  }
  region.replaceChildren(box);
}

function nodeButton(label, symbol, kind, depth, onClick) {
  const button = element('button', `chip-node ${kind}`);
  button.type = 'button';
  button.setAttribute('aria-label', label);
  button.append(element('span', 'chip-symbol', symbol), element('span', 'chip-title', label));
  button.addEventListener('click', onClick);
  button.dataset.depth = String(depth);
  return button;
}

function branchDepth(branchId) {
  let depth = 1;
  let current = state.branches.find(branch => branch.id === branchId);
  while (current && current.parent_id) {
    depth += 1;
    current = state.branches.find(branch => branch.id === current.parent_id);
  }
  return depth;
}

let treeConnectorFrame = 0;
function scheduleTreeConnectors() {
  cancelAnimationFrame(treeConnectorFrame);
  treeConnectorFrame = requestAnimationFrame(drawTreeConnectors);
}

function drawTreeConnectors() {
  const tree = region.querySelector('.tree-content');
  if (!tree) return;
  let svg = tree.querySelector(':scope > .tree-connectors');
  if (!svg) {
    svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('tree-connectors');
    svg.setAttribute('aria-hidden', 'true');
    tree.prepend(svg);
  }
  const bounds = tree.getBoundingClientRect();
  svg.setAttribute('viewBox', `0 0 ${bounds.width} ${bounds.height}`);
  svg.replaceChildren();
  for (const item of tree.querySelectorAll('.tree-item')) {
    const child = item.querySelector(':scope > .chip-node');
    if (!child || !child.getClientRects().length) continue;
    const parentItem = item.parentElement.closest('.branch-item');
    const parent = parentItem?.querySelector(':scope > .chip-node') || tree.querySelector(':scope > .chip-node.root');
    if (!parent || !parent.getClientRects().length) continue;
    const from = parent.getBoundingClientRect();
    const to = child.getBoundingClientRect();
    const x1 = from.left + from.width / 2 - bounds.left;
    const y1 = from.bottom - bounds.top;
    const x2 = to.left + to.width / 2 - bounds.left;
    const y2 = to.top - bounds.top;
    const middle = y1 + (y2 - y1) / 2;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M ${x1} ${y1} C ${x1} ${middle}, ${x2} ${middle}, ${x2} ${y2}`);
    svg.append(path);
  }
}

window.addEventListener('resize', scheduleTreeConnectors);

function renderTree() {
  const branches = state.branches;
  const topics = state.topics;
  const children = new Map();
  const topicsByBranch = new Map();
  const knownBranches = new Set(branches.map(branch => branch.id));
  const sortBranches = (left, right) => (left.sort_order - right.sort_order) || left.name.localeCompare(right.name, 'es');
  branches.forEach(branch => {
    const parent = branch.parent_id && knownBranches.has(branch.parent_id) ? branch.parent_id : 'root';
    if (!children.has(parent)) children.set(parent, []);
    children.get(parent).push(branch);
  });
  children.forEach(group => group.sort(sortBranches));
  topics.forEach(topic => {
    const placements = topic.placements.filter(id => knownBranches.has(id));
    for (const branchId of placements.length ? placements : ['unplaced']) {
      if (!topicsByBranch.has(branchId)) topicsByBranch.set(branchId, []);
      topicsByBranch.get(branchId).push(topic);
    }
  });

  const tree = element('div', 'tree-content');
  const root = nodeButton('Tu biblioteca', '♠', 'root', 0, () => selectRoot());
  root.dataset.kind = 'root';
  tree.append(root);

  function makeTopic(topic, branchId, depth) {
    const item = element('li', 'tree-item topic-item');
    const button = nodeButton(topic.title, '♠', 'topic', depth, () => selectTopic(topic.id, branchId));
    button.dataset.topicId = topic.id;
    button.dataset.branchId = branchId;
    button.append(element('span', 'chip-badge',
      { basic: 'básico', intermediate: 'intermedio', advanced: 'avanzado' }[topic.difficulty] || topic.difficulty));
    item.append(button);
    return item;
  }

  function makeBranch(branch, depth) {
    const item = element('li', 'tree-item branch-item');
    const descendants = element('ul', 'tree-children');
    descendants.id = `branch-children-${branch.id}`;
    const button = nodeButton(branch.name, '♧', 'branch', depth, () => selectBranch(branch.id));
    button.dataset.branchId = branch.id;
    button.dataset.kind = 'branch';
    item.append(button);
    for (const topic of topicsByBranch.get(branch.id) || []) descendants.append(makeTopic(topic, branch.id, depth + 1));
    for (const child of children.get(branch.id) || []) descendants.append(makeBranch(child, depth + 1));
    if (descendants.children.length) {
      item.classList.add('expanded');
      item.append(descendants);
    }
    return item;
  }

  const roots = element('ul', 'tree-children tree-first-level');
  for (const branch of children.get('root') || []) roots.append(makeBranch(branch, 1));
  if (topicsByBranch.has('unplaced')) {
    const unplaced = element('li', 'tree-item branch-item');
    const label = element('div', 'unplaced-heading', 'Sin rama asignada');
    unplaced.append(label);
    const group = element('ul', 'tree-children');
    for (const topic of topicsByBranch.get('unplaced')) group.append(makeTopic(topic, 'unplaced', 1));
    unplaced.append(group);
    roots.append(unplaced);
  }
  if (roots.children.length) tree.append(roots);
  if (!topics.length) {
    const empty = element('div', 'empty-state');
    empty.append(element('strong', '', 'Tu biblioteca aún no tiene temas.'),
      element('p', '', 'Importa un documento para empezar a construir el mapa.'));
    tree.append(empty);
  }
  region.replaceChildren(tree);
  scheduleTreeConnectors();
  document.querySelector('#treeCount').textContent = `${branches.length} ramas · ${topics.length} temas`;
}

function markSelected() {
  region.querySelectorAll('.chip-node').forEach(button => {
    const { kind, topicId, branchId } = button.dataset;
    const selected = (kind === 'root' && state.selected.kind === 'root') ||
      (kind === 'branch' && state.selected.kind === 'branch' && branchId === state.selected.id) ||
      (topicId && state.selected.kind === 'topic' && topicId === state.selected.id && branchId === state.selected.branchId);
    button.classList.toggle('selected', Boolean(selected));
    button.setAttribute('aria-pressed', selected ? 'true' : 'false');
  });
}

function detailBase(path, title, description, depth) {
  document.querySelector('#path').textContent = path;
  document.querySelector('#detailTitle').textContent = title;
  document.querySelector('#detailText').textContent = description;
  document.querySelector('#detailMeta').replaceChildren();
  document.querySelector('#detailLinks').replaceChildren();
  setScene(depth);
  markSelected();
}

function selectRoot() {
  state.selectionVersion += 1;
  state.selected = { kind: 'root' };
  detailBase('TU BIBLIOTECA', 'Tu juego echa raíces',
    state.topics.length ? 'Elige una rama o un tema para recorrer tu biblioteca guardada.' :
      'Aún no hay temas en el mapa. Importa un documento para comenzar.', 0);
}

function selectBranch(branchId) {
  const branch = state.branches.find(item => item.id === branchId);
  if (!branch) return;
  state.selectionVersion += 1;
  state.selected = { kind: 'branch', id: branchId };
  const direct = state.topics.filter(topic => topic.placements.includes(branchId)).length;
  detailBase('RAMA DEL ÁRBOL', branch.name,
    direct ? `${direct} ${direct === 1 ? 'tema aparece' : 'temas aparecen'} directamente en esta rama.` :
      'Esta rama aún no tiene temas asignados directamente.', branchDepth(branchId));
}

function linkButton(text, onClick) {
  const button = element('button', 'relation-link', text);
  button.type = 'button';
  button.addEventListener('click', onClick);
  return button;
}

function focusTopic(topicId, branchId) {
  const topic = state.topics.find(item => item.id === topicId);
  if (!topic) return;
  const placement = branchId || topic.placements[0] || 'unplaced';
  selectTopic(topicId, placement);
  const button = [...region.querySelectorAll('[data-topic-id]')]
    .find(item => item.dataset.topicId === topicId && item.dataset.branchId === placement);
  button?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  button?.focus({ preventScroll: true });
}

async function selectTopic(topicId, branchId) {
  const topic = state.topics.find(item => item.id === topicId);
  if (!topic) return;
  const version = ++state.selectionVersion;
  state.selected = { kind: 'topic', id: topicId, branchId };
  detailBase('TEMA GUARDADO', topic.title,
    topic.summary || topic.explanation || 'Este tema aún no tiene resumen.',
    branchId === 'unplaced' ? 1 : branchDepth(branchId) + 1);

  const meta = document.querySelector('#detailMeta');
  const difficulty = { basic: 'básico', intermediate: 'intermedio', advanced: 'avanzado' }[topic.difficulty] || topic.difficulty;
  const review = { proposed: 'propuesto', reviewed: 'revisado', approved: 'aprobado' }[topic.review_status] || topic.review_status;
  meta.append(element('span', 'meta-pill', `Dificultad: ${difficulty}`),
    element('span', 'meta-pill', `Revisión: ${review}`));
  if (topic.conditions) meta.append(element('p', 'condition', `Condiciones: ${topic.conditions}`));

  const links = document.querySelector('#detailLinks');
  links.append(linkButton('Leer tema completo y fuentes →', () => openTopic(topicId)));
  if (topic.prerequisites.length) {
    const group = element('div', 'relation-group');
    group.append(element('strong', '', 'Antes de este tema'));
    for (const prerequisiteId of topic.prerequisites) {
      const prerequisite = state.topics.find(item => item.id === prerequisiteId);
      if (prerequisite) group.append(linkButton(prerequisite.title, () => focusTopic(prerequisiteId)));
    }
    links.append(group);
  }

  const locationGroup = element('div', 'relation-group');
  locationGroup.append(element('strong', '', 'Volver a su lugar en el mapa'));
  links.append(locationGroup);
  if (branchId === 'unplaced') locationGroup.append(element('span', 'subtle', 'Este tema no tiene rama asignada.'));
  try {
    const response = await fetch(`/api/topics/${encodeURIComponent(topicId)}/locations`, { cache: 'no-store' });
    if (!response.ok) throw new Error('No se pudieron cargar las ubicaciones.');
    const data = await response.json();
    if (version !== state.selectionVersion) return;
    for (const location of data.locations) {
      const label = location.path.map(part => part.name).join(' / ');
      locationGroup.append(linkButton(label, () => focusTopic(topicId, location.branch_id)));
    }
  } catch {
    if (version === state.selectionVersion) locationGroup.append(element('span', 'subtle', 'No se pudieron cargar las ubicaciones. Actualiza el árbol.'));
  }
}

async function loadTree() {
  reloadButton.disabled = true;
  message('Cargando tu biblioteca…');
  try {
    const response = await fetch('/api/tree', { cache: 'no-store' });
    if (!response.ok) throw new Error('No se pudo cargar el árbol.');
    const data = await response.json();
    if (!Array.isArray(data.branches) || !Array.isArray(data.topics)) throw new Error('El árbol recibido no es válido.');
    state.branches = data.branches;
    state.topics = data.topics;
    renderTree();
    const prior = state.selected;
    if (prior.kind === 'topic' && state.topics.some(topic => topic.id === prior.id)) {
      const topic = state.topics.find(item => item.id === prior.id);
      focusTopic(prior.id, topic.placements.includes(prior.branchId) ? prior.branchId : topic.placements[0] || 'unplaced');
    } else if (prior.kind === 'branch' && state.branches.some(branch => branch.id === prior.id)) {
      selectBranch(prior.id);
    } else {
      selectRoot();
    }
  } catch {
    message('No se pudo cargar la biblioteca local. Comprueba que el servidor esté disponible.', loadTree);
    document.querySelector('#treeCount').textContent = 'Sin conexión';
    state.selectionVersion += 1;
    state.selected = { kind: 'root' };
    detailBase('SIN CONEXIÓN', 'No se pudo abrir el mapa',
      'Vuelve a intentarlo cuando la biblioteca local esté disponible.', 0);
  } finally {
    reloadButton.disabled = false;
  }
}

document.querySelector('#rootButton').addEventListener('click', selectRoot);
reloadButton.addEventListener('click', loadTree);
loadTree();
