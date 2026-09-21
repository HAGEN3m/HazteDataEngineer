# 🐻‍❄️ Lección 38: Polars Avanzado — Evaluación Perezosa (`LazyFrame`), Optimizador de Consultas y Lectura Streaming (`scan_parquet`)

En la **Lección 37** descubrimos que Polars es sumamente rápido gracias a su núcleo en Rust y su ejecución multihilo. Sin embargo, su verdadero superpoder para la **Ingeniería de Datos a gran escala** no es solo la velocidad de sus estructuras en memoria (`DataFrame`), sino su **Motor de Evaluación Perezosa (** **Lazy Evaluation** **)** a través de la interfaz **LazyFrame**.

Cuando trabajás con datasets que pesan decenas o cientos de Gigabytes (incluso aquellos que superan la capacidad de tu Memoria RAM local), cargar los datos de golpe con `read_parquet()` o `read_csv()` colapsará tu sistema. Con el enfoque **Lazy**, Polars examina primero todas las transformaciones que querés hacer, optimiza la consulta como lo haría un motor SQL avanzado y recién ahí ejecuta el plan consumiendo el mínimo de recursos posibles.

---

## 1\. Modos de Ejecución: `DataFrame` (Eager) vs. `LazyFrame` (Lazy)

* **Eager Evaluation (** **pl.read\_parquet** **)**: Ejecuta cada línea de código inmediatamente en el momento en que se lee. Si aplicás 5 filtros seguidos, realiza 5 recorridos separados sobre los datos en RAM.
* **Lazy Evaluation (** **pl.scan\_parquet** **)**: No lee los datos de inmediato ni reserva RAM. En su lugar, construye un **Grafo Director Acíclico (DAG)** o **Plan Lógico de Ejecución**. Las transformaciones no se ejecutan hasta que llamás explícitamente al método **.collect()**.

```
import polars as pl

# 🔴 ENFOQUE EAGER (Carga todo el archivo a RAM inmediatamente)
df_eager = pl.read_parquet("data_lake/ventas_gigante.parquet")
df_filtrado = df_eager.filter(pl.col("monto") &gt; 500.0)

# 🟢 ENFOQUE LAZY (No carga nada a RAM, solo construye la receta)
lazy_plan = (
    pl.scan_parquet("data_lake/ventas_gigante.parquet")
    .filter(pl.col("monto") &gt; 500.0)
    .select(["transaccion_id", "cliente_id", "monto", "fecha"])
)

# ⚡ Para disparar la ejecución real y traer el resultado a memoria:
df_resultado = lazy_plan.collect()

```

---

## 2\. El Optimizador de Consultas de Polars (*Query Optimizer*)

Cuando llamás a `.collect()`, el optimizador interno de Polars reescribe y simplifica tu consulta automáticamente aplicando tres técnicas fundamentales:

1. **Projection Pushdown (Poda de Columnas)**: Si tu archivo Parquet tiene 80 columnas pero en tu pipeline solo seleccionás 3, Polars le ordena al lector de Parquet leer únicamente los bytes de esas 3 columnas directamente del disco, ignorando el 95% restante del archivo.
2. **Predicate Pushdown (Poda de Filas)**: Si colocás un `.filter(pl.col("anio") == 2026)` al final de tu pipeline de código, Polars mueve (*empuja*) automáticamente ese filtro hasta el inicio de la lectura. En archivos Parquet o datasets particionados, esto evita leer bloques enteros de filas (*Row Groups*).
3. **Slice Pushdown**: Si ponés un `.head(10)` al final, Polars detiene la lectura tan pronto como obtiene los primeros 10 registros, sin procesar el resto del archivo.

---

## 3\. Inspeccionar el Plan de Ejecución (`explain()`)

Podés ver exactamente cómo Polars ha optimizado tu consulta imprimiendo el plan de ejecución con el método **.explain()**:

```
plan_lazy = (
    pl.scan_parquet("data_lake/ventas/*.parquet")
    .filter(pl.col("estado") == "COMPLETADA")
    .with_columns(monto_usd=pl.col("monto") / 1200.0)
    .select(["transaccion_id", "monto_usd", "estado"])
)

# Muestra en texto claro cómo el optimizador reordenó y simplificó la consulta
print(plan_lazy.explain())

```

---

## 4\. Procesamiento que Supera la Memoria RAM (*Streaming Engine*)

Si tenés un dataset de 50 GB y tu servidor solo tiene 16 GB de RAM, incluso el modo Lazy estándar podría quedarse corto al intentar juntar los resultados finales en memoria.

Para resolver esto, Polars incluye un **Motor de Streaming** que procesa los datos en pequeños lotes (*chunks*) a través del disco y la CPU, sin cargar el dataset completo en memoria RAM al mismo tiempo:

```
# Activa el procesador por lotes en streaming para datasets gigantes
df_gigante_procesado = plan_lazy.collect(streaming=True)

```

---

## 🏋️‍♂️ Práctica de la Lección 38

1. Creá el archivo `ej_38_polars_lazy.py` dentro de la carpeta `practica/`.
2. Escribí un script de **ingesta y optimización Lazy con datasets particionados**:
  * **Paso 1**: Generá un dataset sintético en Pandas/Polars con 200,000 filas y 10 columnas (`id`, `cliente`, `region`, `categoria`, `monto`, `impuesto`, `descuento`, `fecha`, `vendedor`, `observaciones`).
  * **Paso 2**: Guardá el dataset en formato Parquet en la ruta `practica/data_lake_lazy.parquet`.
  * **Paso 3**: Construí una consulta **LazyFrame** usando `pl.scan_parquet()`:
    * Filtrá las filas donde `monto &gt; 100.0` y `region == 'SUR'`.
    * Creá la columna `monto_total = (pl.col("monto") + pl.col("impuesto")) - pl.col("descuento")`.
    * Agrupá por `categoria` y calculá el total de `monto_total` y la cantidad de transacciones.
  * **Paso 4**: Antes de ejecutar `.collect()`, imprimí en pantalla el resultado de `query_lazy.explain()` para inspeccionar cómo funcionó el **Predicate** y **Projection Pushdown**.
  * **Paso 5**: Ejecutá `.collect()` e imprimí el DataFrame analítico final.
3. Ejecutá tu script desde la terminal: `python3 practica/ej_38_polars_lazy.py`