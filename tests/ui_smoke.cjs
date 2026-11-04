const assert = require('node:assert/strict');
const fs = require('node:fs');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const readline = require('node:readline');
const path = require('node:path');
const { chromium } = require('playwright-core');

(async () => {
  const root = path.resolve(__dirname, '..');
  const fixtureProcess = spawn(process.env.PYTHON || 'python', ['tests/ui_fixture_server.py'], {
    cwd: root, stdio: ['pipe', 'pipe', 'inherit'],
  });
  const lines = readline.createInterface({ input: fixtureProcess.stdout });
  const [line] = await once(lines, 'line');
  const fixture = JSON.parse(line);
  const base = fixture.url;
  const executablePath = process.env.POKER_ROOTS_BROWSER_PATH ||
    (process.platform === 'win32' ? 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe' : undefined);
  let browser;
  try {
    browser = await chromium.launch({
      executablePath, headless: true,
      args: ['--no-first-run', '--no-proxy-server', '--proxy-server=direct://', '--proxy-bypass-list=*'],
    });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    await page.goto(base, { waitUntil: 'domcontentloaded', timeout: 12000 });
    const tree = page.locator('#treeRegion');
    await page.getByRole('button', { name: 'Flop Axx avanzado' }).waitFor();
    await page.waitForFunction(() => document.querySelectorAll('.tree-connectors path').length === 7);
    const fullTreeHeight = await tree.evaluate(node => node.clientHeight);
    const mapWidth = await page.locator('.map-shell').evaluate(node => node.getBoundingClientRect().width);
    assert.equal(mapWidth, 1222);
    const menu = page.getByRole('navigation', { name: 'Secciones' });
    assert.equal(await menu.getByRole('button').count(), 7);
    await menu.getByRole('button', { name: 'Buscar' }).click();
    await page.getByRole('heading', { name: 'Buscar en tu teoría' }).waitFor();
    assert.equal(await menu.getByRole('button', { name: 'Buscar' }).getAttribute('aria-current'), 'page');
    await menu.getByRole('button', { name: 'Mapa' }).click();
    assert.equal(await menu.getByRole('button', { name: 'Mapa' }).getAttribute('aria-current'), 'page');
    assert.equal(await page.locator('.map-shell').evaluate(node => getComputedStyle(node).borderTopWidth), '0px');
    const fundamentals = page.getByRole('button', { name: 'Fundamentos', exact: true });
    await fundamentals.click();
    assert.equal(await page.locator('#detailTitle').innerText(), 'Fundamentos');
    assert.equal(await fundamentals.getAttribute('aria-expanded'), null);
    const preflop = page.getByRole('button', { name: 'Preflop', exact: true });
    await preflop.click();
    assert.equal(await page.locator('#detailTitle').innerText(), 'Preflop');
    await page.getByRole('button', { name: /^Posiciones/ }).first().waitFor({ state: 'visible' });
    assert.equal(await page.locator('.tree-connectors path').count(), 7);
    for (const title of ['Posiciones', 'Juego de ciegas']) {
      if (title === 'Juego de ciegas') await page.getByRole('button', { name: 'Postflop', exact: true }).click();
      await page.getByRole('button', { name: new RegExp(`^${title}`) }).first().click();
      assert.equal(await page.locator('#detailTitle').innerText(), title);
    }
    await page.getByRole('button', { name: 'Leer tema completo y fuentes' }).click();
    await page.getByRole('heading', { name: 'Leer un tema' }).waitFor();
    await page.getByRole('button', { name: 'Abrir fuente 1' }).click();
    await page.getByRole('heading', { name: 'Fuentes originales' }).waitFor();
    await page.getByText('BTN y BB', { exact: true }).first().waitFor();
    await page.getByRole('button', { name: 'Flop Axx', exact: true }).click();
    await page.getByRole('button', { name: 'Flop Axx avanzado' }).click();
    await page.waitForFunction(() => document.querySelectorAll('.tree-connectors path').length === 7);
    const preflopBounds = await preflop.boundingBox();
    const positionsBounds = await page.getByRole('button', { name: /^Posiciones/ }).first().boundingBox();
    assert.ok(positionsBounds.y > preflopBounds.y && positionsBounds.x < preflopBounds.x);
    await page.getByText('Flop Axx avanzado', { exact: true }).first().waitFor();
    assert.equal(await page.locator('#sceneNumber').innerText(), '04');
    assert.equal(await page.locator('#detailTitle').innerText(), 'Flop Axx avanzado');
    assert.ok(await page.getByText('Juego de ciegas', { exact: true }).count());

    await page.setViewportSize({ width: 390, height: 844 });
    const metrics = await page.evaluate(() => ({
      innerWidth, scrollWidth: document.documentElement.scrollWidth,
      tabScrollWidth: document.querySelector('.workspace-tabs').scrollWidth,
      tabClientWidth: document.querySelector('.workspace-tabs').clientWidth,
    }));
    assert.equal(metrics.innerWidth, 390);
    assert.ok(metrics.scrollWidth <= 390, JSON.stringify(metrics));
    await page.getByText('Todas las ramas están visibles. Elige un concepto para ver sus detalles.').waitFor();
    const treeWidth = await tree.evaluate(node => ({ client: node.clientWidth, scroll: node.scrollWidth }));
    assert.ok(treeWidth.scroll <= treeWidth.client + 1, JSON.stringify(treeWidth));
    assert.equal(await page.locator('.map-shell').evaluate(node => node.getBoundingClientRect().width), 330);
    assert.equal(await page.locator('.sidebar').isVisible(), true);
    await menu.getByRole('button', { name: 'Fuentes' }).click();
    assert.equal(await page.getByRole('tab', { name: 'Fuentes' }).getAttribute('aria-selected'), 'true');
    await menu.getByRole('button', { name: 'Mapa' }).click();
    await page.waitForFunction(() => {
      const svg = document.querySelector('.tree-connectors');
      return svg && Math.abs(svg.viewBox.baseVal.width - svg.parentElement.clientWidth) < 1;
    });
    const mobileTreeHeight = await tree.evaluate(node => node.clientHeight);
    assert.ok(await tree.evaluate(node => node.scrollHeight <= node.clientHeight + 1));
    const chip = await page.getByRole('button', { name: 'Flop Axx avanzado' }).boundingBox();
    const region = await tree.boundingBox();
    assert.ok(chip.x >= region.x && chip.x + chip.width <= region.x + region.width + 1);
    await page.getByRole('tab', { name: 'Leer y editar' }).click();
    await page.locator('.work-select').selectOption({ label: 'Flop Axx avanzado' });
    await page.getByRole('button', { name: 'Editar este tema' }).click();
    await page.getByRole('button', { name: 'Guardar cambios' }).waitFor();
    const summary = page.locator('.work-field').filter({ hasText: 'Resumen' }).locator('textarea');
    await summary.fill('Resumen móvil corregido');
    await page.getByRole('button', { name: 'Guardar cambios' }).click();
    await page.getByText('Cambios guardados.').waitFor();
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: 'Leer y editar' }).click();
    await page.locator('.work-select').selectOption({ label: 'Flop Axx avanzado' });
    await page.getByRole('button', { name: 'Editar este tema' }).click();
    await page.locator('.work-field').filter({ hasText: 'Resumen' }).locator('textarea')
      .waitFor({ state: 'visible' });
    assert.equal(await page.locator('.work-field').filter({ hasText: 'Resumen' }).locator('textarea').inputValue(),
      'Resumen móvil corregido');
    await page.getByRole('button', { name: 'Fundamentos', exact: true }).click();
    await page.getByRole('button', { name: 'Preflop', exact: true }).click();
    await page.getByRole('button', { name: 'Postflop', exact: true }).click();
    await page.getByRole('button', { name: 'Flop Axx', exact: true }).click();
    await page.getByRole('button', { name: 'Flop Axx avanzado' }).click();
    await page.getByRole('tab', { name: 'Buscar' }).click();
    await page.getByPlaceholder('Ej. BB vs BTN en flop Axx').fill('BTN y BB');
    await page.locator('.workspace').getByRole('button', { name: 'Buscar', exact: true }).click();
    await page.getByText('Respuesta con fuentes').waitFor();
    const after = await page.evaluate(() => document.documentElement.scrollWidth);
    assert.ok(after <= 390, `mobile search overflow ${after}`);
    const beforeImport = Number((await page.locator('#treeCount').innerText()).match(/(\d+) temas/)[1]);
    await page.getByRole('tab', { name: 'Importar' }).click();
    const filename = `leccion-${Date.now()}.docx`;
    await page.locator('input[type=file]').setInputFiles({
      name: filename, mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      buffer: Buffer.concat([fs.readFileSync(fixture.fixture), Buffer.from(filename)]),
    });
    await page.getByRole('button', { name: 'Importar documento' }).click();
    const importedCard = page.locator('.work-card').filter({ hasText: filename });
    await importedCard.getByText('Completado', { exact: true }).waitFor({ timeout: 15000 });
    await importedCard.getByRole('button', { name: 'Ver fuentes' }).click();
    await page.locator('.source-table td').getByText('BTN').waitFor();
    await page.getByRole('tab', { name: 'Importar' }).click();
    const uploaded = (await (await page.request.get(new URL('/api/documents', base).href)).json()).documents
      .find(doc => doc.filename === filename);
    assert.ok(uploaded);
    const linked = await (await page.request.get(new URL(`/api/documents/${uploaded.id}/topics`, base).href)).json();
    assert.equal(linked.topics.length, 2);
    assert.match(await page.locator('#treeCount').innerText(), new RegExp(`${beforeImport + 2} temas`));
    await importedCard.getByRole('button', { name: 'Ver temas' }).click();
    await page.getByRole('heading', { name: 'Leer un tema' }).waitFor();

    await page.locator('[data-quick="create"]').click();
    await page.getByRole('heading', { name: 'Crear un tema' }).waitFor();
    await page.getByLabel('Título del tema').fill('Tema creado a mano');
    await page.getByLabel('Idea principal').fill('Posiciones del documento');
    await page.getByLabel('Lugar en el mapa').selectOption({ label: 'Preflop' });
    const sourcePickers = page.locator('.work-source-picker select');
    await sourcePickers.first().selectOption({ label: 'lesson.docx' });
    await page.waitForFunction(() => document.querySelectorAll('.work-source-picker select')[1].options.length > 1);
    await sourcePickers.nth(1).selectOption({ index: 1 });
    await page.getByRole('button', { name: 'Guardar tema en el mapa' }).click();
    await page.getByText('Tema guardado. Puedes corregirlo y completar sus relaciones.').waitFor();
    assert.match(await page.locator('#treeCount').innerText(), new RegExp(`${beforeImport + 3} temas`));
    const manual = (await (await page.request.get(new URL('/api/topics', base).href)).json()).topics
      .find(topic => topic.title === 'Tema creado a mano');
    assert.ok(manual);
    assert.equal(manual.placements.length, 1);
    assert.equal(manual.evidence.length, 1);

    const longPage = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const longBranch = 'Escenarios de práctica con un nombre muy largo para la biblioteca';
    const longTopic = 'Comparación detallada de decisiones en el flop SupercalifragilisticoSinEspacios';
    await longPage.route('**/api/tree', route => route.fulfill({ json: {
      branches: [{ id: 'long-branch', name: longBranch, parent_id: null, sort_order: 0 }],
      topics: [{ id: 'long-topic', title: longTopic, placements: ['long-branch'], difficulty: 'intermediate',
        review_status: 'proposed', prerequisites: [], summary: 'Tema de prueba' }],
    } }));
    await longPage.goto(base, { waitUntil: 'domcontentloaded' });
    await longPage.getByRole('button', { name: longBranch }).click();
    const longTree = await longPage.locator('#treeRegion').evaluate(node => ({ width: node.clientWidth, scroll: node.scrollWidth }));
    assert.ok(longTree.scroll <= longTree.width + 1, JSON.stringify(longTree));
    assert.ok(await longPage.getByRole('button', { name: longTopic }).evaluate(node => node.clientHeight > 48));
    assert.ok(await longPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await longPage.close();

    const empty = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await empty.route('**/api/tree', async route => {
      await new Promise(resolve => setTimeout(resolve, 250));
      await route.fulfill({ json: { branches: [], topics: [] } });
    });
    await empty.route('**/api/documents', route => route.fulfill({ json: { documents: [{
      id: 'failed-test', filename: 'fallido.docx', state: 'failed', error: 'DOCX invalid', warnings: [],
    }] } }));
    await empty.route('**/api/search', route => route.fulfill({ json: {
      status: 'empty_index', query: 'sin fuente', topics: [], sources: [], retrieval_warnings: [],
    } }));
    await empty.goto(base, { waitUntil: 'domcontentloaded' });
    await empty.getByText('Cargando tu biblioteca…').waitFor();
    await empty.getByText('Tu biblioteca aún no tiene temas.').waitFor();
    await empty.getByText('Falló', { exact: true }).waitFor();
    await empty.getByRole('button', { name: 'Reintentar' }).waitFor();
    await empty.getByRole('tab', { name: 'Buscar' }).click();
    await empty.getByPlaceholder('Ej. BB vs BTN en flop Axx').fill('sin fuente');
    await empty.locator('.workspace').getByRole('button', { name: 'Buscar', exact: true }).click();
    await empty.getByText('Todavía no hay contenido indexado. Importa un DOCX para empezar a buscar.').waitFor();
    await empty.route('**/api/health', route => route.fulfill({ json: { status: 'ok', model_configured: false } }));
    await empty.getByRole('tab', { name: 'Importar' }).click();
    await empty.getByText('Modo manual: tus documentos y fuentes están disponibles.').waitFor();
    await empty.getByRole('tab', { name: 'Buscar' }).click();
    await empty.getByText('La búsqueda con respuestas todavía no está disponible.').waitFor();
    await empty.unroute('**/api/tree');
    await empty.route('**/api/tree', route => route.abort());
    await empty.reload({ waitUntil: 'domcontentloaded' });
    await empty.getByText('No se pudo cargar la biblioteca local. Comprueba que el servidor esté disponible.').waitFor();
    await empty.close();
    console.log(JSON.stringify({ result: 'PASS', metrics, treeWidth, fullTreeHeight, mobileTreeHeight, mapWidth, searchScrollWidth: after,
      states: ['loading', 'empty', 'failed_import', 'empty_index', 'model_unavailable', 'tree_error'],
      importedTopics: linked.topics.length, manualTopicWithSource: true }));
  } finally {
    if (browser) await browser.close();
    fixtureProcess.stdin.end('\n');
    await once(fixtureProcess, 'exit');
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
