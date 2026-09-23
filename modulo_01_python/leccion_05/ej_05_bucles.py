transacciones = [150.0, 200.5, -20.0, 310.0, 0.0, 500.0]
monto_total_valido = 0.0
cantidad_invalidas = 0

for i in transacciones:
    if i <= 0:
        cantidad_invalidas += 1
        print(f"Transacción inválida: {i}")
        continue
    else:
        monto_total_valido += i
        print(f"Transacción válida: {i}")

print(f"Procesamiento finalizado | Total acumulado: ${monto_total_valido} | Transacciones descartadas: {cantidad_invalidas}")