# 🚀 Lección 04: Capa Semántica con dbt MetricFlow: Métricas de Negocio Centralizadas

En las lecciones anteriores dominamos la estructuración modular de modelos (`stg_`, `int_` y `marts_`) con Jinja y Macros, así como la automatización de pruebas de calidad (*Data Testing*) y la generación del grafo de linaje (*Data Lineage*).

Sin embargo, a medida que una organización escala, surge un problema crítico de gobernanza: **diferentes equipos definen y calculan las mismas métricas de formas distintas**[1]. Finanzas calcula la "Tasa de Retención" usando pagos de suscripciones activas, mientras Producto la mide según la interacción en la app[2]. Cada analista escribe su propio SQL en tableros aislados de PowerBI, Tableau o Looker, provocando la llamada "Torre de Babel Analítica"[1][3].

En esta lección aprenderemos a resolver este problema mediante la **Capa Semántica (** **Semantic Layer** **)** utilizando **dbt MetricFlow**, el motor declarativo para centralizar la definición de métricas en código versionado[1].

---

## 1\. ¿Qué es una Capa Semántica y por qué es indispensable?

Una **Capa Semántica** es una capa de abstracción ubicada entre las tablas transformadas en el Data Warehouse y los usuarios finales o herramientas de visualización[3][6].

```
       SIN CAPA SEMÁNTICA (Métricas Fragmentadas)
  ┌─────────────────────────────────────────────────────────┐
  │ Data Warehouse (Gold Layer)                             │
  └─────────────┬─────────────────────────┬─────────────────┘
                │ SQL Ad-Hoc              │ SQL Ad-Hoc
                ▼                         ▼
        [ Tableau (Finanzas) ]   [ Power BI (Producto) ]
        Métrica: 'Revenue'       Métrica: 'Revenue'
        (Calculada diferente)    (Calculada diferente)

       CON CAPA SEMÁNTICA (dbt MetricFlow - Single Source of Truth)
  ┌─────────────────────────────────────────────────────────┐
  │ Data Warehouse (Gold Layer)                             │
  └─────────────────────────────┬───────────────────────────┘
                                │
                                ▼
  ┌─────────────────────────────────────────────────────────┐
  │ CAPA SEMÁNTICA CENTRALIZADA (dbt MetricFlow YAML)        │
  │ • Define 'Revenue', 'Churn', 'Retención' UNA SOLA VEZ   │
  └──────┬──────────────────────┬────────────────────┬──────┘
         │ API (JDBC/GraphQL)   │ API                │ API
         ▼                      ▼                    ▼
  [ Tableau ]            [ Power BI ]           [ App / Python ]

```

### Ventajas Clave de la Capa Semántica:

1. **Consistencia Absoluta**: Las métricas clave de la empresa se definen **una sola vez en YAML** y todos los departamentos consumen exactamente la misma lógica[3].
2. **Consultas SQL Automáticas y Dinámicas**: En lugar de escribir JOINs complejos manualmente, MetricFlow construye el código SQL optimizado en tiempo de consulta (*on-the-fly*) según las dimensiones y filtros solicitados[5].
3. **Desacoplamiento de Herramientas de BI**: Si la empresa cambia de software de BI, las métricas permanecen intactas en la capa semántica versionada en Git[2].

---

## 2\. Componentes Fundamentales de dbt MetricFlow

MetricFlow estructura la capa semántica en dos elementos principales declarados en archivos `.yml`: **Semantic Models** y **Metrics**[7][8].

### A. Modelos Semánticos (`semantic_models`)

Un **Semantic Model** se construye directamente sobre un modelo físico existente de dbt (relación 1:1) y describe sus claves, dimensiones y agregaciones numéricas[9]:

1. **entities**: Son las claves primarias, foráneas o únicas (`primary`, `foreign`, `unique`) que permiten a MetricFlow realizar `JOINs` automáticos entre tablas sin provocar duplicaciones (*fan-out*)[8][10].
2. **measures**: Son los bloques numéricos básicos sobre los cuales se aplican agregaciones agregadas (`sum`, `count`, `min`, `max`, `median`)[8][11].
3. **dimensions**: Atributos categóricos o temporales (`categorical`, `time`) utilizados para cortar o filtrar las métricas (con granularidades como `day`, `week`, `month`)[8][12].

#### Ejemplo de `semantic_models/sm_ventas.yml`:

```
semantic_models:
  - name: sm_fact_ventas
    description: "Modelo semántico para la tabla de hechos de ventas transaccionales."
    model: ref('fct_ventas')
    defaults:
      agg_time_dimension: fecha_transaccion

    entities:
      - name: venta_id
        type: primary
      - name: cliente_id
        type: foreign
      - name: producto_id
        type: foreign

    measures:
      - name: ingresos_brutos
        description: "Suma del monto total ingresado por ventas."
        expr: monto_total_usd
        agg: sum

      - name: cantidad_ordenes
        description: "Conteo total de transacciones registradas."
        expr: venta_id
        agg: count_distinct

    dimensions:
      - name: fecha_transaccion
        type: time
        type_params:
          time_granularity: day

```

---

### B. Definición de Métricas (`metrics`)

Las **Métricas** son las reglas de negocio de alto nivel construidas sobre las medidas de los modelos semánticos[8][13]. MetricFlow admite varios tipos de métricas:

* **simple**: Apunta directamente a una medida definida[14].
* **cumulative**: Acumulados continuos o sobre una ventana de tiempo específica (ej. *Year-to-Date* o *Rolling 7 days*)[14][15].
* **ratio**: Divide un numerador por un denominador (ej. Tasa de Conversión o Ticket Promedio)[16].
* **derived**: Expresión matemática que combina múltiples métricas existentes (ej. `Ingresos - Costos`)[16].

#### Ejemplo de `models/semantic/metrics.yml`:

```
metrics:
  # 1. Métrica Simple
  - name: total_ingresos
    label: "Ingresos Totales (USD)"
    type: simple
    type_params:
      measure: ingresos_brutos

  # 2. Métrica Ratio (División protegida)
  - name: ticket_promedio
    label: "Ticket Promedio por Venta"
    type: ratio
    type_params:
      numerator: ingresos_brutos
      denominator: cantidad_ordenes

  # 3. Métrica Derivada
  - name: margen_ganancia
    label: "Margen de Ganancia Neta"
    type: derived
    type_params:
      expr: total_ingresos - costo_total
      metrics:
        - name: total_ingresos
        - name: costo_total

```

---

## 3\. ¿Cómo Consultan los Usuarios la Capa Semántica?

Cuando un analista de negocio en PowerBI, Tableau o Hex selecciona la métrica `"Ticket Promedio"` cortada por `"Categoría de Producto"` y `"Mes"`[17]:

1. La herramienta de BI envía la solicitud a la **API de dbt Semantic Layer** (a través de conectores **JDBC Apache Arrow Flight SQL** o **GraphQL**)[18].
2. **MetricFlow** analiza el grafo de modelos semánticos, identifica de qué tablas extraer los datos y **construye automáticamente la consulta SQL con los** **JOINs** **y** **GROUP BY** **correctos**[5][20].
3. La consulta se ejecuta directamente *in-warehouse* y devuelve los resultados consolidados a la herramienta de visualización[5].

---

## 🏋️‍♂️ Práctica de la Lección 04

1. Ubicate en la carpeta `practica/modulo_05/` de tu repositorio local.
2. Creá el archivo `ej_04_capa_semantica.py`.
3. Escribí un script Python que simule el **motor de resolución semántica y construcción dinámica de SQL de MetricFlow**:

```
# Simulación del motor de resolución de MetricFlow
class MetricFlowSimulator:
    def __init__(self):
        self.semantic_models = {}
        self.metrics = {}

    def register_semantic_model(self, name: str, table_ref: str, measures: dict, dimensions: list):
        self.semantic_models[name] = {
            "table": table_ref,
            "measures": measures,
            "dimensions": dimensions
        }

    def register_metric(self, name: str, metric_type: str, numerator: str = None, denominator: str = None):
        self.metrics[name] = {
            "type": metric_type,
            "numerator": numerator,
            "denominator": denominator
        }

    def generate_sql(self, metric_name: str, group_by_dimension: str) -&gt; str:
        metric = self.metrics.get(metric_name)
        if not metric:
            raise ValueError(f"Métrica '{metric_name}' no declarada en la Capa Semántica.")

        if metric["type"] == "ratio":
            num_measure = metric["numerator"]
            den_measure = metric["denominator"]
            
            # MetricFlow resuelve la consulta uniendo medidas y dimensiones automáticamente
            sql = f"""-- SQL Generado Dinámicamente por dbt MetricFlow
SELECT
    {group_by_dimension},
    SUM({num_measure}) AS {num_measure},
    COUNT({den_measure}) AS {den_measure},
    ROUND(SUM({num_measure})::DECIMAL / NULLIF(COUNT({den_measure}), 0), 2) AS {metric_name}
FROM analytics.fct_ventas
GROUP BY {group_by_dimension}
ORDER BY {metric_name} DESC;"""
            return sql
        return "-- Métrica no soportada en simulación"

# Prueba de simulación
mf = MetricFlowSimulator()

# 1. Registrar modelo semántico base
mf.register_semantic_model(
    name="sm_fact_ventas",
    table_ref="fct_ventas",
    measures={"monto_total": "sum", "venta_id": "count"},
    dimensions=["pais_cliente", "categoria_producto", "fecha_mes"]
)

# 2. Registrar métrica tipo ratio (Ticket Promedio)
mf.register_metric(
    name="ticket_promedio",
    metric_type="ratio",
    numerator="monto_total",
    denominator="venta_id"
)

# 3. Solicitar la métrica cortada por la dimensión 'pais_cliente'
sql_compilado = mf.generate_sql("ticket_promedio", group_by_dimension="pais_cliente")
print(sql_compilado)

```

1. Agregá comentarios al final del archivo respondiendo:
  * **Consigna A**: ¿Qué diferencia fundamental existe entre calcular una métrica mediante un cálculo `SUM()` manual en un archivo `.sql` de dbt vs. declararla en la **Capa Semántica con MetricFlow**?[5][21]
  * **Consigna B**: ¿Cómo previene MetricFlow que la métrica de "Ingresos" se calcule de forma contradictoria entre el equipo de Finanzas y el equipo de Marketing?