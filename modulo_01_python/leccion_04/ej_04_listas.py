archivos_pendientes = ["ventas_jan.csv", "ventas_feb.csv", "ventas_mar.csv"]

total_archivos = len(archivos_pendientes)

print(f"Archivos pendientes en cola: {total_archivos}")

archivos_pendientes.append("ventas_apr.csv")

archivos_pendientes[0] = "ventas_jan_corregido.csv"

print(f"Primer archivo en cola: {archivos_pendientes[0]}")
print(f"Último archivo en cola: {archivos_pendientes[-1]}")
#print(archivos_pendientes)