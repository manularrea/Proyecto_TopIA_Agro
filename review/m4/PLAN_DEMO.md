# Plan para Demo Day — Recomendador agronómico con foto (M1–M4)

Para el 5 de noviembre, la idea es presentar el sistema como un **lanzamiento de producto**: un agricultor con un problema, una foto tomada con el teléfono y una recomendación útil en segundos. No se trata de defender un laboratorio. Ya tienen las piezas difíciles. Las prioridades de abajo son cambios pequeños sobre el camino que ya existe, pensados para que el sistema luzca. **Ninguna exige rediseñar.**

## Lo que ya tienen conectado (base para el despliegue)

- **Punto de entrada actual:** `sistema_multimodal(pregunta, imagen=None, detalle=False)` en `M4/notebookM4.ipynb`, que se ejecuta de arriba abajo. El cargador del notebook monta todo M3 (§0–§14). Con `detalle=True` devuelve la etiqueta, la probabilidad, la ruta, la válvula y las latencias. Esa es la base natural de la interfaz cuando desplieguen.
- **Recorrido M1–M4 ya integrado en esa función:**
  1. **Problema y clases (M1):** las 38 clases de PlantVillage.
  2. **Generador (M2):** Qwen2.5-0.5B+LoRA, que M3 llama.
  3. **Visión (M4):** la foto pasa por `ver()` (cabeza lineal sobre CLIP), luego por la válvula de cuatro guardas, luego por `consultar_ficha(etiqueta)` (la herramienta que M3 dejó lista para M4) y por último por el generador.
  4. **Texto (M3):** sin foto, o cuando la válvula se activa, la consulta sigue por el RAG agéntico de M3 (`sistema_rag_agentico`).
- **Activos que sirven para la demo:**

  | Activo | Dato |
  |---|---|
  | Acierto en imágenes nunca vistas | 91.4 % de 760 |
  | Tiempo del paso visual | 0.153 s |
  | Ejemplos de punta a punta en `scorecard_m4.csv` | `img-01` papa con tizón tardío (16.5 s), `img-03` maíz con roya (14.3 s), `img-04` vid con esca (14.5 s) |
  | Cobertura | Café fuera de cobertura: el sistema no inventa una clase |
  | Foto ilegible | Pide otra foto (2.7 s) |

## Prioridades (máx. 3)

### P0 — Un «momento wow» de punta a punta, con la foto como entrada y la evidencia a la vista

**Qué podría ocurrir durante la demo:** el producto funciona, pero en el notebook se ve como celdas y diccionarios. Con eso se pierden justo los activos que lo distinguen: la etiqueta que vio, su confianza, la ficha consultada y lo poco que tarda en ver.

**Evidencia exacta:**
- La salida de `sistema_multimodal(..., detalle=True)` en la celda 26 de `notebookM4.ipynb` ya contiene `etiqueta_pred`, `p_top1`, `ruta`, `valvula`, `latencia_vision_s` y `latencia_s`.
- `scorecard_m4.csv` muestra `img-01` y `img-03` con 1.0 en su criterio y unos 15 s de punta a punta.

**Cambio mínimo recomendado:** al desplegar, conviene una interfaz delgada sobre la función existente.
- Entradas: subir o tomar foto, más una pregunta opcional.
- Salidas en tres bloques:
  1. «Lo que vi»: cultivo y enfermedad, con su confianza.
  2. «Qué hacer»: la recomendación.
  3. «De dónde sale»: la ficha o fuente consultada y el tiempo de respuesta.
- Ensayar 2–3 casos estrella. Por ejemplo `img-01` papa (la historia del README: «las hojas se le están poniendo negras») y una foto propia de cultivo cubierto.
- Etiquetar una versión estable (tag) para la demo.

**Qué NO hace falta rehacer:** el clasificador, la válvula, el RAG de M3 ni el eval set. La interfaz solo envuelve la función.

**Cómo verificar el cierre:** desde un dispositivo distinto al del equipo, subir la foto del caso estrella. Se debe ver la etiqueta, la confianza, la recomendación, la fuente y el tiempo, y el resultado debe coincidir con el ensayado.

**Quién lo asume:** lo decide el equipo.

### P1 — Convertir los casos límite en una característica de confianza visible

**Qué podría ocurrir durante la demo:**
- **Hoja sana:** si alguien sube una hoja sana, el sistema dice «sana» y a continuación receta 50–100 g/ha de fungicida.
- **Válvula activada:** el sistema rechaza bien la foto, pero la respuesta de texto que sigue puede cambiar de cultivo o recetar sin la base de la foto.

**Evidencia exacta:**
- **Hoja sana (`img-05`):** el propio README de M4 lo documenta como peor caso. La revisión lo reprodujo con los modelos reales del equipo y obtuvo una respuesta idéntica a la archivada.
- **Válvula activada:** la válvula se respetó en los 4 casos probados. Sin embargo, en un recorte de `img_01` con pregunta sobre papa, la respuesta habló de *mancha gris del maíz*, igual que la fila de control del propio scorecard. En `img-02` nombró *mancha en diana*.

**Cambio mínimo recomendado:** presentarlo como «así se comporta con seguridad»:
- **Hoja sana:** si `ver()` dice sano, se muestra «tu hoja se ve sana, no hace falta aplicar nada» y no se receta. Es la regla de su propio §Límites; C1 en CODE_PR (`review/m4/propuesta/filtro_salida.py`) la implementa como opción, sin tocar el notebook (M4-03).
- **Válvula activada:** mostrar el aviso de la válvula como mensaje de producto («no reconozco este cultivo con suficiente confianza; ¿qué cultivo es?») y no recetar en esa misma respuesta. Para el cultivo pueden reutilizar su guarda 4 (cultivo de la foto vs. texto) (M4-04). C1 trae la regla de válvula como opción apagada: en `img-06` también retiraría la parte útil de la ficha de Cenicafé.
- En la demo, mostrar a propósito un caso de café o una foto borrosa como guardrail visible.

**Qué NO hace falta rehacer:** el clasificador, los umbrales de la válvula ni el generador. Basta con controlar qué texto se muestra cuando la válvula se activa o la foto dice sano.

**Cómo verificar el cierre:**
- `img-05` responde sin receta.
- `img-06`, `img-07` y el recorte de campo muestran el aviso y no recetan para otro cultivo.
- `img-01`, `img-03` e `img-04` no cambian.

**Quién lo asume:** lo decide el equipo.

### P2 — Tres números de valor y una demo que no dependa de la suerte

**Qué podría ocurrir durante la demo:**
- **Métricas:** un 0.25→1.0 puede sonar a una mejora del sistema completo, cuando el control sin foto no podía puntuar en ese criterio. Mientras tanto, el dato que sí impresiona (ver cuesta 0.15 s) queda escondido en una tabla.
- **Infraestructura:** si falla la red o la GPU, no hay respaldo.

**Evidencia exacta:**
- `delta_m3_m4.md`, filas del criterio declarado (0.25 → 1.0) y de latencia (M4-01).
- La celda 34 asigna 0 a los casos `exacto` en el control: esa fila no es comparable. Las comparables (dominio 2/4 → 2/4, `img-02` 1.0 → 1.0, `img-05` 0/1 → 0/1) no cambian.
- Latencias del README de M4: 16.25 s con foto frente a 22.94 s sin foto, en una laptop de 6 GB.

**Cambio mínimo recomendado:**
- **Números de producto, cada uno con su denominador:**
  - «Reconoce la enfermedad en 91.4 % de 760 hojas que nunca vio».
  - «Con foto, el sistema nombra el patógeno en 3 de 4 casos, frente a 2 de 4 sin foto». `delta_comparable.py` (C2 en CODE_PR) añade la columna «comparable» a su tabla.
  - «Ver cuesta 0.15 s; la respuesta completa llega en ~16 s (antes ~23 s)».
- **Robustez de la demo:**
  - Plan B rotulado: una grabación o las salidas guardadas de los casos ensayados.
  - Al desplegar, conviene un health check y logs JSON por consulta (etiqueta, válvula, latencia), y un tablero de W&B para mostrarlo como «así lo operamos».
  - Si aplican la técnica de eficiencia de M5, mostrar una tabla corta de antes y después en el mismo hardware.

**Qué NO hace falta rehacer:** la corrida de evaluación. Los números ya están en sus artefactos.

**Cómo verificar el cierre:**
- Cada número de la diapositiva se puede rastrear a un archivo del repo.
- La grabación o las salidas guardadas están accesibles sin red.

**Quién lo asume:** lo decide el equipo.

## Guion sugerido (bloques, sin minutos obligatorios)

1. **El usuario y su dolor.** Un agricultor de papa ve hojas que se ponen negras. No sabe qué es y tiene el teléfono en la mano. La decisión que toma es si aplica algo, qué y cuánto.
2. **Momento wow.** Toma la foto, la sube y en segundos recibe: «Papa · tizón tardío (confianza X)», qué hacer, de qué ficha sale y cuánto tardó.
3. **Cómo lo logra.** Mostrar en una sola imagen el recorrido foto → CLIP que ve → ficha (M3) → redacción con el modelo afinado (M2). La foto reemplaza tener que saber media respuesta.
4. **Confianza como característica.** Una hoja sana recibe «no apliques nada». Café o una foto borrosa reciben «no lo reconozco con seguridad, ¿qué cultivo es?».
5. **Prueba de valor.** Los tres números, cada uno con su denominador.
6. **Así lo operamos.** Versión etiquetada, health check y logs o W&B, y el plan B a mano.
7. **Límites y siguiente paso.** Hoy cubre 14 cultivos y 38 clases de PlantVillage, con fotos de laboratorio. Siguiente paso: fotos de campo, más cultivos (café) y el modelo generador.

## Backlog (después de la demo)

- Alinear `nota_exacto` y `nota_campos` con el `criterio_texto` de cada caso (M4-02; C3 en CODE_PR).
- Fijar la versión de `scikit-learn` (M4-05; C4 en CODE_PR, igual que los dos puntos siguientes).
- Corregir el enlace `../ejemplos/` y el texto «§4b medimos».
- Corregir la procedencia de `img-07` en el CSV.
- Quitar el token «病情» en la respuesta de café.
- Medir con 3–5 fotos de campo de cultivos cubiertos.
