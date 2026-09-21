* * Configurá `logging.basicConfig(level=logging.INFO)`.
* Creá el decorador `auditar_transaccion(func)`:
  * Debe registrar con `logging.info` los argumentos (`*args`, `**kwargs`) recibidos por la función antes de ejecutarla.
  * Debe medir el tiempo de ejecución.
  * Debe capturar el valor retornado por la función e informar con `logging.info` que la función terminó con éxito mostrando el tiempo de ejecución.
  * Debe retornar el resultado de la función intacto.
* Creá la función `transformar_monto_moneda(monto: float, tasa_cambio: float = 1200.0) -&gt; float` decorada con `@auditar_transaccion`:
  * Simulá una demora de `0.5` segundos usando `time.sleep(0.5)`.
  * Retorná `monto * tasa_cambio`.
* En el bloque `if __name__ == "__main__":`:
* Ejecutá la función pasando un monto de `150.0` y observá cómo el decorador imprime automáticamente los logs de auditoría sin haber ensuciado el código de la función.
* Ejecutá tu script desde la terminal: `python3 practica/ej_21_decoradores.py`