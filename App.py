import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Screener Integral Pro", layout="wide")
st.title("📊 Terminal de Análisis Integral")

# 2. BUSCADOR DINÁMICO
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=6)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

st.sidebar.header("🔍 Configuración")
seleccion = st_searchbox(buscar_en_yahoo, key="search_final_v1", label="Busca un activo:")
periodo_graf = st.sidebar.selectbox("Rango Gráfica:", ["1y", "2y", "5y"], index=0)

# 3. PROCESAMIENTO
if seleccion:
    ticker_id = seleccion.split(" | ")[0]
    
    with st.spinner(f"Analizando {ticker_id}..."):
        t_obj = yf.Ticker(ticker_id)
        hist = t_obj.history(period="1y")
        info = t_obj.info
        
    if not hist.empty:
        # --- PESTAÑAS ---
        tab_info, tab_grafica = st.tabs(["🧐 Análisis y Fundamental", "📈 Gráfico Interactivo"])

        with tab_info:
            # FILA 1: Resumen y Señal Técnica
            st.subheader(f"Resumen de Mercado: {info.get('shortName', ticker_id)}")
            col1, col2, col3, col4 = st.columns(4)
            
            precio_actual = info.get('currentPrice', hist['Close'].iloc[-1])
            
            # Cálculo de RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rsi_val = 100 - (100 / (1 + (gain.iloc[-1]/loss.iloc[-1])))
            
            # Lógica de Señal Estricta
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if rsi_val < 32 and precio_actual > (sma50 * 0.97): señal = "🟢 COMPRA"
            elif rsi_val > 68: señal = "🔴 VENTA"
            else: señal = "⚪ NEUTRAL"

            col1.metric("Precio Actual", f"${precio_actual:.2f}")
            col2.metric("RSI (14d)", f"{rsi_val:.2f}")
            col3.metric("Señal Técnica", señal)
            col4.metric("Crecimiento Rev.", f"{info.get('revenueGrowth', 0)*100:.1f}%")

            st.divider()

            # FILA 2: Equity Research (Analistas)
            st.subheader("🏛️ Consenso de Equity Research")
            c_low, c_mean, c_high, c_upside = st.columns(4)
            
            t_low = info.get('targetLowPrice', 0)
            t_mean = info.get('targetMeanPrice', 0)
            t_high = info.get('targetHighPrice', 0)
            upside = ((t_mean / precio_actual) - 1) * 100 if t_mean else 0

            c_low.metric("Target Min", f"${t_low}" if t_low else "N/A")
            c_mean.metric("Target Promedio", f"${t_mean}" if t_mean else "N/A")
            c_high.metric("Target Max", f"${t_high}" if t_high else "N/A")
            c_upside.metric("Upside Potencial", f"{upside:.2f}%")

            # FILA 3: Desglose de Firmas o Datos Clave
            st.write("### 📋 Detalle de Instituciones y Calificaciones")
            try:
                recomendas = t_obj.recommendations
                if recomendas is not None and not recomendas.empty:
                    st.dataframe(recomendas.tail(8)[['Firm', 'To Grade', 'Action']], use_container_width=True)
                else:
                    st.info(f"Sin desglose detallado. Consenso: {info.get('recommendationKey', 'N/A').upper()} (Score: {info.get('recommendationMean', 'N/A')})")
            except:
                st.warning("No se pudo conectar con el servidor de firmas. Mostrando márgenes:")
                st.write(f"Margen Operativo: {info.get('operatingMargins', 0)*100:.1f}% | P/E Ratio: {info.get('trailingPE', 'N/A')}")

        with tab_grafica:
            # Gráfica interactiva con datos frescos
            data_graf = yf.download(ticker_id, period=periodo_graf)
            if not data_graf.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=data_graf.index, y=data_graf['Close'].squeeze(), name='Precio', line=dict(color='#00ffcc')))
                fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No se encontraron datos para este activo.")
else:
    st.info("🔍 Busca una empresa o ETF en el buscador para ver el análisis unificado.")
