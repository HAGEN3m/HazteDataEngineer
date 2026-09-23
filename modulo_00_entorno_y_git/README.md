# 🐚 Módulo 00: La Terminal y Git desde CERO Absoluto

> *Perdele el miedo a la pantalla negra: aprendé a moverte por tu computadora usando comandos y a guardar el historial de tu código con Git.*

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

### 1. ¿Dónde estoy parado? (`pwd`)

Escribí `pwd` y presioná Enter.

* Significa: *Print Working Directory* (Imprimir directorio de trabajo).
* **Te muestra la ruta exacta de la carpeta donde estás ubicado ahora mismo.**

### 2. Mirar a tu alrededor (`ls`)

Escribí `ls` y presioná Enter.

* Significa: *List* (Listar).
* **Muestra todos los archivos y carpetas que están adentro de tu carpeta actual.**
* *Tip*: Si escribís `ls -a`, también te muestra los archivos ocultos (los que empiezan con un punto, como `.gitignore`).

### 3. Moverte de carpeta (`cd`)

Significa: *Change Directory* (Cambiar de directorio).

* Para entrar a una carpeta llamada `documentos`: `cd documentos`
* Para volver a la carpeta anterior (subir un nivel): `cd ..`

### 4. Crear una carpeta nueva (`mkdir`)

Significa: *Make Directory* (Crear directorio).

* Para crear una carpeta llamada `mi_primer_carpeta`: `mkdir mi_primer_carpeta`

### 5. Crear un archivo vacío (`touch`)

* Para crear un archivo llamado `notas.txt`: `touch notas.txt`

### 6. Escribir texto en un archivo (`echo`)

* Para escribir "Hola Mundo" adentro de `notas.txt`: `echo "Hola Mundo" > notas.txt`

### 7. Leer un archivo en la pantalla (`cat`)

Significa: *Concatenate* (Ver contenido).

* Para ver qué hay adentro de `notas.txt`: `cat notas.txt`

### 8. Borrar archivos y carpetas (`rm`)

* Para borrar un archivo: `rm notas.txt`
* Para borrar una carpeta vacía: `rmdir mi_primer_carpeta`

---

## 🌿 Lección 0.2: ¿Qué es Git y para qué sirve?

Imaginá que estás jugando a un videojuego largo y difícil. Antes de enfrentarte a un jefe final, **guardás la partida**. Si morís o te equivocás, podés volver al punto donde guardaste sin perder todo tu progreso.

**Git hace exactamente eso con tu código:**

* Te permite guardar "fotos" (puntos de control) de tu proyecto.
* Si rompes algo, podés volver al estado anterior con un comando.
* **GitHub** es como la nube donde subís esos puntos de control guardados para compartirlos o no perderlos si se te rompe la computadora.

---

## 🔄 Lección 0.3: El Flujo de Git en 4 Pasos Sencillos

Cada vez que haces un cambio en tu código y querés guardarlo en GitHub, seguís estos 4 pasos en orden:

```text
[ Tu Computadora ]   --->   [ Área de Preparación ]   --->   [ Historial Local ]   --->   [ GitHub ]
    (Cambios)                   (git add .)                   (git commit)             (git push)