# Revisión M4: integración visual y evaluación

**Repositorio:** `Manco312/Proyecto_TopIA_Agro` · **Commit revisado:** [`9dc4769`](https://github.com/Manco312/Proyecto_TopIA_Agro/tree/9dc476984a5f2e782ccc6cba2f15f7f1483c4267) («M4 Base», `main`, 25-oct 17:06, hora de Colombia), carpeta `M4/`. No hay commits posteriores.

Esta revisión es técnica. La calificación se comunica por canal privado. Las sugerencias no son requisitos retroactivos ni cambian los criterios que ustedes fijaron antes de correr. Las celdas del notebook se cuentan **desde 0**; los enlaces a líneas usan la vista de texto del `.ipynb`.

---

## 1. Cómo se verificó

Niveles: **L** = lectura · **R** = recálculo desde sus artefactos · **E** = ejecución real · **D** = prueba con dobles o proyección sobre sus artefactos (sin volver a correr modelos).

| Qué | Cómo | Nivel | Resultado |
|---|---|---|---|
| Delta M3–M4 | Recálculo de `delta_m3_m4.csv` desde `scorecard_m4.csv` | R | 12/12 cifras coinciden |
| `ver()` y válvula | Celdas 13–15 ejecutadas sin cambios con CLIP real y su `clasificador_m4.joblib` sobre las 7 fotos, en otro hardware (CPU de Mac) | E | Etiqueta y decisión de válvula iguales a su scorecard en 7/7 |
| Cadena completa | Ver detalle debajo de la tabla. 5 casos, en otro hardware (Apple MPS) | E | `img-05` sale **idéntica carácter a carácter** a la archivada. La válvula se respeta en los 4 casos donde dispara |
| Sonda fuera del eval set | Recorte central del 50 % de `img_01` con la pregunta de papa, por la misma cadena | E | La válvula dispara (p = 0.19) y la respuesta de texto habla de maíz (M4-04) |
| Criterios por caso | `nota_exacto` y `nota_campos` (celda 31) frente a su `criterio_texto` | R | Solo `img-02` cambia con la lectura literal (M4-02) |
| Filtro de salida propuesto (C1) | Sobre las 41 filas de `scorecard_m4.csv` y sobre las 5 salidas de la cadena real | D | `img-05` pasa a 1.0 y el resto no cambia (M4-03) |
| Corrida completa en Colab, juez Groq y alternativa Qwen2-VL (§4e) | — | — | No re-ejecutados |

**Detalle de la cadena completa:**
- Se ejecutó su cargador de M3 (§0–§14) y las celdas de M4 sin cambios, salvo `cuda → mps`.
- Modelos: Qwen2.5-0.5B+LoRA y Qwen2.5-1.5B, en las mismas revisiones que ustedes usaron.
- Sin el juez por API.

Las diferencias de hardware (CPU/MPS frente a su GPU) no se consideran defectos de la entrega. Las latencias que medimos sirven como orden de magnitud y no reemplazan las suyas.

## 2. Fortalezas comprobadas

1. **La foto entra al sistema por la puerta que M3 dejó preparada.**
   - `sistema_multimodal` ([celda 26, L1930](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L1930)) encadena `ver()`, la válvula, `consultar_ficha(etiqueta)` y el generador afinado de M2.
   - Sin foto, o si la válvula dispara, sigue por el RAG agéntico de M3 sin reescribirlo.
   - La etiqueta visual decide qué ficha se consulta, así que la salida visual sí cambia la respuesta.
2. **Componente visual medido por separado y reproducible.**
   - Compararon zero-shot y una cabeza lineal sobre 760 imágenes retenidas, excluyendo las del eval set.
   - El clasificador acierta el 91.4 % y ver cuesta 0.153 s.
   - Los artefactos versionados (162 KB) permiten correrlo sin el dataset. Al ejecutarlo, sale igual en 7/7.
3. **Válvula de cuatro guardas, con umbrales calibrados.** En café y en la foto degradada no nombra ninguna de las 38 enfermedades y pide otra foto o el cultivo.
4. **Delta trazable y diagnóstico honesto.**
   - Usan un control sin foto con las mismas preguntas.
   - Separan la latencia de visión de la total.
   - Registran las revisiones de modelo en el scorecard.
   - Atribuyen el cambio 9/22 → 12/22 del bloque de texto a la actualización de `torch`, no a M4.
5. **Eval set con procedencia ejemplar.**
   - Nombres de archivo neutros, para no filtrar la etiqueta.
   - Licencias declaradas.
   - Transformación exacta de `img-07`.
   - `_procedencia.json` reconstruible.
6. **Límites y peor caso de primer nivel.**
   - `img-05` está analizado con los dos medidores en contradicción.
   - Declaran que el eval set tiene n = 7, que hubo una sola corrida, la brecha entre laboratorio y campo, que los umbrales se calibraron en el mismo retenido y que `es_hoja` no se ejerció.
   - Proponen ustedes mismos el filtro de salida.

## 3. Observaciones

### M4-01 · La fila «criterio declarado 0.25 → 1.00» compara un brazo que no puede puntuar
- **Dónde:**
  - [Control, celda 34, L2311](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L2311);
  - [`nota_valvula`, celda 31, L2172](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L2172);
  - [README L133](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/README.md?plain=1#L133) y [L217](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/README.md?plain=1#L217);
  - [`delta_m3_m4.md` L4–L7](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/delta_m3_m4.md?plain=1#L4-L7).
- **Qué se observa:**
  - En el control sin foto, los 3 casos `exacto` valen 0 por construcción.
  - `img-06` e `img-07` exigen la válvula visual, que sin foto no existe.
  - Las filas comparables no cambian:
    - el único gold comparable (`img-02`, `campos`) da 1.0 → 1.0;
    - el adversarial comparable (`img-05`) da 0/1 → 0/1;
    - los aciertos de dominio dan 2/4 → 2/4.
  - Sí mejoran, y son comparables:
    - «patógeno nombrado por el modelo»: 2/4 → 3/4;
    - la latencia: 22.94 → 16.25 s.
  - Aun así, el README presenta 0.25 → 1.00 como «la mejora real». El comentario del código y la columna «lectura» lo aclaran solo en parte.
- **Por qué importa:** mezcla una métrica del clasificador con una del sistema. En la Demo, ese número sobrevende el aporte de la foto y es fácil de cuestionar.
- **Sugerencia:**
  - Añadir al delta una columna «comparable sí/no».
  - Reportar como mejora del sistema solo las filas comparables, y el acierto del clasificador (91.4 % de 760) como fila propia.
  - `delta_comparable.py` (C2 en CODE_PR) reconstruye sus 4 filas con foto (coinciden con su CSV) y añade esa columna.
- **Criterio de cierre:** tabla de delta con la columna «comparable» y la conclusión 2 reformulada.

### M4-02 · Los criterios implementados miden menos que su `criterio_texto`
- **Dónde:**
  - [`nota_exacto` L2162](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L2162) y [`nota_campos` L2166](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L2166) (celda 31);
  - fila `img-02` de [`casos_m4.csv`](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/eval_set/casos_m4.csv?plain=1#L3) y de `scorecard_m4.csv`.
- **Qué se observa:**
  - `nota_exacto` solo compara la etiqueta. Su `criterio_texto` exige además que la respuesta nombre el patógeno y la acción.
  - `nota_campos` da 1.0 en `img-02`, aunque la respuesta afirma *mancha en diana (Corynespora cassiicola)* antes de citar la ficha de moho de la hoja. Los campos aparecen porque están en la ficha recuperada.
  - Con la lectura literal de su `criterio_texto`, solo cambia `img-02`, que pasa de 1.0 a 0.0 en los dos brazos.
  - En la cadena real (MPS), `img-02` vuelve a nombrar *mancha en diana*.
- **Por qué importa:** un texto con un patógeno equivocado se cuenta como acierto completo.
- **Sugerencia:**
  - Implementar `exacto` como «etiqueta correcta, patógeno esperado nombrado y ninguno ajeno», o renombrarlo `clasificador_top1`.
  - En `campos`, penalizar un patógeno ajeno.
  - `criterio_estricto.py` (C3 en CODE_PR) implementa ambas cosas, con pruebas.
- **Criterio de cierre:** `img-02` deja de valer 1.0 si nombra *Corynespora*, y hay una prueba por criterio.

### M4-03 · Hoja sana con receta: su propio filtro de salida, implementado
- **Dónde:**
  - [README «El peor caso», L166](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/README.md?plain=1#L166) y [§Límites, L207–L210](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/README.md?plain=1#L207-L210);
  - [`sistema_multimodal`, celda 26](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L1930).
- **Qué se observa:**
  - Ustedes lo documentan bien: `ver()` acierta («sana», 51 %) y el encabezado dice que no hay nada que tratar. Aun así, el generador receta 50–100 g/ha de fungicida.
  - Con sus modelos reales, la respuesta sale idéntica a la archivada. El fallo es estable, no ruido.
  - Su §Límites dice que el sistema no debe desplegarse sin un filtro que bloquee las prescripciones cuando el diagnóstico es «sano» o la válvula ha disparado. Ese filtro todavía no está en `sistema_multimodal`.
  - En la cadena real, con la válvula disparada, `img-02` también incluye un tratamiento para la clase ajena.
- **Por qué importa:**
  - Es el caso que más probablemente intente alguien del público en la Demo.
  - Al desplegar, la regla de su §Límites pasa a ser una condición de salida.
- **Sugerencia:** `filtro_salida.py` (C1 en CODE_PR) implementa su propia regla con su detector `dio_prescripcion_m4`.
  - Si la foto dice «sana» y el texto receta, se sustituye esa parte y se conserva el encabezado.
  - La regla de válvula viene como opción apagada, porque en `img-06` también retira la parte útil de la ficha de Cenicafé.
  - Es opt-in y no modifica su notebook.
- **Criterio de cierre:** `img-05` obtiene 1.0 en `nota_valvula` y las otras 40 filas no cambian. Repetirlo en su corrida real.

### M4-04 · Fotos de campo: la válvula protege y conviene acotar el texto que sigue
- **Dónde:** [README L191–L197](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/README.md?plain=1#L191-L197) («PlantVillage no es el campo»); `vision/vision_config.json` (umbrales: `p` 0.2173 y prototipo 0.9221).
- **Qué se observa:** es un límite que ustedes declaran como «el más serio de M4». Lo exploramos con una sola sonda, que no estima una tasa:
  - **Recorte de campo:** un recorte central del 50 % de `img_01` (tizón tardío, bien clasificado en la foto completa) baja a p = 0.19 y la válvula dispara. Es el comportamiento seguro.
  - **Texto que sigue:** la ruta de texto, con la pregunta de papa, responde sobre la mancha gris del maíz, igual que la fila de control de `img-01` en su scorecard.
  - **Café:** queda a 0.006 del umbral (p = 0.2115).
- **Por qué importa:** en la Demo, una foto propia de campo puede terminar en «no puedo identificar» o en una respuesta sobre otro cultivo.
- **Sugerencia:**
  - Probar 3–5 fotos de campo con licencia, de clases cubiertas, y reportar en cuántas dispara la válvula.
  - Cuando la válvula dispare, que la respuesta no cambie de cultivo. Pueden reutilizar su guarda 4 (cultivo de la foto frente al del texto) o pedir el cultivo.
- **Criterio de cierre:** una tabla breve «foto de campo → etiqueta / válvula / respuesta», con procedencia.

### M4-05 · Coherencia de textos y versiones
- **Dónde y qué se observa:**
  1. **Alternativa VLM no medida:**
     - La [celda 0, L48](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L48) dice «En la §4b medimos esa alternativa».
     - Pero `MEDIR_ALTERNATIVA_VLM = False` ([celda 24, L1795](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L1795)).
     - Su README (L51) lo dice bien: la medición queda montada.
  2. **Versión de `scikit-learn`:** la [celda 2, L81](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L81) la instala sin fijar versión, aunque el `.joblib` se guardó con la 1.9.0. Con otra versión aparece `InconsistentVersionWarning`.
  3. **Enlace roto:** el [README L268](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/README.md?plain=1#L268) apunta a `../ejemplos/`, que no existe.
  4. **Procedencia de `img-07`:** su `criterio_texto` dice «img_01 degradada», pero su `REFERENCIAS.md` registra otra hoja (`RS_LB 2845`).
- **Por qué importa:**
  - Son detalles, pero el punto 1 describe como medida una comparación que no se corrió.
  - El punto 2 puede romper la carga del clasificador en una instalación limpia.
- **Sugerencia:** C4 en CODE_PR corrige los cuatro sin tocar la lógica.
- **Criterio de cierre:** textos coherentes y «Restart & run all» en Colab sin avisos de versión.

**Menores (sin acción necesaria):**
- La respuesta de café incluye el token «病情», un resto del modelo de 0.5B.
- La columna `receta_m4_detector` está vacía en el bloque `texto_m3`.
- La celda 19 conserva una salida con `execution_count` nulo.

## 4. Seguimiento de M3 (PR #1 y #2 del fork)

- **Incorporado tal cual:** `consultar_ficha(etiqueta)` como punto de integración de la foto.
- **Incorporado de otra forma:**
  - En el camino visual, el detector de prescripción con negadores (`dio_prescripcion_m4`) y su `assert` de regresión (celda 30) ([#1](https://github.com/manularrea/Proyecto_TopIA_Agro/pull/1)).
  - El conflicto de cultivo, como guarda 4 de la válvula (foto frente a texto), en lugar de validar `args` en las herramientas de M3 ([#2](https://github.com/manularrea/Proyecto_TopIA_Agro/pull/2)).
  - La comparación bajo el mismo protocolo, con un control sin foto bien diseñado. M4-01 afina su lectura.
- **Decisión razonable:** no reescribir M3, de modo que el camino de texto conserva su detector original.
- **Sigue abierto:** separar «cita» de «abstención» en los adversariales de texto (3 de 5 en M3 y en M4).
- #1 y #2 pueden quedar como referencia histórica.

## 5. Prioridades para Demo Day

La Demo presenta el sistema completo como producto. Ya tienen un único punto de entrada, `sistema_multimodal(pregunta, imagen=None, detalle=False)` ([celda 26, L1930](https://github.com/Manco312/Proyecto_TopIA_Agro/blob/9dc476984a5f2e782ccc6cba2f15f7f1483c4267/M4/notebookM4.ipynb?plain=1#L1930)). Esa función encadena:

- la foto (`ver()` y la válvula, M4);
- la ficha y el RAG agéntico (M3);
- el generador Qwen2.5-0.5B+LoRA (M2);
- las 38 clases de M1.

[`PLAN_DEMO.md`](PLAN_DEMO.md) propone tres prioridades sobre ese camino:

1. **[P0] Un «momento wow» de punta a punta.** El agricultor sube la foto y ve «lo que vi», «qué hacer» y «de dónde sale», con tiempos. Al desplegar en M5, conviene una interfaz delgada sobre `sistema_multimodal`.
2. **[P1] La confianza como característica** (M4-03, M4-04). Ante una hoja sana, «no aplique nada». Ante café o una foto ilegible, «¿qué cultivo es?», sin recetar ni cambiar de cultivo.
3. **[P2] Tres números de valor y una demo robusta** (M4-01):
   - números comparables, con su denominador;
   - tag y casos ensayados;
   - plan B rotulado.

`PLAN_DEMO.md` incluye además un guion sugerido y un backlog breve (M4-02, M4-05).

## 6. Cómo reproducir lo verificado

Desde la raíz del repositorio, con la rama de CODE_PR:

```bash
python -m unittest discover -s review/m4/tests -p 'test_*.py' -v   # 17 pruebas (C1 necesita pandas; el resto solo stdlib)
python review/m4/propuesta/delta_comparable.py --estricto           # 4/4 filas iguales a delta_m3_m4.csv + columna «comparable»
python review/m4/propuesta/criterio_estricto.py                     # criterio entregado frente a lectura literal, por caso
```

- **`ver()`:** celdas 13–15 sin cambios, con `openai/clip-vit-base-patch32` y `M4/vision/`, sobre `M4/eval_set/imagenes/`.
- **Cadena completa:** su cargador de `notebookM3` (§0–§14) y las celdas de M4 hasta la 33, cambiando solo el dispositivo (`cuda → mps`).
  - Casos: `img-02`, `img-05`, `img-06`, `img-07` y el recorte del 50 % de `img_01`.
  - Las huellas de las celdas y las salidas están en `review/m4/evidence/validacion_m4.json`, en la rama de CODE_PR.
- **No se re-ejecutaron:** la corrida completa en Colab, el juez por API ni la alternativa Qwen2-VL.
