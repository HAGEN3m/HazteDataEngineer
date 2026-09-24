# 🐍 Lección 14: Manejo Avanzado de Fechas y Horarios (`datetime`, `timedelta`, `strftime`, `strptime`)

En la Ingeniería de Datos, el tiempo lo es todo: particionamiento de datos por fecha (`YYYY/MM/DD`), cálculo de ventanas de procesamiento (*SLA*), detección de registros duplicados y conversión entre zonas horarias. 

En esta lección aprenderemos a dominar el módulo nativo **`datetime`**, la herramienta esencial para manipular fechas y horas de manera precisa.

---

## 1. Clases Principales de `datetime`

El módulo `datetime` ofrece tres objetos fundamentales:
* **`date`**: Representa solo año, mes y día (`YYYY-MM-DD`).
* **`time`**: Representa solo hora, minuto, segundo y microsegundos (`HH:MM:SS`).
* **`datetime`**: Combina fecha y hora juntas en un solo objeto.

```python
from datetime import datetime, date

# Fecha y hora actual del sistema
ahora = datetime.now()
print(f"Timestamp actual: {ahora}") # Ej: 2026-01-15 14:30:45.123456

# Fecha específica (Año, Mes, Día)
fecha_inicio = date(2026, 1, 1)
print(f"Fecha inicio: {fecha_inicio}") # 2026-01-01
```

---

## 2. Conversión entre Texto y Fecha (`strptime` y `strftime`)

Los datos externos (CSVs, JSONs, APIs) siempre entregan las fechas como simples cadenas de texto (`str`). Para poder operar con ellas debemos convertirlas a objetos `datetime`.

### A. De Texto a Fecha (`strptime` - *Parse*)
Sintaxis: `datetime.strptime(cadena_texto, formato)`

```python
from datetime import datetime

fecha_str = "15/01/2026 18:30:00"
formato = "%d/%m/%Y %H:%M:%S"

# Convierte el texto a un objeto datetime real
fecha_obj = datetime.strptime(fecha_str, formato)
print(type(fecha_obj)) # <class 'datetime.datetime'>
```

### B. De Fecha a Texto (`strftime` - *Format*)
Sintaxis: `objeto_datetime.strftime(formato)`

```python
# Convertimos el objeto datetime a un formato estándar de partición de Data Lake
particion = fecha_obj.strftime("year=%Y/month=%m/day=%d")
print(particion) # "year=2026/month=01/day=15"
```

### 🔤 Códigos de Formato más comunes:
* `%Y`: Año completo con 4 dígitos (ej: `2026`).
* `%m`: Mes con 2 dígitos (`01` a `12`).
* `%d`: Día del mes con 2 dígitos (`01` a `31`).
* `%H`: Hora en formato 24hs (`00` a `23`).
* `%M`: Minutos (`00` a `59`).
* `%S`: Segundos (`00` a `59`).

---

## 3. Aritmética de Fechas con `timedelta`

Para sumar o restar días, horas o minutos a una fecha, usamos el objeto **`timedelta`**:

```python
from datetime import datetime, timedelta

fecha_actual = datetime.now()

# Restar 7 días (definir ventana de la última semana)
hace_una_semana = fecha_actual - timedelta(days=7)

# Sumar 3 horas a la fecha actual
en_tres_horas = fecha_actual + timedelta(hours=3)

print(f"Hace 7 días fue: {hace_una_semana.strftime('%Y-%m-%d')}")
```

### Restar dos fechas
Al restar dos objetos `datetime`, obtenemos un `timedelta` que representa la diferencia exacta entre ambos momentos:

```python
inicio_pipeline = datetime(2026, 1, 15, 10, 0, 0)
fin_pipeline = datetime(2026, 1, 15, 10, 15, 30)

duracion = fin_pipeline - inicio_pipeline
print(f"Duración total: {duracion.total_seconds()} segundos") # 930.0 segundos
```

---

## 4. Timestamps UTC (Buenas Prácticas de Producción)

En servidores distribuidos (nube, Airflow, bases de datos), **nunca debes usar la hora local** del servidor porque varía según el país o el horario de verano. Todo pipeline profesional debe operar en **UTC** (*Coordinated Universal Time*):

```python
from datetime import datetime, timezone

# Fecha y hora actual en UTC
ahora_utc = datetime.now(timezone.utc)
print(f"Timestamp UTC: {ahora_utc.isoformat()}") 
# Salida en formato ISO-8601: 2026-01-15T14:30:45.123456+00:00
```

---

## 🏋️‍♂️ Práctica de la Lección 14

1. Creá el archivo `ej_14_fechas.py` dentro de la carpeta `leccion_14/`.
2. Escribí un script de **filtrado por ventana de tiempo y cálculo de SLA**:
   * Definí una lista de logs recibidos desde un servidor:
     ```python
     logs_servidor = [
         {"id": 1, "timestamp_str": "2026-01-10 08:30:00", "estado": "OK"},
         {"id": 2, "timestamp_str": "2026-01-14 12:00:00", "estado": "ERROR"},
         {"id": 3, "timestamp_str": "2026-01-15 09:15:00", "estado": "OK"},
     ]
     ```
   * Definí la fecha de referencia del procesamiento: `fecha_referencia = datetime(2026, 1, 15, 10, 0, 0)`.
   * Para cada log:
     1. Convertí `timestamp_str` a un objeto `datetime` con `strptime`.
     2. Calculá la diferencia en días entre la `fecha_referencia` y la fecha del log.
     3. Si la diferencia es de **2 días o menos**, considerá el log dentro de la ventana activa.
     4. Si el log está activo y su estado es `"ERROR"`, imprimí una alerta formateada:  
        `"🚨 ALERTA: Log #2 con estado ERROR detectado dentro de la ventana de 48hs (Fecha: 2026-01-14)"`
3. Ejecutá tu script desde la terminal:  
   `python3 leccion_14/ej_14_fechas.py`

---
