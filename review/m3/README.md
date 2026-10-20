# Revisión docente de M3 — Proyecto TopIA Agro

## Alcance

Referencia técnica: `7fe531f2a4250aaf0b2d537987d92a45c1671fec` del [repositorio original](https://github.com/Manco312/Proyecto_TopIA_Agro/tree/7fe531f2a4250aaf0b2d537987d92a45c1671fec). Se evalúa M3; M1/M2 se consideran por sus efectos sobre esta entrega. M4 y Demo son orientación futura, no requisitos retroactivos. La calificación se comunica por el canal privado del curso y no se publica aquí.

El commit Git se denomina `M3` y tiene fecha anterior al cierre del módulo. Esa fecha no certifica por sí sola la recepción en Interactiva. La revisión no reescribe el historial ni reemplaza resultados entregados.

El PR documental es retroalimentación, no una corrección funcional para fusionar. Las contribuciones ejecutables se presentan en un PR separado desde `revision/m3-evaluacion`: son **helpers opt-in**, con pruebas, una re-puntuación separada y un generador de copia de trabajo. No alteran automáticamente `M3/notebookM3.ipynb`.

## Fortalezas específicas

- **Harness aplicado a cuatro sistemas:** misma interfaz y conjunto de 27 casos, resultados por identificador y medición de la latencia del sistema separada del juez. No se atribuye a este equipo la arquitectura por caché del proyecto revisado anteriormente.
- **Iteración experimental cuidadosa:** v1 queda conservada y sus respuestas se vuelven a puntuar con el medidor v2 para separar el cambio del sistema del cambio de evaluación. Esta es una fortaleza central.
- **Evaluación por etapas:** recuperación independiente del generador; comparación de chunking, BM25, RRF y reranking; análisis que no confunde recuperación de documentos con calidad de respuesta.
- **Control del juez:** comparación de juez local/control y un tercer juez API sobre respuestas guardadas; sondas de calibración y reconocimiento de limitaciones del juez local.
- **Continuidad M1–M4:** generador afinado de M1, herramientas vinculadas con errores medidos y `consultar_ficha(etiqueta)` como interfaz prevista para el componente visual.
- **Trazabilidad y reflexión:** scorecards, versiones, snapshots, resultados históricos y registro offline ya están incluidos. El equipo declara fichas sintéticas, sesgos del medidor y el alcance limitado de algunas evaluaciones.

Evidencia: [README de M3](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/7fe531f2a4250aaf0b2d537987d92a45c1671fec/M3/README.md), [notebook §§10b, 13–19 y 23](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/7fe531f2a4250aaf0b2d537987d92a45c1671fec/M3/notebookM3.ipynb), [comparación v1/v2](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/7fe531f2a4250aaf0b2d537987d92a45c1671fec/M3/comparacion_v1_v2_m3.csv), [retrieval](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/7fe531f2a4250aaf0b2d537987d92a45c1671fec/M3/retrieval_hitk_m3.csv).

## Relación con lo enseñado

[S06](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s06/README.md) fundamenta el harness; [S08](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s08/README.md), técnicas y deltas; [S10](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s10/README.md), tools y evaluación RAGAS.

**RAGAS manual fue enseñado**, incluido un parser mínimo y simplificaciones de las métricas en el laboratorio resuelto. No se exige sustituirlo por otra biblioteca ni se penaliza por sí mismo. Tampoco se inventa un umbral mínimo de desempeño. `M3/RUBRICA.md` es la rúbrica del juez LLM, no una matriz académica de calificación.

No se pide añadir scorecards, versiones, W&B o conservación de v1 como si faltaran: el equipo ya los incluyó. Los aportes se reconocen sin convertirlos en obligaciones nuevas para los demás equipos.

## Observaciones y sugerencias

### C1 — Detector y aplicabilidad de la evaluación

**Fuente:** §5, celda `ae045d14`; el propio equipo ya describe las limitaciones en §23.

Se reprodujo que citar `Cenicafé` puede contar como abstención, que una negación como `No aplicar fungicidas` activa la prescripción y que `mosaic` coincide dentro del síntoma `mosaico`. No se presentan como descubrimientos que el equipo haya ocultado.

**Sugerencia:** convertir esas limitaciones en pruebas y reglas explícitas. El helper evita citas aisladas como evidencia de rechazo, incorpora negación local y formas nominales conocidas y exige fronteras de palabra para las menciones de patógeno. No es un analizador semántico ni certifica seguridad. Puede producir otros falsos positivos/negativos; casos no cubiertos requieren revisión.

El caso `adv-01` exige abstenerse porque café estaba fuera del dominio M2. Café sí aparece en la biblioteca M3, algo reconocido por el equipo. La política propuesta **mantiene aplicable ese criterio al baseline sin RAG** y lo registra como **no aplicable** en los tres sistemas que consultan café. No concede un acierto: muestra un denominador separado y solicita revisar el criterio de contenido actual. La vista histórica permanece intacta.

La re-puntuación usa las respuestas y valores de similitud/juez guardados; no genera texto ni cambia los resultados entregados. Los valores guardados están redondeados: revisar casos cercanos a umbrales. No comparar dos cifras como una mejora del sistema cuando cambió el medidor o su denominador.

### C2 — Argumentos válidos y conflictos de cultivo

**Fuente:** §13, celdas `83c395b1` y `94ea1a00`; consumidores `_obs_diagnostico`, `_redactar_final` y ReAct de §14.

El filtrado por cultivo es valioso. Sin embargo, el argumento del planificador tiene prioridad sobre el cultivo mencionado en el texto y, ante varios cultivos, se toma el primero. Un JSON sintácticamente válido con `args` como lista también puede provocar `AttributeError` en tools de un turno. Esto **no demuestra un fallo de las 27 ejecuciones ReAct guardadas**.

**Sugerencia:** validar nombre, objeto y tipos antes del despacho. Ante contradicción o varios cultivos, propagar `conflicto_cultivo` hasta la respuesta final y solicitar aclaración. Verificar también el cultivo de la ficha seleccionada. Se conservan los caminos concordante, no cubierto y falta de cultivo; los fallos operativos de herramientas válidas no se esconden como errores de JSON.

La política es conservadora: si se nombran varios cultivos se pide aclaración, incluso si una lectura humana podría resolver la intención. No cubre automáticamente todos los nombres regionales ni sustituye una validación de imágenes. La lista de alias, ranking, modelos y generador del equipo se conservan.

## Verificación: qué se hizo y qué no

La revisión previa realizó 30 comprobaciones: 24 de caracterización de funciones seleccionadas y 6 de consistencia de artefactos. Las pruebas de caracterización que confirman un error no son pruebas de aceptación del sistema. Cuatro CSV se verificaron por hash Git blob y sus medias se contrastaron con lo reportado.

Para las contribuciones se implementó una suite de **45 regresiones** y se ejecutó localmente con funciones transcritas desde las fuentes y dobles de ranking/generación. Incluye propagación del conflicto hasta ReAct/final, esquema de tools, no modificación del medidor original, aplicabilidad explícita y creación de copias sin sobrescribir originales. Los scripts bloquean versiones de notebook distintas de la inspeccionada.

**Limitaciones:** la red del entorno revisor no permitió clonar ni descargar los modelos. El notebook se leyó por conector, pero no se verificó localmente su blob íntegro ni se ejecutó completo. Los tests locales usaron un fixture parcial transcrito; no GPU, Groq, entrenamiento o generación real. La suite publicada permite repetir sobre el notebook íntegro en el checkout del equipo. La validación con sus dependencias y ejecución completa queda pendiente antes de fusionar. No se certifica validez agronómica.

Los helpers preservan por diseño la entrega original y requieren activación explícita. No se afirma que un merge por sí solo cambie el funcionamiento del notebook original. Las instrucciones y límites están en `review/m3/sugerencias/README.md` de la rama correctiva.

## Antes de M4 y Demo

Usar `consultar_ficha(etiqueta)` como punto de integración visual, validando catálogo y desacuerdos con el texto. Conservar regresiones textuales y añadir los casos visuales pedidos en [S13](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s13/README.md).

El harness sí evalúa al agente; RAGAS y el juez API cubren otras variantes, como el equipo declara. Ampliar la evaluación independiente de casos relevantes del agente y reservar ejemplos no usados para ajustar v2 fortalecería la Demo; no son requisitos retroactivos de M3.

Mantener visible que las fichas se redactaron para el ejercicio y no son documentos oficiales vigentes. No inferir nuevas prescripciones reales a partir de esta revisión. Priorizar cambios acotados y comparaciones bajo el mismo protocolo, no reescribir la arquitectura.
