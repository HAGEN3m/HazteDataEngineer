sueldo_bruto_str = "3500.50"
porcentaje_impuesto = 15

sueldo_bruto_float = float(sueldo_bruto_str)
descuento = ((sueldo_bruto_float * porcentaje_impuesto)/100)
sueldo_neto = sueldo_bruto_float - descuento

print(f"Sueldo Bruto: ${sueldo_bruto_float} |Descuento ({porcentaje_impuesto}%): {descuento}| Sueldo Neto: ${sueldo_neto}")