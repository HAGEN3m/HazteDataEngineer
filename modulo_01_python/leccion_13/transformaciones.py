
def limpiar_monto_str(monto_raw: str) -> float:
    try:
        monto_limpio = monto_raw.replace("$", "").strip()
        monto_limpio = monto_limpio.replace(",", "")
        return float(monto_limpio)
    except ValueError:
        print("Monto invalido: ValueError")
        return 0.0