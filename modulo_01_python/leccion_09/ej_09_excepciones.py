registros_raw = ["100.5", "200.0", "INVALIDO", "0.0", None, "500.25"]


def procesar_registros(valor_str):
    try:
        valor_float = float(valor_str)
        division = 1000 / valor_float
        return round(division, 2)
    except TypeError:
        print("🔴 Error: Los datos de entrada deben ser numéricos.")
        return 0.0
    except ValueError:
        print("🔴 Error: El texto no es numérico.")
        return 0.0
    except ZeroDivisionError:
        print("🔴 Error: El valor era 0. Provocando un ZeroDivisionError")
        return 0.0

suma_total = 0

for i in registros_raw:
    suma_total += procesar_registros(i)

print(f"La suma de registros procesados fue de {suma_total}")