# 🐍 Lección 17: Logging Profesional en Python (`logging`)

En las primeras lecciones usamos la función `print()` para mostrar mensajes en pantalla. Sin embargo, en un entorno de producción de Ingeniería de Datos (donde los pipelines corren de forma desatendida en la nube, contenedores Docker o orquestadores como Apache Airflow), **print()** **es totalmente insuficiente**.

El módulo nativo **logging** permite registrar todo lo que sucede en tu pipeline con fecha, hora, nivel de severidad y módulo de origen, guardando ese historial en archivos de registro (*log files*) o sistemas centralizados de monitoreo (Datadog, AWS CloudWatch, ELK).

---

## 1\. Niveles de Severidad de Logs

`logging` clasifica los eventos en 5 niveles jerárquicos según la gravedad del suceso:

| Nivel        | Valor | ¿Cuándo usarlo en Data Engineering?                                                                                                |
| ------------ | ----- | ---------------------------------------------------------------------------------------------------------------------------------- |
| **DEBUG**    | 10    | Información detallada para diagnóstico en desarrollo (ej: cantidad de filas antes de filtrar).                                     |
| **INFO**     | 20    | Confirmación de que el pipeline avanza según lo esperado (ej: *"Conexión a BD establecida"*, *"10,000 filas procesadas"*).         |
| **WARNING**  | 30    | Ocurrió algo inesperado pero el proceso puede continuar (ej: *"Un registro vino sin email y fue omitido"*).                        |
| **ERROR**    | 40    | Ocurrió un fallo grave que impidió completar un paso específico (ej: *"Falló la consulta SQL en la tabla de facturas"*).           |
| **CRITICAL** | 50    | Error fatal que detiene la ejecución completa del sistema (ej: *"Falta la base de datos principal"*, *"Sin credenciales de AWS"*). |

---

## 2\. Configuración Básica de `logging` (`logging.basicConfig`)

Para activar y dar formato al sistema de registros usamos `logging.basicConfig()`:

```
import logging

# Configuración inicial del logger
logging.basicConfig(
    level=logging.INFO,  # Captura mensajes de nivel INFO hacia arriba (ignora DEBUG)
    format="%(asctime)s [%(levelname)s] (%(module)s): %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pipeline_ejecucion.log", encoding="utf-8"), # Guarda en archivo
        logging.StreamHandler()                                         # Muestra en consola
    ]
)

# Ejemplos de emisión de logs
logging.info("🚀 Pipeline de Ingesta iniciado.")
logging.warning("⚠️ La API respondió con latencia elevada (1.5s).")
logging.error("🔴 Falló la escritura del archivo Parquet.")

```

### 📄 Salida generada en consola y en `pipeline_ejecucion.log`:

```
2026-01-15 14:30:00 [INFO] (main): 🚀 Pipeline de Ingesta iniciado.
2026-01-15 14:30:02 [WARNING] (main): ⚠️ La API respondió con latencia elevada (1.5s).
2026-01-15 14:30:05 [ERROR] (main): 🔴 Falló la escritura del archivo Parquet.

```

---

## 3\. Captura Automática de Excepciones (`exc_info=True`)

Cuando capturás un error dentro de un bloque `try / except`, podés pasar el argumento `exc_info=True` (o usar directamente `logging.exception()`). Esto adjunta automáticamente el rastreo completo del error (*traceback*) al archivo de log, lo cual es invaluable para depurar fallos en producción:

```
import logging

try:
    resultado = 100 / 0
except ZeroDivisionError:
    # Registra el mensaje y graba la traza completa de la excepción
    logging.exception("🔴 Error crítico durante el cálculo del promedio:")

```

---

## 4\. Buenas Prácticas de Logging en Producción

1. **Jamás loguear información sensible (PII/Credenciales)**: Nunca escribas en los logs contraseñas, tokens de API, números de tarjeta o datos personales de usuarios.
2. **Usar formateo estandarizado**: Mantener el mismo patrón de fecha y severidad en todos los microservicios y pipelines.
3. **Mapear errores con contexto**: En lugar de loguear `"Error"`, logueá `"Error al procesar el lote #5021 en la tabla 'fact_ventas'"`.

---

## 🏋️‍♂️ Práctica de la Lección 17

1. Creá el archivo `ej_17_logging.py` dentro de la carpeta `practica/`.
2. Escribí un script que simule el proceso de ingesta y transformación de un dataset con logging habilitado:
  * Configurá `logging.basicConfig` para que escriba tanto en la terminal como en el archivo `practica/ejecucion_pipeline.log` con nivel `DEBUG` y formato con timestamp.
  * Definí la función `transformar_lote_datos(lote: list) -&gt; list`:
    * Emití un log `logging.info` indicando cuántos registros llegaron.
    * Recorré la lista de registros. Si un registro tiene un monto negativo o nulo (`None`), emití un `logging.warning` indicando el ID del registro afectado y omitilo.
    * Si el registro es válido, sumale un 10% de impuesto y agregalo a una lista procesada.
    * Si ocurre una excepción inesperada durante la conversión, capturala con `except Exception:` y logueala usando `logging.exception()`.
    * Emití un `logging.info` al finalizar con la cantidad total de registros transformados con éxito.
  * Ejecutá la función con este dataset de prueba:

```
lote_prueba = [
    {"id": 101, "monto": 150.0},
    {"id": 102, "monto": -50.0},
    {"id": 103, "monto": None},
    {"id": 104, "monto": 300.0}
]

```

1. Ejecutá tu script desde la terminal: `python3 practica/ej_17_logging.py`
2. Verificá que se haya creado el archivo `practica/ejecucion_pipeline.log` con el historial completo de la corrida.