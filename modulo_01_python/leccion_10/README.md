# 🐍 Lección 10: Lectura y Escritura de Archivos Básicos (`txt`, `csv` y Contexto `with`)

Con esta lección cerramos el **Bloque 1: Cimientos de Programación**. En Ingeniería de Datos, los pipelines leen y escriben información constantemente en discos locales, almacenamiento en la nube o servidores remotos.

En Python, la forma profesional y segura de interactuar con archivos es mediante la instrucción **with open()** (administrador de contexto).

---

## 1\. El Administrador de Contexto (`with open()`)

Antes se solía usar `f = open("archivo.txt")` y luego `f.close()`. El problema era que si el código fallaba antes de llegar a `f.close()`, el archivo quedaba "bloqueado" en memoria.

La sentencia **with** asegura que el archivo se cierre automáticamente en cuanto termina el bloque de código, incluso si ocurre un error durante la ejecución.

### Modos de apertura más comunes:

* **"r"** **(Read / Leer)**: Modo por defecto. Abre el archivo para lectura. Falla con error si el archivo no existe.
* **"w"** **(Write / Escribir)**: Abre para escritura. **¡Cuidado! Sobrescribe y borra** todo el contenido previo del archivo si ya existía. Si no existe, lo crea.
* **"a"** **(Append / Anexar)**: Abre para escribir al final del archivo sin borrar lo existente.
* **encoding="utf-8"**: Especifica la codificación para evitar problemas con acentos y caracteres especiales (como la `ñ`).

---

## 2\. Leer y Escribir Archivos de Texto (`.txt`)

```
# 1. Escribir en un archivo de texto
with open("notas.txt", mode="w", encoding="utf-8") as archivo:
    archivo.write("Línea 1: Ingesta de datos iniciada.\n")
    archivo.write("Línea 2: Registros procesados con éxito.\n")

# 2. Leer un archivo de texto línea por línea
with open("notas.txt", mode="r", encoding="utf-8") as archivo:
    for linea in archivo:
        print(f"📖 Leyendo: {linea.strip()}")  # .strip() remueve el salto de línea \n

```

---

## 3\. Manejo Básico de Archivos CSV (`import csv`)

El formato **CSV** (*Comma-Separated Values*) es el estándar universal para mover datos tabulares. Python incluye el módulo nativo `csv` para manipularlos sin necesidad de instalar librerías externas.

### Usar `csv.DictWriter` para escribir CSVs estructurados

```
import csv

datos = [
    {"id": 101, "cliente": "Juan", "monto": 150.5},
    {"id": 102, "cliente": "María", "monto": 200.0}
]

columnas = ["id", "cliente", "monto"]

with open("ventas.csv", mode="w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=columnas)
    writer.writeheader()   # Escribe la fila de cabecera con los nombres de columnas
    writer.writerows(datos)  # Escribe todas las filas de datos

```

### Usar `csv.DictReader` para leer CSVs como diccionarios

```
import csv

with open("ventas.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for fila in reader:
        print(f"Cliente: {fila['cliente']} | Monto: ${fila['monto']}")

```

---

## 🏋️‍♂️ Práctica de la Lección 10

1. Creá el archivo `ej_10_archivos.py` dentro de la carpeta `leccion_10/`.
2. Escribí un script que realice un ciclo completo de **generación, lectura y filtrado de un log de auditoría**:
  * Definí una lista de diccionarios con eventos del pipeline:

```
eventos_raw = [
    {"timestamp": "2026-01-01 10:00:00", "modulo": "Ingesta", "nivel": "INFO", "mensaje": "Conexión exitosa"},
    {"timestamp": "2026-01-01 10:01:15", "modulo": "Transformación", "nivel": "ERROR", "mensaje": "Monto negativo detectado"},
    {"timestamp": "2026-01-01 10:02:30", "modulo": "Carga", "nivel": "WARNING", "mensaje": "Tiempo de respuesta elevado"}
]

```

1. Guardá esos datos en un archivo llamado `log_ejecucion.csv` dentro de la carpeta de trabajo usando `csv.DictWriter`.
2. Leé el archivo `log_ejecucion.csv` recién creado usando `csv.DictReader`.
3. Filtrá los eventos: si el `nivel` es `"ERROR"` o `"WARNING"`, escribí ese mensaje en un archivo de texto llamado `alertas.txt` usando `with open(..., "a")`.
4. Verificá que `alertas.txt` contenga únicamente los eventos críticos formateados.
5. Ejecutá tu script en la terminal: `python3 leccion_10/ej_10_archivos.py`