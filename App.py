import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Multi-Asset Screener", layout="wide")

st.title("🚀 Screener de Inversión Multiactivo")

# --- BARRA LATERAL ---
st.sidebar.header("Panel de Control")
tickers_input = st.sidebar.text_input("Ingresa los Tickers (separados por coma):", "QQQ, VGT, AAPL, SPY")
periodo = st.sidebar.selectbox("Historial para análisis:", ["6mo", "1y", "2y"])

# Función para procesar la lógica de cada ticker
def procesar_ticker(symbol):
    df = yf.download(symbol, period=periodo, interval="1d", progress=False)
    if df.empty: return None
    
    # Cálculo de indicadores
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    precio = df['Close'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    sma50 = df['SMA50'].iloc[-1]
    
    # Lógica de Veredicto
    if rsi < 35 and precio > sma50: veredicto = "🟢 COMPRA (DIP)"
    elif rsi > 70: veredicto = "🔴 VENTA / CARO"
    elif precio > sma50: veredicto = "🟡 MANTENER"
    else: veredicto = "⚪ NEUTRAL / DEBIL"
    
    return {"Ticker": symbol, "Precio": round(precio, 2), "RSI": round(rsi, 2), "Señal": veredicto}

# --- TABLA COMPARATIVA ---
st.subheader("📊 Comparativa de Señales")
lista_tickers = [t.strip().upper() for t in tickers_input.split(",")]
resultados = []

for t in lista_tickers:
    res = procesar_ticker(t)
    if res: resultados.append(res)

if resultados:
    df_res = pd.DataFrame(resultados)
    st.table(df_res) # Mostramos la tabla comparativa

# --- DETALLE INDIVIDUAL ---
st.divider()
st.subheader("🔍 Análisis Detallado")
ticker_detalle = st.selectbox("Selecciona un ticker para ver su gráfica:", lista_tickers)
datos_det = yf.download(ticker_detalle, period=periodo)

if not datos_det.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=datos_det.index, y=datos_det['Close'], name='Precio'))
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)
