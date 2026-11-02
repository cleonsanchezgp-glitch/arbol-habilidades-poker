# Poker Roots — boceto de interfaz

Prototipo estático del árbol de teoría de póker, integrado sobre cuatro escenarios ilustrados.

## Abrir el boceto

Abre `index.html` en el navegador. No necesita instalación, compilación, Node.js ni conexión a Internet.

También puedes servir la carpeta con `python -m http.server 8000` y visitar http://localhost:8000.

## Añadirlo a tu repositorio

Copia esta carpeta, por ejemplo a `prototipos/poker-roots/`, manteniendo la estructura. No contiene un repositorio Git ni configuración del alojamiento original.

## Archivos

- `index.html`: estructura de la interfaz.
- `styles.css`: diseño, fichas, haces luminosos y adaptación a móvil.
- `app.js`: escenarios, nodos, relaciones y navegación.
- `assets/drawn-0.jpg` a `drawn-3.jpg`: cuatro escenarios ilustrados.

## Personalizar

Edita `environments` en `app.js` para cambiar nombres y descripciones de escenarios. Cada posición corresponde a una imagen `drawn-N.jpg`.

Edita `nodes` para cambiar el árbol. Cada nodo incluye `id`, `parent` (excepto la raíz), `label`, `symbol`, coordenadas `x`/`y`, `type`, `level` y `text`. `muted: true` da un aspecto tenue a un tema por explorar. `level` va de 0 a 3 y selecciona el escenario al pulsar la ficha.

Las coordenadas usan un lienzo de referencia de 800 × 590. Los haces se dibujan automáticamente entre cada nodo y su padre. Al cambiar esa proporción, ajusta también el SVG y los cálculos de posición.

## Alcance

Es un boceto visual con teoría de ejemplo, sin backend ni almacenamiento. La selección se restablece al recargar. Todas las fichas son explorables; el aspecto tenue no implica bloqueo real. Las imágenes son ilustraciones generadas para este concepto.

Para integrarlo en un frontend existente, traslada el HTML al componente correspondiente y adapta el JavaScript, las rutas de imágenes y los estilos globales (`body`, `header`, `aside`, etc.) al proyecto.
