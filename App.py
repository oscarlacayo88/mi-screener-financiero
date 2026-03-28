import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Screener Equity Research Pro", layout="wide")
st.title("🎯 Terminal de Análisis: Precios Objetivo y Firmas")

# 2. BUSCADOR DINÁMICO
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=6)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

st.sidebar.header("🔍 Selección de Activo")
seleccion = st_searchbox(buscar_en_yahoo, key="search_v3", label="Busca una acción (ej: MSFT):")
periodo_graf = st.sidebar.selectbox("Rango Visual:", ["1y", "2y", "5y"], index=0)

# 3. PROCESAMIENTO PRINCIPAL
if seleccion:
    ticker_id = seleccion.split(" | ")[0]
    
    # Descarga de datos previa (Fuera de los tabs para evitar que se quede cargando)
    with st.spinner(f"Cargando datos de {ticker_id}..."):
        t_obj = yf.Ticker(ticker_id)
        hist = t_obj.history(period=periodo_graf)
        info = t_obj.info
        
    if not hist.empty:
        # PESTAÑAS
        tab1, tab2, tab3 = st.tabs(["📊 Resumen y Señal", "🏛️ Equity Research", "📈 Gráfico Interactivo"])

        with tab1:
            col_a, col_b = st.columns(2)
            with col_a:
                precio_actual = info.get('currentPrice', hist['Close'].iloc[-1])
                st.metric("Precio Actual", f"${precio_actual:.2f} USD")
            with col_b:
                # Lógica de RSI rápida
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
                st.metric("RSI (14d)", f"{rsi:.2f}")

        with tab2:
            st.subheader("🎯 Consenso de Analistas")
            c1, c2, c3 = st.columns(3)
            c1.metric("Target Low", f"${info.get('targetLowPrice', 'N/A')}")
            c2.metric("Target Mean", f"${info.get('targetMeanPrice', 'N/A')}", help="Precio objetivo promedio")
            c3.metric("Target High", f"${info.get('targetHighPrice', 'N/A')}")

            st.divider()
            st.subheader("📋 Últimas Calificaciones de Firmas")
            # Extraer recomendaciones (Firms)
            try:
                recomendas = t_obj.recommendations
                if recomendas is not None and not recomendas.empty:
                    # Mostramos las últimas 8 para que quepan bien
                    st.dataframe(recomendas.tail(8)[['Firm', 'To Grade', 'Action']], use_container_width=True)
                else:
                    st.info("No hay desglose detallado reciente. Recomendación general: " + str(info.get('recommendationKey', 'N/A')).upper())
            except:
                st.error("Error al conectar con el servidor de recomendaciones.")

        with tab3:
            # GRÁFICA CORREGIDA (Sin bloqueos de carga)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist['Close'].squeeze(), 
                name='Precio de Cierre',
                line=dict(color='#00ffcc', width=2)
            ))
            
            # Media Móvil 50 para contexto
            hist['SMA50'] = hist['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist['SMA50'].squeeze(), 
                name='SMA 50',
                line=dict(color='orange', dash='dot')
            ))

            fig.update_layout(
                template="plotly_dark",
                height=500,
                margin=dict(l=20, r=20, t=30, b=20),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No se encontraron datos históricos para este ticker.")
else:
    st.info("👋 Bienvenida/o. Busca una empresa en el panel izquierdo para desplegar el Equity Research.")
