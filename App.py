import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN
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
seleccion = st_searchbox(buscar_en_yahoo, key="search_v4", label="Busca una acción:")
periodo_graf = st.sidebar.selectbox("Rango Visual:", ["1y", "2y", "5y"], index=0)

# 3. PROCESAMIENTO PRINCIPAL
if seleccion:
    ticker_id = seleccion.split(" | ")[0]
    
    with st.spinner(f"Cargando datos de {ticker_id}..."):
        t_obj = yf.Ticker(ticker_id)
        hist = t_obj.history(period=periodo_graf)
        info = t_obj.info
        
    if not hist.empty:
        # PESTAÑAS (Asegurando alineación perfecta)
        tab1, tab2, tab3 = st.tabs(["📊 Resumen y Señal", "🏛️ Equity Research", "📈 Gráfico Interactivo"])

        with tab1:
            col_a, col_b = st.columns(2)
            precio_actual = info.get('currentPrice', hist['Close'].iloc[-1])
            with col_a:
                st.metric("Precio Actual", f"${precio_actual:.2f} USD")
            with col_b:
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rsi_val = 100 - (100 / (1 + (gain.iloc[-1]/loss.iloc[-1])))
                st.metric("RSI (14d)", f"{rsi_val:.2f}")

        with tab2:
            st.subheader("🎯 Consenso de Analistas")
            c1, c2, c3 = st.columns(3)
            t_low = info.get('targetLowPrice', 'N/A')
            t_mean = info.get('targetMeanPrice', 'N/A')
            t_high = info.get('targetHighPrice', 'N/A')
            
            c1.metric("Target Mínimo", f"${t_low}")
            c2.metric("Target Promedio", f"${t_mean}")
            c3.metric("Target Máximo", f"${t_high}")

            st.divider()
            st.subheader("📊 Sentimiento y Firmas")
            
            # Intentamos obtener firmas, si falla, damos el resumen
            try:
                # Método alternativo para recomendaciones
                recomendas = t_obj.recommendations
                if recomendas is not None and not recomendas.empty:
                    st.dataframe(recomendas.tail(10)[['Firm', 'To Grade', 'Action']], use_container_width=True)
                else:
                    st.info(f"Consenso Actual: {info.get('recommendationKey', 'N/A').upper()}")
                    st.write(f"Puntuación (1-5): {info.get('recommendationMean', 'N/A')}")
            except:
                st.warning("Desglose de firmas no disponible. Mostrando datos clave:")
                st.write(f"Crecimiento Ingresos: {info.get('revenueGrowth', 0)*100:.1f}%")

        with tab3:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'].squeeze(), name='Precio', line=dict(color='#00ffcc')))
            fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No se encontraron datos.")
else:
    st.info("Busca una empresa en el panel izquierdo.")
