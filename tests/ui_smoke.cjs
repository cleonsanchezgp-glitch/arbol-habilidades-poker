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
    for (const title of ['Posiciones', 'Juego de ciegas']) {
      await page.getByRole('button', { name: new RegExp(`^${title}`) }).first().click();
      assert.equal(await page.locator('#detailTitle').innerText(), title);
    }
    await page.getByRole('button', { name: 'Flop Axx avanzado' }).click();
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
    await page.getByText('Desliza el árbol hacia los lados').waitFor();
    const tree = page.locator('#treeRegion');
    const treeWidth = await tree.evaluate(node => ({ client: node.clientWidth, scroll: node.scrollWidth }));
    assert.ok(treeWidth.scroll > treeWidth.client, JSON.stringify(treeWidth));
    await tree.evaluate(node => { node.scrollLeft = node.scrollWidth; });
    const chip = await page.getByRole('button', { name: 'Flop Axx avanzado' }).boundingBox();
    const region = await tree.boundingBox();
    assert.ok(chip.x >= region.x && chip.x + chip.width <= region.x + region.width + 1);
    await page.getByRole('tab', { name: 'Leer y editar' }).click();
    await page.locator('.work-select').selectOption({ label: 'Flop Axx avanzado' });
    await page.getByRole('button', { name: 'Guardar cambios' }).waitFor();
    const summary = page.locator('.work-field').filter({ hasText: 'Resumen' }).locator('textarea');
    await summary.fill('Resumen móvil corregido');
    await page.getByRole('button', { name: 'Guardar cambios' }).click();
    await page.getByText('Cambios guardados.').waitFor();
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: 'Leer y editar' }).click();
    await page.locator('.work-select').selectOption({ label: 'Flop Axx avanzado' });
    await page.locator('.work-field').filter({ hasText: 'Resumen' }).locator('textarea')
      .waitFor({ state: 'visible' });
    assert.equal(await page.locator('.work-field').filter({ hasText: 'Resumen' }).locator('textarea').inputValue(),
      'Resumen móvil corregido');
    await page.getByRole('button', { name: 'Flop Axx avanzado' }).click();
    await page.getByRole('tab', { name: 'Buscar' }).click();
    await page.getByPlaceholder('Ej. BB vs BTN en flop Axx').fill('BTN y BB');
    await page.getByRole('button', { name: 'Buscar', exact: true }).click();
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
    const uploaded = (await (await page.request.get(new URL('/api/documents', base).href)).json()).documents
      .find(doc => doc.filename === filename);
    assert.ok(uploaded);
    const linked = await (await page.request.get(new URL(`/api/documents/${uploaded.id}/topics`, base).href)).json();
    assert.equal(linked.topics.length, 2);
    assert.match(await page.locator('#treeCount').innerText(), new RegExp(`${beforeImport + 2} temas`));
    await importedCard.getByRole('button', { name: 'Ver temas' }).click();
    await page.getByRole('heading', { name: 'Tema y corrección' }).waitFor();

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
    await empty.getByRole('button', { name: 'Buscar', exact: true }).click();
    await empty.getByText('Todavía no hay contenido indexado. Importa un DOCX para empezar a buscar.').waitFor();
    await empty.unroute('**/api/tree');
    await empty.route('**/api/tree', route => route.abort());
    await empty.reload({ waitUntil: 'domcontentloaded' });
    await empty.getByText('No se pudo cargar la biblioteca local. Comprueba que el servidor esté disponible.').waitFor();
    await empty.close();
    console.log(JSON.stringify({ result: 'PASS', metrics, treeWidth, searchScrollWidth: after,
      states: ['loading', 'empty', 'failed_import', 'empty_index', 'tree_error'], importedTopics: linked.topics.length }));
  } finally {
    if (browser) await browser.close();
    fixtureProcess.stdin.end('\n');
    await once(fixtureProcess, 'exit');
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
