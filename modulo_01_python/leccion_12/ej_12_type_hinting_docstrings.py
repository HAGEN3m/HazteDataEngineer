from typing import List, Dict, Optional, Union

def filtrar_y_promediar_ventas(ventas: List[Dict[str, Union[str, float]]], estado_filtro: str = "COMPLETADA") -> Optional[float]:
    """Filtra y calcula métricas de ingesta
    Args:
        ventas (List[Dict[str, Union[str, float]]]): Cada diccionario representa una venta.
        estado_filtro (str): Es el estado requerido para incluir la venta en el cálculo. Defaults to "COMPLETADA".
    Returns:
        Optional[float]: Decimal que representa el promedio de las ventas, si no hay ventas válidas retorna none.
    """
    total = 0
    contador = 0
    for i in ventas:  
        if i["estado"] == estado_filtro and i["monto"] > 0: 
            total += i["monto"]
            contador += 1
            
    if contador > 0:
        return round(total/contador, 2)
    else:
        return None

dataset_test = [
    {"id": "101", "monto": 150.0, "estado": "COMPLETADA"},
    {"id": "102", "monto": -50.0, "estado": "COMPLETADA"},
    {"id": "103", "monto": 300.0, "estado": "PENDIENTE"},
    {"id": "104", "monto": 250.0, "estado": "COMPLETADA"}
]

print(filtrar_y_promediar_ventas(dataset_test))