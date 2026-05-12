import streamlit as st
import plotly.graph_objects as go

def aplicar_estilo_github():
    st.markdown("""
        <style>
        .stMetric { border: 1px solid #d0d7de; padding: 10px; border-radius: 6px; background-color: #f6f8fa; }
        .stButton>button { background-color: #2f81f7; color: white; width: 100%; border-radius: 6px; }
        </style>
        """, unsafe_allow_html=True)

def renderizar_grafica_interactiva(df):
    fig = go.Figure()
    colores = {"pagado": "#2f81f7", "organico": "#2da44e", "mixto": "#8250df"}
    
    for modo in ["pagado", "organico", "mixto"]:
        fig.add_trace(go.Scatter(
            x=df['dia'], 
            y=df[f'ventas_{modo}'],
            name=modo.capitalize(),
            line=dict(color=colores[modo]),
            hovertemplate="Ventas: %{y}<br>Evento: %{customdata}",
            customdata=df['evento']
        ))

    fig.update_layout(
        hovermode="x unified", 
        template="plotly_white", 
        title="Ventas Diarias por Estrategia",
        xaxis_title="Dia",
        yaxis_title="Ventas"
    )
    st.plotly_chart(fig, use_container_width=True)