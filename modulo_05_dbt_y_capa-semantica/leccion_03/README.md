## 🚀 Lección 03: Testing, Documentación Automática y Linaje de Datos (*Data Lineage*) en dbt

En la **Lección 02** aprendimos a estructurar proyectos de dbt de forma modular en tres capas (`stg_`, `int_` y `marts_`) y a potenciar nuestro SQL utilizando **Jinja y Macros**.

Sin embargo, en entornos de producción Ssr/Senior, escribir código de transformación no es suficiente. Un pipeline analítico confiable exige **garantizar la calidad de los datos (** **Data Quality** **)**, exponer **documentación viva y actualizada** para los analistas de negocio y visualizar el **linaje de datos (** **Data Lineage** **)** para evaluar el impacto de cualquier cambio antes de llevarlo a producción (*Impact Analysis*).

En esta lección aprenderemos a configurar pruebas de calidad automatizadas, generar documentación sin esfuerzo manual y controlar la ejecución mediante el Grafo de Linaje de dbt.

---

## 1\. Quality Assurance: Testing en dbt

En dbt, las pruebas de calidad de datos son consultas SQL de validación que se ejecutan contra la base de datos. Existen dos tipos principales de tests: **Pruebas Genéricas (** **Generic Tests** **)** y **Pruebas Singulares (** **Singular Tests** **)**.

```
                               TIPOS DE TESTS EN DBT
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   PRUEBAS GENÉRICAS (Declarativas)               PRUEBAS SINGULARES (Custom SQL)
   • Definidas en YAML (`schema.yml`)             • Consultas SQL en carpeta `tests/`
   • `unique`, `not_null`                         • Regla: Si retorna 0 filas ➔ PASA
   • `accepted_values`, `relationships`           • Si retorna 1+ filas ➔ FALLA

```

---

### A. Pruebas Genéricas (*Generic Tests*)

Se declaran directamente en los archivos de configuración **schema.yml** dentro de la carpeta de modelos. dbt incluye cuatro pruebas out-of-the-box:

1. **unique**: Valida que no existan valores duplicados en la columna (ideal para claves primarias o *Surrogate Keys*).
2. **not\_null**: Valida que la columna no contenga valores `NULL`.
3. **accepted\_values**: Comprueba que todos los registros de la columna pertenezcan a una lista permitida de valores.
4. **relationships**: Valida la integridad referencial (*Foreign Key*) asegurando que los valores existan en la tabla relacionada.

#### Ejemplo de `schema.yml`:

```
version: 2

models:
  - name: stg_pos__ventas
    description: "Tabla de staging de ventas transaccionales limpias."
    columns:
      - name: transaccion_id
        description: "Clave primaria única de la transacción."
        tests:
          - unique
          - not_null

      - name: cliente_id
        description: "Identificador del cliente que realizó la compra."
        tests:
          - not_null
          - relationships:
              to: ref('stg_crm__clientes')
              field: cliente_id

      - name: estado
        description: "Estado actual de la transacción."
        tests:
          - accepted_values:
              values: ['COMPLETADA', 'PENDIENTE', 'CANCELADA']

```

---

### B. Pruebas Singulares (*Singular Tests*)

Son archivos `.sql` personalizados guardados en el directorio `tests/`.

* **Regla de Ejecución**: Escribís una consulta SQL que busque **los datos erróneos o anómalos**. Si la consulta devuelve **0 filas**, dbt considera que la prueba **PASÓ**. Si la consulta devuelve **1 o más filas**, la prueba **FALLÓ**.

#### Ejemplo: `tests/assert_monto_total_positivo.sql`

```
-- Test Singular: Detecta transacciones completadas con montos negativos o cero
SELECT
    transaccion_id,
    monto_usd
FROM {{ ref('fct_ventas') }}
WHERE monto_usd &lt;= 0;

```

---

## 2\. Documentación Automática y Catálogo de Datos

Mantener la documentación de un Data Warehouse en archivos de Word, Confluence o Notion es un anti-patrón: se desactualiza a los pocos días.

En dbt, **la documentación vive junto al código**. Al definir descripciones en los archivos `schema.yml`, dbt compila los metadatos de la base de datos (nombres de tablas, tipos de columnas, nulos, relaciones) y genera un portal web interactivo.

```
# 1. Extrae los metadatos de la base de datos y compila el catálogo
dbt docs generate

# 2. Inicia un servidor web local para navegar la documentación
dbt docs serve --port 8080

```

Ese portal muestra la descripción de cada modelo, sus columnas, los tests que tiene aplicados, el código SQL compilado e historial de cambios, y el **diagrama gráfico de linaje de datos**.

---

## 3\. Linaje de Datos (*Data Lineage*) y Selección Inteligente en CLI

Dado que dbt conoce las relaciones entre modelos a través de las funciones `ref()` y `source()`, construye un **Grafo Acíclico Dirigido (DAG)** que representa todo el flujo de datos desde la ingesta cruda hasta las métricas finales:

```
[ source('pos_system', 'raw_transactions') ]
                   │
                   ▼
         [ stg_pos__ventas ]
                   │
                   ▼
     [ int_ventas_enriquecidas ]
                   │
                   ▼
          [ fct_ventas_diarias ]

```

### ⚡ Selección Operativa en la Terminal mediante Linaje:

Podemos usar la sintaxis de grafos en la CLI de dbt para ejecutar o probar subconjuntos específicos de modelos sin procesar todo el Data Warehouse:

* **+modelo** **(Ancestros)**: Ejecuta el modelo y **todos los modelos aguas arriba** de los que depende.

```
dbt run --select +fct_ventas_diarias

```

* **modelo+** **(Descendientes)**: Ejecuta el modelo y **todos los modelos aguas abajo** que se ven afectados por él.

```
dbt run --select stg_pos__ventas+

```

* **Sintaxis Combinada (** **+modelo+** **)**: Ejecuta ancestros, el modelo y descendientes.

```
dbt run --select +int_ventas_enriquecidas+

```

---

## 🏋️‍♂️ Práctica de la Lección 03

1. Ubicate en la carpeta `practica/modulo_05/` de tu repositorio local.
2. Creá el archivo `ej_03_testing_and_lineage.py`.
3. Escribí un script Python que simule el **motor de validación de pruebas genéricas de dbt Core**:

```
import pandas as pd

# Simulación de un dataset cargado en la capa Staging
data_staging_ventas = pd.DataFrame([
    {"transaccion_id": 101, "cliente_id": "C-1", "monto": 150.0, "estado": "COMPLETADA"},
    {"transaccion_id": 102, "cliente_id": "C-2", "monto": 80.0,  "estado": "PENDIENTE"},
    {"transaccion_id": 103, "cliente_id": "C-3", "monto": 200.0, "estado": "COMPLETADA"},
    {"transaccion_id": 103, "cliente_id": "C-4", "monto": 50.0,  "estado": "INVALIDO"}, # Duplicado e inválido
    {"transaccion_id": 105, "cliente_id": None,  "monto": 120.0, "estado": "COMPLETADA"}  # Cliente NULL
])

# Evaluador de Pruebas Genéricas tipo dbt
class DBTTesterSimulator:
    @staticmethod
    def test_unique(df: pd.DataFrame, column: str) -&gt; bool:
        duplicates = df[df.duplicated(subset=[column], keep=False)]
        failed_count = len(duplicates)
        if failed_count &gt; 0:
            print(f"❌ TEST UNIQUE FAILED en '{column}': {failed_count} filas duplicadas encontradas.")
            return False
        print(f"✅ TEST UNIQUE PASSED en '{column}'")
        return True

    @staticmethod
    def test_not_null(df: pd.DataFrame, column: str) -&gt; bool:
        nulls = df[df[column].isnull()]
        failed_count = len(nulls)
        if failed_count &gt; 0:
            print(f"❌ TEST NOT_NULL FAILED en '{column}': {failed_count} valores NULL encontrados.")
            return False
        print(f"✅ TEST NOT_NULL PASSED en '{column}'")
        return True

    @staticmethod
    def test_accepted_values(df: pd.DataFrame, column: str, allowed_values: list) -&gt; bool:
        invalid = df[~df[column].isin(allowed_values)]
        failed_count = len(invalid)
        if failed_count &gt; 0:
            print(f"❌ TEST ACCEPTED_VALUES FAILED en '{column}': {failed_count} valores fuera de la lista permitida.")
            return False
        print(f"✅ TEST ACCEPTED_VALUES PASSED en '{column}'")
        return True

# Ejecución de la suite de pruebas
print("--- EJECUTANDO DBT TEST SIMULATION ---")
tester = DBTTesterSimulator()

tester.test_unique(data_staging_ventas, "transaccion_id")
tester.test_not_null(data_staging_ventas, "cliente_id")
tester.test_accepted_values(data_staging_ventas, "estado", ["COMPLETADA", "PENDIENTE", "CANCELADA"])

```

1. Agregá comentarios al final del archivo respondiendo:
  * **Consigna A**: Si un desarrollador modifica la lógica de cálculo dentro del modelo `stg_pos__ventas`, ¿qué comando de la CLI de dbt utilizando la sintaxis de linaje (`+` / `-`) debe ejecutar para compilar y correr pruebas **únicamente sobre** **stg\_pos\_\_ventas** **y todas las tablas que dependen de ella**?
  * **Consigna B**: Explicá por qué en un test singular de dbt (SQL) que devuelva filas significa que el test **falló**, mientras que no devolver filas significa que **pasó**.