# Poker Roots — mapa visual conectado

Esta carpeta conserva los cuatro escenarios ilustrados del boceto y contiene ahora el árbol conectado a la biblioteca local. Las ramas, temas, ubicaciones y prerrequisitos vienen de `GET /api/tree`; no hay teoría de ejemplo en la interfaz activa.

## Abrir

Desde la raíz del repositorio, inicia `python -m backend.api --port 8765` y abre `http://127.0.0.1:8765/`. El servidor entrega estos archivos y la API desde el mismo origen. Abrir `index.html` como archivo o servir esta carpeta por separado no carga la biblioteca.

## Herramientas de biblioteca

`workspace.js` conecta seis vistas con la API local: importar DOCX y seguir su estado, leer y corregir temas, inspeccionar fuentes, buscar respuestas con citas, crear rutas de estudio respaldadas y comparar temas similares. Las correcciones de campos, facetas y relaciones se guardan juntas. El análisis de importaciones y la búsqueda necesitan un modelo local configurado; la lectura y las rutas usan el contenido ya guardado.

## Archivos

- `index.html`: estructura accesible del mapa y panel de detalle.
- `styles.css`: fichas, conectores, escenarios y adaptación móvil.
- `app.js`: carga de temas guardados, navegación por ramas y retorno a ubicaciones.
- `assets/drawn-0.jpg` a `drawn-3.jpg`: escenarios ilustrados del boceto.

La escena visual sigue la profundidad de navegación; no representa la dificultad del tema. Un tema situado en varias ramas aparece en cada lugar y conserva un único registro. La página muestra estados de carga, vacío y error. Las vistas completas de importación, edición, búsqueda y estudio pertenecen a TSK-017.
