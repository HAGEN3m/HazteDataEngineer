# 🐚 Módulo 00: Entorno de Trabajo, Consola Unix &amp; Versionado con Git

&gt; *Las herramientas fundamentales del Data Engineer: navegar el sistema operativo desde la terminal y gestionar el historial de código con Git.*

---

## 📌 1\. ¿Por qué la consola es el hábitat del Data Engineer?

En el mundo del desarrollo y la analítica tradicional, muchas tareas se hacen haciendo clic en interfaces gráficas. Sin embargo, en la **Ingeniería de Datos**, la mayoría de las herramientas (servidores Cloud, contenedores Docker, pipelines de Airflow y clústeres de Spark) **no tienen interfaz gráfica**: se gestionan 100% mediante la línea de comandos (CLI).

Dominar la terminal te da velocidad, control total sobre el sistema operativo y la capacidad de automatizar scripts.

---

## 💻 2\. Los 10 Comandos Esenciales de Unix/Linux

Abrí tu terminal (Bash, Zsh o WSL en Windows) y practicá estos comandos:

| Comando | Descripción                                                                   | Ejemplo de Uso                       |
| ------- | ----------------------------------------------------------------------------- | ------------------------------------ |
| `pwd`   | Muestra la ruta de la carpeta donde estás parado (*Print Working Directory*). | `pwd`                                |
| `ls`    | Lista los archivos y carpetas del directorio actual.                          | `ls -la`                             |
| `cd`    | Cambia de carpeta (*Change Directory*).                                       | `cd modulo-00-entorno-y-git`         |
| `mkdir` | Crea una nueva carpeta.                                                       | `mkdir mis_scripts`                  |
| `touch` | Crea un archivo vacío.                                                        | `touch script.py`                    |
| `rm`    | Elimina un archivo o carpeta.                                                 | `rm archivo.txt`                     |
| `cat`   | Muestra el contenido de un archivo en la consola.                             | `cat README.md`                      |
| `grep`  | Busca un texto específico dentro de un archivo.                               | `grep "ERROR" pipeline.log`          |
| `cp`    | Copia archivos o carpetas.                                                    | `cp config.py config_backup.py`      |
| `mv`    | Mueve o renombra archivos/carpetas.                                           | `mv viejo_nombre.py nuevo_nombre.py` |

---

## 🌿 3\. Control de Versiones con Git y GitHub

### ¿Qué es Git?

Git es un sistema de control de versiones local que registra los cambios realizados en tus archivos a lo largo del tiempo. Te permite volver a versiones anteriores, trabajar en ramas paralelas (*branches*) y colaborar sin pisar el trabajo de otros.

### ¿Qué es GitHub?

GitHub es una plataforma en la nube que aloja repositorios de Git remotos, permitiendo compartir código, automatizar pruebas y colaborar en equipo.

---

### 🔄 El Flujo de Trabajo Fundamental en Git

1. `git status`: Muestra el estado de tu repositorio (archivos modificados, nuevos o no rastreados).
2. `git add .`: Agrega los cambios al área de preparación (*Staging Area*).
3. `git commit -m "mensaje explicativo"`: Guarda una versión inmutable de los cambios preparados con un mensaje descriptivo.
4. `git push origin main`: Sube tus commits locales al repositorio remoto en GitHub.
5. `git pull origin main`: Descarga y combina los últimos cambios de GitHub en tu máquina local.

---

## 📺 4\. Recurso Recomendado (Inmersión Pasiva)

Para reforzar este módulo de forma visual y dinámica, te recomiendo ver el curso completo de MoureDev:

* 🎥 [Curso de Git y GitHub desde Cero - MoureDev](https://www.google.com/url?sa=E&amp;q=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D3GymExBkKjE)

---

## 🛠️ 5\. Práctica Guiada: Tu Primer Ejercicio de Terminal y Git

Realizá la siguiente secuencia de pasos en tu consola para verificar tu dominio de las herramientas:

1. Abrí la terminal y posicionate en la carpeta raíz de este proyecto.
2. Navegá hasta la carpeta del Módulo 00: `cd modulo-00-entorno-y-git`
3. Creá un archivo llamado `practica.txt`: `touch practica.txt`
4. Escribí tu nombre dentro del archivo usando la consola: `echo "Hola, soy [Tu Nombre] y estoy aprendiendo Data Engineering" &gt; practica.txt`
5. Verificá que el contenido se guardó correctamente: `cat practica.txt`
6. Guardá los cambios en Git y súbelos a GitHub: `git add practica.txt` `git commit -m "docs: agregar archivo de practica del Modulo 00"` `git push origin main`

---

## 💡 Buenas Prácticas de Commit

* Escribí mensajes de commit claros y en presente (ej: `feat: agregar script de ingesta`, `fix: corregir error de conexion`).
* Nunca subas archivos pesados (más de 100MB), claves privadas o credenciales. Usá siempre el archivo `.gitignore`.