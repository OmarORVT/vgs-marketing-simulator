import simpy
import random
import pandas as pd
from .formulas import calcular_alcance_total, tasa_conversion_steam, calcular_ganancia_neta

class SimuladorVentas:
    def __init__(self, env, config, pool_eventos):
        self.env = env
        self.c = config
        self.pool_eventos = pool_eventos
        self.historial = []

    def ejecutar(self):
        while True:
            dia = self.env.now
            shock = 1.0
            evento = "Ninguno"
            for ev in self.pool_eventos:
                if random.random() < ev['probabilidad']:
                    shock = ev['multiplicador']
                    evento = ev['nombre']
                    break

            modos = ["pagado", "organico", "mixto"]
            datos_dia = {"dia": dia, "evento": evento}
            
            for m in modos:
                alcance = calcular_alcance_total(self.c['marketing']['gasto_diario'], 
                                              self.c['marketing']['seguidores'], 
                                              shock, self.c['juego']['peso_tags'], m)
                cr = tasa_conversion_steam(0.025)
                ventas = int(alcance * cr)
                ganancia = calcular_ganancia_neta(ventas, self.c['juego']['precio'])
                
                datos_dia[f"ventas_{m}"] = ventas
                datos_dia[f"ganancia_{m}"] = ganancia

            self.historial.append(datos_dia)
            yield self.env.timeout(1)

def correr_monte_carlo(config, pool_eventos, iteraciones=200):
    resultados = []
    for _ in range(iteraciones):
        env = simpy.Environment()
        sim = SimuladorVentas(env, config, pool_eventos)
        env.process(sim.ejecutar())
        env.run(until=config['simulacion']['duracion_dias'] + 1)
        df = pd.DataFrame(sim.historial)
        
        for m in ["pagado", "organico", "mixto"]:
            resultados.append({
                "modo": m,
                "ventas_totales": df[f"ventas_{m}"].sum(),
                "ganancia_total": df[f"ganancia_{m}"].sum()
            })
    return pd.DataFrame(resultados)