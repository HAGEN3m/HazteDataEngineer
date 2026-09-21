# 🐍 Lección 14: Manejo Avanzado de Fechas y Horarios (`datetime`, `timedelta`, `strftime`, `strptime`)

En la Ingeniería de Datos, el tiempo lo es todo: particionamiento de datos por fecha (`YYYY/MM/DD`), cálculo de ventanas de procesamiento (*SLA*), detección de registros duplicados y conversión entre zonas horarias.

En esta lección aprenderemos a dominar el módulo nativo **datetime**, la herramienta esencial para manipular fechas y horas de manera precisa.

---

## 1\. Clases Principales de `datetime`

El módulo `datetime` ofrece tres objetos fundamentales:

* **date**: Representa solo año, mes y día (`YYYY-MM-DD`).
* **time**: Representa solo hora, minuto, segundo y microsegundos (`HH:MM:SS`).
* **datetime**: Combina fecha y hora juntas en un solo objeto.

```
from datetime import datetime, date

# Fecha y hora actual del sistema
ahora = datetime.now()
print(f"Timestamp actual: {ahora}") # Ej: 2026-01-15 14:30:45.123456

# Fecha específica (Año, Mes, Día)
fecha_inicio = date(2026, 1, 1)
print(f"Fecha inicio: {fecha_inicio}") # 2026-01-01

```

---

## 2\. Conversión entre Texto y Fecha (`strptime` y `strftime`)

Los datos externos (CSVs, JSONs, APIs) siempre entregan las fechas como simples cadenas de texto (`str`). Para poder operar con ellas debemos convertirlas a objetos `datetime`.

### A. De Texto a Fecha (`strptime` \- *Parse*)

Sintaxis: `datetime.strptime(cadena_texto, formato)`

```
from datetime import datetime

fecha_str = "15/01/2026 18:30:00"
formato = "%d/%m/%Y %H:%M:%S"

# Convierte el texto a un objeto datetime real
fecha_obj = datetime.strptime(fecha_str, formato)
print(type(fecha_obj)) #