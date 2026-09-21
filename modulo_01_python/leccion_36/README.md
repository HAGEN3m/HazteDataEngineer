# 🐍 Lección 36: GroupBy Avanzado, Agregaciones Compuestas y Funciones de Ventana en Pandas (`transform()`, `pivot_table()`, `melt()`)

En la **Lección 35** aprendimos a limpiar y transformar datasets usando vectorización y `df.assign()`. Ahora daremos el paso hacia el análisis agregativo y el remodelado de datos (*Data Reshaping*).

En SQL, las agregaciones con `GROUP BY` y las **Funciones de Ventana (** **OVER (PARTITION BY ...)** **)** son fundamentales para responder preguntas analíticas complejas. En Pandas, el módulo `.groupby()` combinado con `.agg()`, `.transform()`, `.pivot_table()` y `.melt()` nos otorga exactamente ese mismo poder expresivo.

---

## 1\. GroupBy y Agregaciones Compuestas con `.agg()`

Cuando agrupás datos por una o más dimensiones, rara vez querés aplicar una sola agregación. Usando la sintaxis de diccionario dentro de **.agg()**, podés aplicar múltiples funciones de agregación a diferentes columnas simultáneamente:

```
import pandas as pd

df_ventas = pd.DataFrame({
    "region": ["NORTE", "NORTE", "SUR", "SUR", "NORTE"],
    "categoria": ["ELECTRONICA", "HOGAR", "ELECTRONICA", "HOGAR", "ELECTRONICA"],
    "monto": [150.0, 200.0, 300.0, 120.0, 450.0],
    "descuento": [10.0, 0.0, 25.0, 5.0, 50.0]
})

# Agregación múltiple con renombrado directo de columnas
resumen_agrupado = (
    df_ventas
    .groupby(["region", "categoria"], as_index=False)
    .agg(
        total_ventas=("monto", "sum"),
        promedio_monto=("monto", "mean"),
        descuento_maximo=("descuento", "max"),
        cantidad_transacciones=("monto", "count")
    )
)

```

&gt; 💡 **Tip de Producción**: El argumento `as_index=False` evita que las columnas de agrupación se conviertan en el índice del DataFrame, entregando un DataFrame plano listo para exportar o insertar en SQL.

---

## 2\. Funciones de Ventana en Pandas con `.transform()`

En SQL, las funciones de ventana (*Window Functions*) como `SUM(monto) OVER (PARTITION BY region)` calculan un valor agrupado pero **mantienen la cantidad original de filas del DataFrame**, adosando la métrica grupal a cada registro individual.

En Pandas, logramos este comportamiento exacto usando **.transform()**:

```
# Calcular el total de ventas por región y adosarlo a cada fila original
df_ventas["total_region"] = (
    df_ventas
    .groupby("region")["monto"]
    .transform("sum")
)

# Ahora podemos calcular vectorizadamente el % de participación de cada venta sobre su región
df_ventas["porcentaje_participacion"] = (
    (df_ventas["monto"] / df_ventas["total_region"]) * 100
).round(2)

print(df_ventas[["region", "monto", "total_region", "porcentaje_participacion"]])

```

### Salida:

```
  region  monto  total_region  porcentaje_participacion
0  NORTE  150.0         800.0                     18.75
1  NORTE  200.0         800.0                     25.00
2    SUR  300.0         420.0                     71.43
3    SUR  120.0         420.0                     28.57
4  NORTE  450.0         800.0                     56.25

```

---

## 3\. Remodelado de Datos: `pivot_table()` (Wide) vs. `melt()` (Long)

En la Ingeniería de Datos es habitual convertir estructuras entre formato ancho (*Wide Format*, ideal para reportes ejecutivos) y formato largo (*Long/Unpivoted Format*, ideal para bases de datos relacionales e ingesta en Data Warehouses).

```
 ┌────────────────┐                           ┌────────────────┐
 │  LONG FORMAT   │  ──── pivot_table() ────&gt; │  WIDE FORMAT   │
 │ (Bases de Data)│  &lt;────── melt() ───────── │ (Reportes/BI)  │
 └────────────────┘                           └────────────────┘

```

### A. De Long a Wide: `pd.pivot_table()`

Remodela filas en columnas cruzadas mediante funciones de agregación:

```
df_pivot = df_ventas.pivot_table(
    index="region",
    columns="categoria",
    values="monto",
    aggfunc="sum",
    fill_value=0.0
).reset_index()

print(df_pivot)
# Columnas resultantes: region, ELECTRONICA, HOGAR

```

### B. De Wide a Long: `pd.melt()`

Despivota columnas para volver a normalizar un esquema en formato largo:

```
df_long = pd.melt(
    df_pivot,
    id_vars=["region"],
    value_vars=["ELECTRONICA", "HOGAR"],
    var_name="categoria",
    value_name="monto_total"
)

```

---

## 🏋️‍♂️ Práctica de la Lección 36

1. Creá el archivo `ej_36_pandas_advanced.py` dentro de la carpeta `practica/`.
2. Escribí un script para **analizar y normalizar transacciones de ventas**:
  * Dataset sintético de prueba:

```
import pandas as pd

df_transacciones = pd.DataFrame({
    "sucursal": ["CENTRO", "CENTRO", "NORTE", "NORTE", "CENTRO", "NORTE"],
    "vendedor": ["Ana", "Pedro", "Maria", "Juan", "Ana", "Maria"],
    "monto": [1200.0, 800.0, 2500.0, 1100.0, 1500.0, 3000.0],
    "mes": ["ENE", "ENE", "ENE", "ENE", "FEB", "FEB"]
})

```

1. **Consigna 1 (GroupBy &amp; Agg)**: Generá un DataFrame agrupado por `sucursal` que calcule:
  * `monto_total` (`sum`)
  * `ticket_promedio` (`mean`)
  * `total_operaciones` (`count`)
2. **Consigna 2 (Window Function con** **.transform()** **)**: Agregá al DataFrame original `df_transacciones` una columna llamada `monto_promedio_sucursal` que contenga el promedio de ventas de la sucursal correspondiente y una columna `diferencia_vs_promedio` (`monto - monto_promedio_sucursal`).
3. **Consigna 3 (Pivot Table)**: Creá una tabla pivote que muestre las sucursales en las filas (`index`), los meses en las columnas (`columns`) y la suma total de ventas como valores (`values`), rellenando nulos con `0.0`.
4. Ejecutá tu script desde la terminal: `python3 practica/ej_36_pandas_advanced.py`