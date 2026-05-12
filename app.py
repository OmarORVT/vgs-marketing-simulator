import streamlit as st
import simpy
import pandas as pd
import json
from core.engine import SimuladorVentas, correr_monte_carlo
from ui.components import aplicar_estilo_github, renderizar_grafica_interactiva

def cargar_datos():
    with open('data/tags_y_eventos.json', 'r') as f:
        return json.load(f)

st.set_page_config(page_title="VGS Interactive Pro", layout="wide")
aplicar_estilo_github()
datos = cargar_datos()

st.title("Simulador Estrategico de Mercado")

t1, t2 = st.tabs(["Producto", "Marketing"])

with t1:
    c1, c2 = st.columns(2)
    with c1:
        costo_dev = st.number_input("Costo Desarrollo ($)", 0, 1000000, 20000)
        precio = st.number_input("Precio ($)", 0.0, 70.0, 19.99)
    with c2:
        dias = st.slider("Dias Simulacion", 30, 365, 90)
        tags = st.multiselect("Tags de Steam", list(datos['tags_steam'].keys()), default=["roguelike"])
    peso_tags = sum([datos['tags_steam'][t] for t in tags]) / max(len(tags), 1)

with t2:
    cp, co = st.columns(2)
    with cp:
        gasto_ads = st.number_input("Gasto Ads Diario ($)", 0, 5000, 100)
    with co:
        seg_x = st.number_input("Seguidores X", 0, 1000000, 5000)
        seg_yt = st.number_input("Suscriptores YT", 0, 1000000, 15000)

if st.button("Ejecutar Simulacion"):
    config = {
        'juego': {'precio': precio, 'peso_tags': peso_tags},
        'marketing': {'gasto_diario': gasto_ads, 'seguidores': {'x': seg_x, 'yt': seg_yt}},
        'simulacion': {'duracion_dias': dias}
    }

    env = simpy.Environment()
    sim = SimuladorVentas(env, config, datos['posibles_eventos'])
    env.process(sim.ejecutar())
    env.run(until=dias + 1)
    df_single = pd.DataFrame(sim.historial)

    with st.spinner("Procesando 200 corridas para KPIs..."):
        df_monte = correr_monte_carlo(config, datos['posibles_eventos'], 200)

    # Solo renderizamos la grafica de lineas interactiva
    renderizar_grafica_interactiva(df_single)
    
    # Calculo y muestra de la tabla de KPIs
    stats = df_monte.groupby('modo')['ganancia_total'].mean().reset_index()
    stats['Costo'] = stats['modo'].apply(lambda x: costo_dev + (gasto_ads*dias if x != 'organico' else 0))
    stats['ROI (%)'] = ((stats['ganancia_total'] - stats['Costo']) / stats['Costo']) * 100
    
    st.subheader("KPIs Comparativos")
    st.table(stats.style.format({'ganancia_total': '${:,.2f}', 'Costo': '${:,.2f}', 'ROI (%)': '{:.2f}%'}))