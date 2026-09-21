```
import json

# Estructura del Notebook Interactivo (Nivel 0.1)
notebook_content = {
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# 🐍 Módulo 01 - Lección 0.1: Tu Primera Línea de Código (`print` y Comentarios)\n",
        "\n",
        "&gt; **Bienvenido/a a tu primer Notebook Interactivo.**\n",
        "&gt; Vas a aprender ejecutando celdas de código directamente en VS Code.\n",
        "\n",
        "---\n",
        "\n",
        "### 📌 1. ¿Qué es `print()`?\n",
        "La función `print()` le pide a Python que muestre un mensaje en pantalla.\n",
        "Ejecutá la celda de abajo haciendo clic en el botón **Play (▶)** o presionando `Shift + Enter`."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Ejemplo 1: Ejecutá esta celda\n",
        "print('¡Hola! Bienvenido a Data Engineering desde CERO.')"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "---\n",
        "### 🧪 Ejercicio 1.1: Tu Primer Mensaje\n",
        "**Consigna:** Completa la variable `mensaje` con tu nombre y la frase `'listo para programar'`.\n",
        "Ejemplo: `\"Soy Tomas y estoy listo para programar\"`."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# TODO: Escribí tu mensaje entre las comillas\n",
        "mensaje = \"\" \n",
        "print(mensaje)"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "### 🟢 Evaluador Automático del Ejercicio 1.1\n",
        "Ejecutá esta celda para verificar si tu respuesta es correcta."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Celda de Autoevaluación\n",
        "try:\n",
        "    assert len(mensaje) &gt; 0, \"❌ La variable 'mensaje' no puede estar vacía.\"\n",
        "    assert \"listo para programar\" in mensaje.lower(), \"❌ El mensaje debe contener la frase 'listo para programar'.\"\n",
        "    print(\"🟢 ¡EXCELENTE! Ejercicio 1.1 Aprobado.\")\n",
        "except AssertionError as error:\n",
        "    print(error)\n",
        "except NameError:\n",
        "    print(\"❌ Primero tenés que ejecutar la celda de arriba donde definís 'mensaje'.\")"
      ]
    }
  ],
  "metadata": {
    "language_info": { "name": "python" }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}

# Guardar en la carpeta del Módulo 01
ruta_destino = "modulo-01-python-defensivo/01_nivel_0_1_hola_mundo.ipynb"
with open(ruta_destino, "w", encoding="utf-8") as f:
    json.dump(notebook_content, f, indent=2, ensure_ascii=False)

print(f"✅ Notebook generado con éxito en: {ruta_destino}")

```

1. Guardá el archivo y ejecutalo en la terminal:

```
python3 generar_notebook.py
```