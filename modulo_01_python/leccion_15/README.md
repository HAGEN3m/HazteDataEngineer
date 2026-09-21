# 🐍 Lección 11: Profundizando en Funciones (Scope, `*args`, `**kwargs` y Retorno Múltiple)

¡Damos inicio al **Bloque 2: Programación Modular y Robusta**! En la Lección 08 aprendimos los fundamentos de las funciones. En esta lección daremos un salto de calidad aprendiendo a manejar el alcance de las variables (*scope*), retornar múltiples métricas a la vez y diseñar funciones ultra flexibles usando `*args` y `**kwargs`.

---

## 1\. Scope de Variables (Ámbito Global vs. Local)

El **Scope** (alcance) define en qué partes de tu código una variable es accesible:

* **Scope Local**: Las variables creadas **dentro de una función** solo existen mientras esa función se está ejecutando. Al terminar la función, esas variables se borran de la memoria.
* **Scope Global**: Las variables creadas en la raíz del script están disponibles en todo el archivo.

```
 t = "ARS" # Variable Global

def calcular_monto():
    monto_local = 1500.0 # Variable Local
    print(f"Monto: ${monto_local} {moneda_global}")

calcular_monto()

# 🔴 Error: NameError: name 'monto_local' is not defined
# print(monto_local) 

```

&gt; 💡 **Regla de oro de producción**: Evitá modificar variables globales dentro de funciones. Toda entrada a una función debe pasar por sus parámetros y toda salida debe devolverse con `return`.

---

## 2\. Retorno Múltiple de Valores (Desempaquetado)

Una función en Python puede devolver más de un valor en un solo `return`. Por debajo, Python empaqueta esos valores en una **Tupla**, que luego podés desempaquetar directamente en variables individuales:

```
def obtener_metricas_monto(lista_montos):
    total = sum(lista_montos)
    promedio = total / len(lista_montos)
    monto_maximo = max(lista_montos)
    return total, round(promedio, 2), monto_maximo # Devuelve una tupla

# Desempaquetado directo de variables
total_ingresos, promedio_diario, venta_pico = obtener_metricas_monto([100.0, 250.0, 400.0, 150.0])

print(f"Total: ${total_ingresos} | Promedio: ${promedio_diario} | Máximo: ${venta_pico}")

```

---

## 3\. Argumentos Posicionales Indeterminados (`*args`)

Cuando querés que una función acepte **cualquier cantidad de argumentos posicionales**, usás `*args` (el asterisco es la clave). Dentro de la función, `args` se comporta como una **tupla** con todos los valores recibidos:

```
def sumar_montos_variables(*args):
    # args es una tupla: (100, 200, 300...)
    total = sum(args)
    return total

print(sumar_montos_variables(100, 200))          # 300
print(sumar_montos_variables(50, 150, 200, 500)) # 900

```

---

## 4\. Argumentos Clave Indeterminados (`**kwargs`)

Cuando querés recibir **parámetros nombrados opcionales o dinámicos**, usás `**kwargs` (*keyword arguments*). Dentro de la función, `kwargs` se comporta como un **diccionario**:

```
def construir_query_sql(tabla, **kwargs):
    # kwargs es un diccionario con los filtros recibidos
    query = f"SELECT * FROM {tabla}"
    
    if kwargs:
        filtros = []
        for columna, valor in kwargs.items():
            filtros.append(f"{columna} = '{valor}'")
        query += " WHERE " + " AND ".join(filtros)
        
    return query

# 1. Sin filtros adicionales
print(construir_query_sql("fact_ventas")) 
# SELECT * FROM fact_ventas

# 2. Con filtros dinámicos mediante kwargs
print(construir_query_sql("fact_ventas", estado="COMPLETADA", pais="AR")) 
# SELECT * FROM fact_ventas WHERE estado = 'COMPLETADA' AND pais = 'AR'

```

---

## 🏋️‍♂️ Práctica de la Lección 11

1. Creá el archivo `ej_11_funciones_avanzadas.py` dentro de la carpeta `practica/`.
2. Escribí un script para **analizar y auditar lotes de datos flexibles**:
  * Definí la función `auditar_pipeline(nombre_pipeline, *registros, **metadata)`:
    * El parámetro `nombre_pipeline` recibe el nombre del proceso (string).
    * `*registros` recibe una cantidad variable de montos numéricos.
    * `**metadata` recibe pares de clave-valor opcionales (ej: `entorno="PROD"`, `version="1.2.0"`).
    * La función debe:
      1. Calcular el total acumulado y la cantidad de registros procesados desde `*registros`.
      2. Si no se pasaron registros, total es `0.0` y cantidad es `0`.
      3. Retornar **dos valores**: el diccionario consolidado de resumen y un booleano `es_exitoso` (que es `True` si la cantidad de registros es mayor a 0).
  * Probá llamar a la función pasando:
    * Pipeline: `"ingesta_diaria"`
    * Registros: `150.50, 300.00, 450.25, 100.00`
    * Metadata: `entorno="PROD"`, `ejecutado_por="airflow"`
  * Imprimí el resultado desempaquetando el retorno doble y verificá cómo se construyen el resumen y la metadata.
3. Ejecutá tu script en la terminal: `python3 practica/ej_11_funciones_avanzadas.py`