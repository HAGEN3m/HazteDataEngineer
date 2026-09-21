# 🐍 Módulo 01 — Lección 0.1: Tu Primera Línea de Código (`print` y Comentarios)

&gt; *El comienzo de todo programador: enseñarle a la computadora a comunicarse con vos a través de la pantalla.*

---

## 📌 1\. ¿Qué es `print()`?

Cuando programamos, la computadora ejecuta instrucciones en silencio. La función **print()** (imprimir) es la herramienta básica que usamos para pedirle a Python que nos muestre un mensaje en la terminal.

Pensalo como el "parlante" de tu código: **todo lo que pones adentro de los paréntesis de** **print()** **, Python lo muestra en pantalla.**

### Ejemplo:

```
print("¡Hola, mundo!")

```

Si ejecutás esa línea, la consola va a responder:

```
¡Hola, mundo!

```

---

## 🔤 2\. El Texto en Python (Cadenas de Texto / *Strings*)

Fijate que el mensaje `"¡Hola, mundo!"` está rodeado de **comillas dobles** (`" "`).

En programación, al texto plano se lo llama **String** (cadena de caracteres). Las comillas le avisan a Python: *"Ey, esto no es una instrucción ni un comando, es simplemente texto literal que quiero que conserves tal cual"*.

Podés usar comillas dobles (`" "`) o comillas simples (`' '`), pero **siempre tenés que abrir y cerrar con el mismo tipo**:

* ✅ `print("Hola")` \-&gt; Correcto
* ✅ `print('Hola')` \-&gt; Correcto
* ❌ `print("Hola')` \-&gt; **Error**: mezclaste comillas dobles con simples.

---

## 📝 3\. Los Comentarios (`#`)

Un **comentario** es una anotación en español (o inglés) que escribimos dentro del archivo de código para explicarnos a nosotros mismos o a otros compañeros qué hace una línea.

Python **ignora por completo** todo lo que esté después del símbolo de numeral/hashtag (`#`).

### Ejemplo:

```
# Este es un comentario: Python no lo ejecuta
print("Esta línea sí se ejecuta en la pantalla") # Este comentario está al final de la línea

```

Los comentarios son fundamentales para mantener un código ordenado y legible.

---

## 🛠️ Práctica Guiada (Paso a Paso)

Vamos a crear y ejecutar tu primer script de Python en tu computadora:

1. Abrí la terminal en la raíz de tu proyecto.
2. Navegá hasta la carpeta del Módulo 01:

```
cd modulo-01-python-defensivo

```

1. Creá la carpeta `src` (si no existe) y el archivo `01_hola_mundo.py`:

```
mkdir -p src
touch src/01_hola_mundo.py

```

1. Abrí el archivo `src/01_hola_mundo.py` en VS Code y escribí estas líneas:

```
# Mi primer script de Python en Data Engineering
print("¡Hola! Estoy dando mis primeros pasos en Python.")
print("Aprendiendo desde CERO absoluto.")

```

1. Guardá el archivo (`Ctrl + S`).
2. Ejecutalo desde tu terminal con el comando:

```
python3 src/01_hola_mundo.py

```

*(Si estás en Windows y* *python3* *no funciona, probá escribiendo solo* *python src/01\_hola\_mundo.py* *)*.

---

### 💡 ¿Qué tendría que pasar en tu terminal?

Deberías ver estas dos líneas impresas limpia y directamente en la consola:

```
¡Hola! Estoy dando mis primeros pasos en Python.
Aprendiendo desde CERO absoluto.
```