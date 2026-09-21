# 🐍 Lección 24: Entornos Virtuales (`venv`), Gestores de Dependencias y `requirements.txt`

En la **Ingeniería de Datos**, es habitual trabajar en múltiples proyectos a la vez: un pipeline antiguo puede requerir `pandas==1.5.3` para mantener compatibilidad con un sistema legado, mientras que un desarrollo nuevo utiliza `polars==1.0.0` y `pandas==2.2.0`. Si instalás todas las librerías de forma global en tu sistema operativo, tarde o temprano se producirán conflictos de versiones insalvables.

Un **Entorno Virtual** (`venv`) es un directorio aislado que contiene su propia instalación ejecutable de Python y su propio árbol independiente de librerías instaladas.

---

## 1\. ¿Por qué son indispensables en Producción?

* **Aislamiento Total de Dependencias**: Evita que la actualización de un paquete en un proyecto rompa el funcionamiento de otros proyectos en la misma máquina.
* **Reproducibilidad en Producción**: Garantiza que el entorno local de desarrollo sea una copia exacta del entorno de producción, un contenedor Docker o un ejecutor de CI/CD en GitHub Actions.
* **Higiene del Sistema Operativo**: Mantiene el Python base de tu sistema limpio y protegido contra colisiones de paquetes.

---

## 2\. Crear y Activar un Entorno Virtual (`venv`)

El módulo `venv` viene incluido de forma nativa en la librería estándar de Python.

### Paso 1: Crear el entorno virtual

En la terminal, ubicado en la raíz de tu proyecto:

```
# Sintaxis: python3 -m venv