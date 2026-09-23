def validar_y_convertir_monto(monto_raw, conversion=1.0):
    monto_raw = float(monto_raw)
    if monto_raw <= 0:
        return None
    else:
        resultado = monto_raw * conversion
        return round(resultado, 2)

lote_raw = ["100.50", -50.0, "200.00", 0.0, "350.25"]


for i in lote_raw:
    resultado = validar_y_convertir_monto(i, 1200)
    if resultado is not None:
        print(f"🟢 Monto convertido a moneda local: ${resultado}")
    else:
        print(f"🔴 Registro inválido descartado.")