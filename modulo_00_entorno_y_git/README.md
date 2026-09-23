# 🐚 Módulo 00: La Terminal y Git desde CERO Absoluto

&gt; *Perdele el miedo a la pantalla negra: aprendé a moverte por tu computadora usando comandos y a guardar el historial de tu código con Git.*

---

## 📌 ¿Qué es la Terminal y por qué no hay que tenerle miedo?

Cuando usás tu computadora normalmente, usás una **Interfaz Gráfica (GUI)**: hacés doble clic en carpetas, arrastrás archivos con el mouse y los abrís con un botón.

La **Terminal (o Línea de Comandos / CLI)** es simplemente otra forma de comunicarte con tu computadora, pero **escribiendo texto**.

### ¿Por qué los Ingenieros de Datos usan la terminal?

1. **Es más rápida**: Podés crear 50 carpetas o buscar un texto en mil archivos en un segundo.
2. **Los servidores no tienen pantalla**: Cuando tu código corre en la nube (AWS, Google Cloud, Docker), no hay mouse ni ventanas. Todo se maneja por consola.

---

## 🐣 Lección 0.1: Los Comandos Básicos (Paso a Paso)

Abrí tu terminal (Git Bash en Windows, Terminal en Mac/Linux) y probá estos comandos uno por uno:

### 1\. ¿Dónde estoy parado? (`pwd`)

Escribí `pwd` y presioná Enter.

* Significa: *Print Working Directory* (Imprimir directorio de trabajo).
* **Te muestra la ruta exacta de la carpeta donde estás ubicado ahora mismo.**

### 2\. Mirar a tu alrededor (`ls`)

Escribí `ls` y presioná Enter.

* Significa: *List* (Listar).
* **Muestra todos los archivos y carpetas que están adentro de tu carpeta actual.**
* *Tip*: Si escribís `ls -a`, también te muestra los archivos ocultos (los que empiezan con un punto, como `.gitignore`).

### 3\. Moverte de carpeta (`cd`)

Significa: *Change Directory* (Cambiar de directorio).

* Para entrar a una carpeta llamada `documentos`: `cd documentos`
* Para volver a la carpeta anterior (subir un nivel): `cd ..`

### 4\. Crear una carpeta nueva (`mkdir`)

Significa: *Make Directory* (Crear directorio).

* Para crear una carpeta llamada `mi_primer_carpeta`: `mkdir mi_primer_carpeta`

### 5\. Crear un archivo vacío (`touch`)

* Para crear un archivo llamado `notas.txt`: `touch notas.txt`

### 6\. Escribir texto en un archivo (`echo`)

* Para escribir "Hola Mundo" adentro de `notas.txt`: `echo "Hola Mundo" &gt; notas.txt`

### 7\. Leer un archivo en la pantalla (`cat`)

Significa: *Concatenate* (Ver contenido).

* Para ver qué hay adentro de `notas.txt`: `cat notas.txt`

### 8\. Borrar archivos y carpetas (`rm`)

* Para borrar un archivo: `rm notas.txt`
* Para borrar una carpeta vacía: `rmdir mi_primer_carpeta`

---

## 🌿 Lección 0.2: ¿Qué es Git y para qué sirve?

Imaginá que estás jugando a un videojuego largo y difícil. Antes de enfrentarte a un jefe final, **guardás la partida**. Si morís o te equivocás, podés volver al punto donde guardaste sin perder todo tu progreso.

**Git hace exactamente eso con tu código:**

* Te permite guardar "fotos" (puntos de control) de tu proyecto.
* Si rompes algo, podés volver al estado anterior con un comando.
* **GitHub** es como la nube (PlayStation Network / Drive) donde subís esos puntos de control guardados para compartirlos o no perderlos si se te rompe la computadora.

---

## 🔄 Lección 0.3: El Flujo de Git en 4 Pasos Sencillos

Cada vez que haces un cambio en tu código y querés guardarlo en GitHub, seguís estos 4 pasos en orden:

```
[ Tu Computadora ]  ---&gt;  [ Área de Preparación ]  ---&gt;  [ Historial Local ]  ---&gt;  [ GitHub ]
    (Cambios)               (git add .)               (git commit)             (git push)

```

1. **git status**: Revisa qué archivos cambiaste o creaste.
2. **git add .**: Prepara todos los archivos modificados para guardarlos (los mete en la "caja de envío").
3. **git commit -m "Explicación del cambio"**: Le saca una foto a la caja de envío y le pone una etiqueta descriptiva (ej: `git commit -m "crear primer archivo"`).
4. **git push origin main**: Sube esa foto guardada a tu repositorio remoto en GitHub.

---

## 🏋️‍♂️ Práctica Guiada

Hagamos un ejercicio real en tu consola para fijar todo:

1. Abrí la terminal y navigate hasta este módulo: `cd modulo-00-entorno-y-git`
2. Verificá qué archivos hay en la carpeta: `ls`
3. Creá un archivo llamado `mi_presentacion.txt`: `touch mi_presentacion.txt`
4. Escribí tu nombre adentro usando el comando `echo`: `echo "Hola, soy [Tu Nombre] y estoy aprendiendo Data Engineering desde CERO" &gt; mi_presentacion.txt`
5. Leé el archivo para asegurarte de que se guardó bien: `cat mi_presentacion.txt`
6. Subí el archivo a tu GitHub ejecutando los 3 comandos sagrados: `git add mi_presentacion.txt` `git commit -m "docs: agregar mi presentacion"` `git push origin main`

---

## 📺 Recurso Recomendado

* 🎥 [Curso de Git y GitHub desde Cero - MoureDev](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D3GymExBkKjE) (Miralo a tu ritmo para ver la explicación en video).

```
## ⚡ Lección 0.4: Scripting Defensivo en Bash y Monitoreo de Procesos

Cuando creamos scripts en la terminal para mover o procesar datos, necesitamos que fallen de forma segura si ocurre un error.

### 1. Las 3 reglas de oro del Scripting Defensivo (`set -euo pipefail`)
Agregá siempre esta línea al inicio de tus scripts `.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

```

* **set -e**: Detiene la ejecución del script inmediatamente si cualquier comando da error.
* **set -u**: Da error si intentás usar una variable que no fue definida.
* **set -o pipefail**: Si usás tuberías (`comando1 | comando2`), el script falla si *cualquiera* de los comandos falla, no solo el último.

### 2\. Monitoreo de memoria y procesos en tiempo real

* **top** **/** **htop**: Muestra los procesos que más CPU y RAM están consumiendo.
* **lsof -i :8080**: Te dice qué proceso está usando un puerto específico.
* **kill -9