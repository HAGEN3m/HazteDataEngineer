```
# 🐚 Módulo 00: La Terminal, Git y Entorno Local de Trabajo

&gt; Perdele el miedo a la pantalla negra: aprendé a moverte por tu computadora usando comandos, a guardar el historial de tu código con Git y a configurar un entorno de desarrollo profesional defensivo.

---

## 📌 ¿Qué es la Terminal y por qué la usa un Data Engineer?

Cuando usás tu computadora normalmente, usás una Interfaz Gráfica (GUI): hacés doble clic en carpetas y arrastrás archivos. La Terminal (CLI) es la forma directa de comunicarte con el sistema operativo escribiendo texto.

* **Es más rápida**: Podés procesar o filtrar miles de archivos en segundos.
* **Los servidores no tienen pantalla**: En la nube (AWS, GCP, Docker) no hay mouse ni ventanas. Todo se maneja por consola.
* **Administración de recursos**: Un Data Engineer maneja procesos, memoria RAM e I/O directamente desde el sistema operativo.

---

## 🐣 Lección 0.1: Los Comandos Básicos (Paso a Paso)

Abrí tu terminal (Git Bash en Windows, Terminal en Mac/Linux) y probá estos comandos:

1. **`pwd`** (*Print Working Directory*): Muestra la ruta exacta de la carpeta donde estás ubicado.
2. **`ls`** (*List*): Muestra los archivos y carpetas del directorio actual. Usa `ls -la` para ver archivos ocultos y permisos.
3. **`cd`** (*Change Directory*): Cambia de carpeta. Uso: `cd nombre_carpeta` (para entrar) o `cd ..` (para subir un nivel).
4. **`mkdir`** (*Make Directory*): Crea una carpeta nueva. Uso: `mkdir mi_carpeta`.
5. **`touch`**: Crea un archivo vacío. Uso: `touch notas.txt`.
6. **`echo`**: Imprime texto o lo escribe en un archivo. Uso: `echo "Hola Mundo" &gt; notas.txt`.
7. **`cat`** (*Concatenate*): Muestra el contenido de un archivo en pantalla. Uso: `cat notas.txt`.
8. **`rm`**: Borra un archivo (`rm notas.txt`) o una carpeta (`rm -rf mi_carpeta`).

---

## 🌿 Lección 0.2: ¿Qué es Git y para qué sirve?

Git es un sistema de control de versiones. Te permite guardar puntos de control ("fotos") de tu proyecto. Si rompes algo, podés volver al estado anterior sin perder tu trabajo.

* **Git**: El programa instalado en tu computadora que rastrea los cambios.
* **GitHub**: La plataforma en la nube donde guardás tu código para respaldarlo o compartirlo.

---

## 🔄 Lección 0.3: El Flujo de Git en 4 Pasos

```

[ Tu Computadora ] ---&gt; [ Área de Preparación ] ---&gt; [ Historial Local ] ---&gt; [ GitHub ] (Cambios) (git add .) (git commit) (git push)

```

1. **`git status`**: Revisa qué archivos cambiaste o creaste.
2. **`git add .`**: Prepara todos los archivos modificados para el guardado.
3. **`git commit -m "mensaje"`**: Saca la "foto" y le pone una etiqueta descriptiva.
4. **`git push origin main`**: Sube tus commits a GitHub.

---

## ⚡ Lección 0.4: Scripting Defensivo en Bash y Monitoreo de Procesos

Cuando creamos scripts en Bash para automatizar la ingesta o movimiento de datos, necesitamos que se detengan inmediatamente ante cualquier fallo.

### 1. Las 3 reglas del Scripting Defensivo (`set -euo pipefail`)
Agregá siempre esta línea al inicio de tus scripts `.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

```

* **set -e**: Detiene el script si cualquier comando devuelve un código de error.
* **set -u**: Da error si se intenta usar una variable no definida.
* **set -o pipefail**: Si usás tuberías (`comando1 | comando2`), el script falla si *cualquiera* de los comandos falla.

### 2\. Monitoreo de memoria y procesos

* **top** **/** **htop**: Inspecciona el consumo de CPU y RAM de cada proceso en tiempo real.
* **lsof -i :8080**: Identifica qué proceso está ocupando un puerto específico.
* **kill -9