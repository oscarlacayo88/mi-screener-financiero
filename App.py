import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Smart Financial Screener", layout="wide")

st.title("📊 Smart Financial Screener")
st.markdown("Analizador de activos en tiempo real con lógica de trading algorítmico.")

# --- BARRA LATERAL ---
st.sidebar.header("Configuración")
ticker = st.sidebar.text_input("Símbolo del Activo (Ticker)", value="QQQ").upper()
periodo = st.sidebar.selectbox("Periodo de análisis", ["6mo", "1y", "2y", "5y"])
umbral_rsi_baja = st.sidebar.slider("Umbral Sobreventa (Compra)", 0, 100, 30)
umbral_rsi_alta = st.sidebar.slider("Umbral Sobrecompra (Venta)", 0, 100, 70)

# --- OBTENCIÓN DE DATOS ---
@st.cache_data
def cargar_datos(symbol, p):
    df = yf.download(symbol, period=p, interval="1d")
    return df

data = cargar_datos(ticker, periodo)

if not data.empty:
    # Cálculos Técnicos
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()
    
    # Lógica RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    precio_act = float(data['Close'].iloc[-1].item())
    rsi_act = float(data['RSI'].iloc[-1].item())
    sma50_act = float(data['SMA50'].iloc[-1].item())

    # --- INDICADORES VISUALES (Métricas) ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Precio Actual", f"${precio_act:,.2f}")
    with col2:
        st.metric("RSI (14d)", f"{rsi_act:.2f}")
    with col3:
        # Lógica de Semáforo
        if rsi_act < umbral_rsi_baja and precio_act > sma50_act:
            st.success("SEÑAL: COMPRA (DIP)")
        elif rsi_act > umbral_rsi_alta:
            st.error("SEÑAL: VENTA / CARO")
        else:
            st.info("SEÑAL: NEUTRAL / MANTENER")

    # --- GRÁFICA INTERACTIVA ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Precio', line=dict(color='royalblue', width=2)))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='Promedio 50d', line=dict(color='orange', dash='dot')))
    
    fig.update_layout(title=f"Evolución Histórica de {ticker}", xaxis_title="Fecha", yaxis_title="Precio (USD)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Error al cargar datos. Verifica el Ticker.")
