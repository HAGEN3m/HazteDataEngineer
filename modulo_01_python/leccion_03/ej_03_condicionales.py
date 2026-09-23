cliente_activo = True
monto_compra = 2500.0
codigo_pais = "AR"
# codigo_pais = "BR"

if cliente_activo == False:
    print("🔴 Cliente inactivado. Transacción rechazada.")
elif cliente_activo and monto_compra <= 0:
    print("🔴 Monto de compra inválido. Transacción rechazada.")
else:
    if codigo_pais == "AR" or codigo_pais == "CL":
        monto_final = monto_compra + monto_compra * 0.10
        print(f"El total a pagar es: ${monto_final}")
    else:
        print(f"El total a pagar es: ${monto_compra}")