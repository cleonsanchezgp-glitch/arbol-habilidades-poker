## Title

| Field | Value |
| --- | --- |
| Document | Project Glossary — Texas Hold'em learning library |
| Initiative | INI-001 / PRJ-001 |
| Version | 0.1 |
| Status | Draft - for owner review |
| Author | Notarius |
| Reviewers | Project owner |
| Organization | Aelium |
| Last Updated | 2026-10-31 |

| Term | Definition |
| --- | --- |
| Texas Hold'em | Modalidad de póker cuyo material de estudio organiza esta aplicación. Define el alcance temático del producto. |
| Mentopoker | Escuela de la que procede la teoría recopilada por el usuario; sus documentos importados son la fuente principal de conocimiento del producto. |
| DOCX original | Archivo subido por el usuario y conservado sin sustituirlo por la explicación generada. Permite volver a comprobar el contenido y sus condiciones. |
| Importación | Proceso de validar y guardar un DOCX, extraer sus fragmentos, proponer temas e incorporarlos al índice de búsqueda. Su estado y sus errores son visibles. |
| Fragmento de fuente | Parte identificable del DOCX original, como un párrafo, tabla o imagen extraíble, a la que puede enlazar un tema o una respuesta. |
| Tema | Concepto o estrategia de estudio con título y contenido estructurado; un DOCX puede producir varios temas y un tema puede aparecer en varias ramas sin duplicarse. |
| Procedencia | Relación que permite saber qué documento y fragmentos respaldan un tema o una afirmación. Las correcciones del usuario y los ejemplos generados no sustituyen el original. |
| Afirmación respaldada | Explicación estratégica cuyo significado y condiciones pueden contrastarse con los fragmentos de fuente citados. |
| Ejemplo didáctico generado | Ejemplo creado para ayudar a entender una explicación. Debe identificarse como generado y no atribuir a la fuente datos estratégicos que esta no aporta. |
| Dato desconocido | Campo estratégico que el documento no especifica. Se conserva como desconocido en vez de inferirse como hecho. |
| Contradicción entre fuentes | Diferencia relevante entre documentos importados que afecta a una explicación; se muestra al usuario sin resolverla mediante una conclusión inventada. |
| Clasificación temática / faceta | Campo ampliable que describe el contexto de un tema, como calle, posiciones, tipo de bote, textura del board o concepto estratégico. |
| Calle | Etapa de la mano usada como faceta temática: preflop, flop, turn o river, cuando la fuente permite identificarla. |
| BTN / BB / SB | Abreviaturas de las posiciones botón, ciega grande y ciega pequeña usadas en consultas y clasificación. |
| Textura del board | Descripción de las cartas comunitarias pertinente para situar una estrategia; se registra solo si la fuente permite determinarla. |
| Dificultad | Nivel básico, intermedio o avanzado atribuido a un tema para orientar el estudio. No implica por sí mismo una relación de prerrequisito. |
| Prerrequisito | Tema que conviene comprender antes de otro por una razón pedagógica. Puede haber varios y sus relaciones no pueden formar ciclos. |
| Ubicación en rama | Enlace de navegación que sitúa un tema en una o varias ramas del árbol. Es distinto del prerrequisito y no crea copias del tema. |
| Árbol de conocimientos | Vista descendente de temas y ramas, desde fundamentos hacia estrategias más complejas; presenta una red de relaciones sin exigir que cada tema tenga un único padre. |
| Ruta de aprendizaje | Secuencia recomendada de temas realmente disponibles, ordenada según sus prerrequisitos y acompañada de una razón breve. |
| RAG | Recuperación de fragmentos y temas importados para aportar contexto a una respuesta del modelo local; la respuesta debe enlazar sus fuentes y reconocer lagunas. |
| Recuperación léxica | Búsqueda por términos del texto indexado, incluidos términos técnicos presentes en fuentes y consultas. |
| Recuperación semántica | Búsqueda por proximidad de significado mediante representaciones vectoriales locales, complementaria de la búsqueda léxica. |
| Embedding | Representación vectorial calculada localmente para comparar una consulta con fragmentos o temas; no es una explicación ni una fuente de teoría. |
| Modelo de IA local | Modelo ejecutado en la máquina del usuario para proponer temas, interpretar consultas o redactar respuestas sobre material recuperado. |
| Ollama | Opción técnica propuesta para ejecutar y consultar modelos de IA locales. No es una modalidad de póker ni una fuente de teoría; el diseño permite sustituirla. |
| Solver | Herramienta que calcula estrategias bajo supuestos matemáticos explícitos. Esta aplicación organiza teoría importada y no presenta sus respuestas RAG como cálculos de solver. |
| Documento duplicado / teoría similar | Un duplicado exacto coincide con un archivo ya importado; la similitud temática es una posible coincidencia que el usuario revisa antes de conservar o combinar temas. |
| Escena visual | Uno de los cuatro ambientes ilustrados del boceto Poker Roots. Refuerza la progresión visual, pero no equivale a los tres niveles de dificultad. |
| Evidencia de fuente | Referencia al DOCX original que respalda una explicación de póker. Es diferente de la evidencia de ejecución de pruebas. |
| Evidencia de prueba | Registro de una prueba ejecutada, con resultado y referencia verificable; las pruebas del TMP están actualmente `Not Run` y no tienen esta evidencia. |
