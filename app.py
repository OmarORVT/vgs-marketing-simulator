import streamlit as st
import simpy
import pandas as pd
import json
import io
from core.engine import SimuladorVentas, correr_monte_carlo
from ui.components import aplicar_estilo_github, renderizar_grafica_interactiva
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def cargar_datos():
    with open('data/tags_y_eventos.json', 'r') as f:
        return json.load(f)

def generar_pdf_reporte(df_semanal, stats_monte_carlo, dias_sim):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("<b>Reporte Detallado: VGS Marketing Simulator</b>", styles['Title']))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>Resumen Global (Promedio de 200 Ciclos)</b>", styles['Heading2']))
    story.append(Spacer(1, 8))
    
    tabla_kpis = [["Estrategia", "Ganancia Total Promedio", "Costo Incurrido", "ROI (%)"]]
    for _, row in stats_monte_carlo.iterrows():
        tabla_kpis.append([
            str(row['modo']).capitalize(),
            f"${row['ganancia_total']:,.2f}",
            f"${row['Costo']:,.2f}",
            f"{row['ROI (%)']:.2f}%"
        ])
    
    t_kpi = Table(tabla_kpis)
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2f81f7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke])
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("<b>Resultados Detallados por Semana</b>", styles['Heading2']))
    story.append(Spacer(1, 8))
    
    tabla_semanal = [["Semana", "Ventas Pagado", "Ventas Organico", "Ventas Mixto", "Evento Destacado"]]
    
    for i in range(0, len(df_semanal), 7):
        sub_df = df_semanal.iloc[i:i+7]
        semana_num = (i // 7) + 1
        eventos = sub_df['evento'].unique()
        evento_print = next((e for e in eventos if e != "Ninguno"), "Ninguno")
        
        tabla_semanal.append([
            f"Semana {semana_num}",
            str(sub_df['ventas_pagado'].sum()),
            str(sub_df['ventas_organico'].sum()),
            str(sub_df['ventas_mixto'].sum()),
            evento_print
        ])
        
    t_sem = Table(tabla_semanal)
    t_sem.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#24292f')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t_sem)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

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
        seg_ig = st.number_input("Seguidores Instagram (IG)", 0, 1000000, 2000)

if st.button("Ejecutar Simulacion"):
    config = {
        'juego': {'precio': precio, 'peso_tags': peso_tags},
        'marketing': {'gasto_diario': gasto_ads, 'seguidores': {'x': seg_x, 'yt': seg_yt, 'ig': seg_ig}},
        'simulacion': {'duracion_dias': dias}
    }

    env = simpy.Environment()
    sim = SimuladorVentas(env, config, datos['posibles_eventos'])
    env.process(sim.ejecutar())
    env.run(until=dias + 1)
    df_single = pd.DataFrame(sim.historial)

    with st.spinner("Procesando 200 corridas para KPIs..."):
        df_monte = correr_monte_carlo(config, datos['posibles_eventos'], 200)

    renderizar_grafica_interactiva(df_single)
    
    stats = df_monte.groupby('modo')['ganancia_total'].mean().reset_index()
    stats['Costo'] = stats['modo'].apply(lambda x: costo_dev + (gasto_ads*dias if x != 'organico' else 0))
    stats['ROI (%)'] = ((stats['ganancia_total'] - stats['Costo']) / stats['Costo']) * 100
    
    st.subheader("Comparacion de Estrategias (Promedio de 200 Corridas)")
    st.table(stats.style.format({'ganancia_total': '${:,.2f}', 'Costo': '${:,.2f}', 'ROI (%)': '{:.2f}%'}))

    st.markdown("---")
    st.subheader("Exportar Reporte Ejecutivo")
    
    with st.spinner("Generando archivo PDF detallado..."):
        pdf_file = generar_pdf_reporte(df_single, stats, dias)
        
    st.download_button(
        label="Descargar Reporte PDF Detallado",
        data=pdf_file,
        file_name="Reporte_Detallado_Marketing_VGS.pdf",
        mime="application/pdf"
    )