import random

def calcular_alcance_total(presupuesto_diario, seguidores, shock_multiplier, peso_tags, modo):
    impresiones_pagadas = (presupuesto_diario / 4.5) * 1000
    clics_anuncio = impresiones_pagadas * 0.10 if modo != "organico" else 0
    
    vistas_organicas = (seguidores.get('x', 0) * 0.05 + seguidores.get('yt', 0) * 0.12) * peso_tags
    if modo == "pagado": vistas_organicas = 0
    
    return (clics_anuncio + vistas_organicas) * shock_multiplier

def tasa_conversion_steam(base_cr):
    return base_cr * random.uniform(0.85, 1.15)

def calcular_ganancia_neta(ventas, precio):
    return (ventas * precio) * 0.70 * 0.92