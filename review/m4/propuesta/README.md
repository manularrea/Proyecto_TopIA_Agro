# Sugerencias de código M4 (propuesta para validar en su entorno)

Base: `9dc476984a5f2e782ccc6cba2f15f7f1483c4267` (`main`, «M4 Base»). Todo lo nuevo está en `review/m4/`. Los únicos cambios a archivos existentes son tres correcciones de texto y la fijación de una versión (C4). **No se modifica la lógica del notebook ni los resultados entregados.**

| | Archivo | Observación | Qué hace |
|---|---|---|---|
| C1 | `propuesta/filtro_salida.py` | M4-03 | Filtro de salida opt-in que implementa la regla de su §Límites. Ver detalle abajo. |
| C2 | `propuesta/delta_comparable.py` | M4-01 | Reconstruye desde `scorecard_m4.csv` las filas del delta con foto y añade la columna «comparable». |
| C3 | `propuesta/criterio_estricto.py` | M4-02 | Implementa `exacto` y `campos` tal como los describe `criterio_texto`. Ver detalle abajo. |
| C4 | `M4/notebookM4.ipynb`, `M4/README.md`, `M4/eval_set/casos_m4.csv` | M4-05 | Correcciones de texto y fijación de `scikit-learn`. Ver detalle abajo. |

**C1 · Filtro de salida opt-in**
- **Regla principal:** si la foto dice «sana», el texto del modelo no puede recetar. Si receta, se sustituye esa parte y se conserva el encabezado.
- **Regla opcional `bloquear_en_valvula=True`:** hace lo mismo cuando la válvula se dispara.

**C3 · Criterios según `criterio_texto`**
- `exacto` = etiqueta correcta, más el patógeno esperado nombrado, sin nombrar el de otra clase.
- `campos` vale 0 si la respuesta nombra el patógeno de otra clase.

**C4 · Correcciones de texto y versión**
- Celda 0: «§4b medimos» pasa a decir «§4e dejamos montada su medición».
- Celda 2: `scikit-learn~=1.9.0`, la versión con la que se guardó `clasificador_m4.joblib`.
- Enlace `../ejemplos/` de su README.
- Procedencia de `img-07` en el texto del criterio.

## Activar C1 en una copia del notebook

Ejecútenlo después de la celda 26 (`sistema_multimodal`) y de la §6 (`dio_prescripcion_m4`):

```python
import sys; sys.path.insert(0, "../review/m4/propuesta")
import filtro_salida; filtro_salida.instalar(globals())             # solo la regla «sano»
# filtro_salida.instalar(globals(), bloquear_en_valvula=True)       # + regla de válvula
```

**Costo de diseño (decídanlo ustedes):** con la regla de válvula, `img-06` (café) pierde también la parte útil de la ficha de Cenicafé, porque esa respuesta contiene «fungicidas cúpricos». Por eso viene apagada.

## Cómo probar

Desde la raíz del repositorio:

```bash
python -m unittest discover -s review/m4/tests -p 'test_*.py' -v   # 17 pruebas (pandas para C1; el resto solo stdlib)
python review/m4/propuesta/delta_comparable.py --estricto           # tabla comparable, con y sin criterio estricto
python review/m4/propuesta/criterio_estricto.py                     # valor entregado frente a valor estricto, por caso
```

## Qué se probó y qué no

**Probado con sus artefactos:**
- 17/17 pruebas OK con `scorecard_m4.csv`, `casos_m4.csv`, `delta_m3_m4.csv` y `datos/base_conocimiento_plantvillage.json`.
- **C1:**
  - El detector transcrito reproduce la columna `receta_m4_detector`.
  - `img-05` pasa de 0.0 a 1.0 y las otras 40 filas no cambian.
  - Con la regla de válvula, solo cambian `img-05` e `img-06`.
- **C2:** reconstruye 4 filas de su `delta_m3_m4.csv` y coinciden.
- **C3:** solo cambia `img-02`, en los dos brazos. La respuesta nombra *Corynespora cassiicola* (mancha en diana) antes de citar la ficha de *Passalora fulva*.

**Probado con generación real en otro hardware:**
- Su cadena completa se ejecutó en 5 casos en Apple MPS, sin el juez por API y sin cambios fuera del dispositivo:
  - celdas de M4 y `notebookM3` §0–§14;
  - Qwen2.5-0.5B+LoRA y Qwen2.5-1.5B en las mismas revisiones.
- La respuesta de `img-05` salió idéntica a la archivada.
- Con C1 instalado sobre `sistema_multimodal` en esa misma cadena, `img-05` obtiene 1.0 con su criterio de válvula.
- C1 aplicado a esas salidas:
  - bloquea la receta de `img-05`;
  - con `bloquear_en_valvula=True`, también las de `img-02` e `img-06`;
  - no toca `img-07` ni el recorte de `img_01`.

**No probado:**
- El notebook completo en Colab o en su GPU, con C1 instalado.
- C4 en una instalación limpia de Colab.
- El detector de prescripción es heurístico: una receta redactada sin sus verbos o productos no se bloquearía.
- C1 no certifica seguridad agronómica.
