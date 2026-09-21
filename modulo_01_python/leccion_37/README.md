# 🐻‍❄️ Lección 37: Introducción a Polars — La Alternativa de Alto Rendimiento a Pandas en Rust

En las lecciones 35 y 36 exploramos cómo exprimir el rendimiento de **Pandas** mediante vectorización y operaciones en C. Sin embargo, Pandas tiene limitaciones de arquitectura históricas:

1. **Mono-hilo (Single-threaded)**: No aprovecha múltiples núcleos de la CPU por defecto.
2. **Uso Excesivo de Memoria RAM**: Suele requerir entre 5x y 10x el tamaño del dataset en memoria para realizar transformaciones.
3. **Evolución basada en Índices**: La estructura basada en índices complejos (`Index` / `MultiIndex`) añade sobrecarga y confusión.

En la Ingeniería de Datos moderna, **Polars** se ha consolidado como la alternativa de más rápido crecimiento. Escrito desde cero en **Rust** sobre la memoria columnar de **Apache Arrow**, Polars está diseñado para ser ultra rápido, multihilo nativo y eficiente en memoria.

---

## 1\. ¿Por qué Polars es tan Rápido?

| Característica               | Pandas             | Polars                                           |
| ---------------------------- | ------------------ | ------------------------------------------------ |
| **Lenguaje del Motor**       | Python / C         | Rust (sin GIL de Python)                         |
| **Paralelismo**              | Mono-hilo (1 core) | Multihilo automático (Aprovecha todos los cores) |
| **Estructura en Memoria**    | Arrays de NumPy    | Apache Arrow Columnar (Zero-Copy)                |
| **Estrategia de Evaluación** | Eager (Inmediata)  | Eager + **Lazy (Optimizador de Consultas)**      |
| **Uso de Índices**           | Sí (`df.index`)    | No (Columnas explícitas únicamente)              |

---

## 2\. El Motor de Expresiones de Polars (`pl.col()`)

A diferencia de Pandas (donde seleccionamos columnas con `df["columna"]`), en Polars todo se construye utilizando **Expresiones** mediante la función **pl.col()**.

Las expresiones de Polars son **declarativas** e **inmutables**: describen la transformación que querés hacer, permitiendo que Polars ejecute múltiples transformaciones en paralelo a nivel de CPU.

```
import polars as pl

df = pl.DataFrame({
    "cliente": ["CLI-01", "CLI-02", "CLI-01", "CLI-03"],
    "monto": [150.0, 200.0, 300.0, 50.0],
    "pais": ["AR", "CL", "AR", "UY"]
})

# 🟢 SELECCIÓN Y TRANSFORMACIÓN CON EXPRESIONES
df_transformado = df.select([
    pl.col("cliente"),
    (pl.col("monto") * 1.21).alias("monto_con_impuesto"),
    pl.col("pais").str.to_lowercase().alias("pais_min")
])

```

---

## 3\. Operaciones Esenciales: `filter()`, `with_columns()` y `group_by()`

En Polars no modificás las columnas existentes in situ (*in-place*). Utilizás los siguientes métodos principales:

### A. Filtrado de Filas: `.filter()`

```
# Múltiples condiciones combinadas con &amp; (AND) o | (OR)
df_filtrado = df.filter(
    (pl.col("monto") &gt; 100.0) &amp; (pl.col("pais") == "AR")
)

```

### B. Agregar o Modificar Columnas: `.with_columns()`

```
df_nuevo = df.with_columns(
    monto_usd=pl.col("monto") / 1200.0,
    categoria=pl.when(pl.col("monto") &gt; 150.0).then(pl.lit("ALTO")).otherwise(pl.lit("BAJO"))
)

```

### C. Agrupación y Agregación: `.group_by()`

```
resumen = df.group_by("pais").agg([
    pl.col("monto").sum().alias("monto_total"),
    pl.col("monto").mean().alias("monto_promedio"),
    pl.col("cliente").count().alias("cantidad_clientes")
])

```

---

## 4\. Polars vs. Pandas: Ejemplo Comparativo de Sintaxis

```
# --- EN PANDAS ---
df_pandas["monto_final"] = df_pandas["monto"] * 1.21
df_pandas_filtrado = df_pandas[df_pandas["monto_final"] &gt; 200.0]

# --- EN POLARS ---
df_polars_filtrado = (
    df_polars
    .with_columns(monto_final=pl.col("monto") * 1.21)
    .filter(pl.col("monto_final") &gt; 200.0)
)

```

---

## 🏋️‍♂️ Práctica de la Lección 37

1. Creá el archivo `ej_37_polars_intro.py` dentro de la carpeta `practica/`.
2. Escribí un script para **comparar la velocidad de procesamiento entre Pandas y Polars**:
  * Instalá Polars en tu entorno virtual: `pip install polars`.
  * **Paso 1**: Generá un dataset sintético de **1,000,000 de filas** con las columnas: `id`, `categoria`, `monto`, `descuento`.
  * **Paso 2**: Implementá la siguiente transformación en **Pandas** midiendo el tiempo de ejecución con `time.time()`:
    * Filtrar `monto &gt; 50.0`.
    * Crear la columna `monto_neto = (monto - descuento) * 1.21`.
    * Agrupar por `categoria` y calcular la suma de `monto_neto` y el promedio de `monto`.
  * **Paso 3**: Implementá exactamente la misma transformación en **Polars** usando `with_columns()`, `filter()` y `group_by().agg()`, midiendo el tiempo de ejecución.
  * **Paso 4**: Imprimí en consola ambos tiempos y la diferencia de aceleración (*speedup* xN).
3. Ejecutá tu script desde la terminal: `python3 practica/ej_37_polars_intro.py`