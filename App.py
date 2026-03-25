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
    ticker_obj = yf.Ticker(symbol)
    # Pedimos 1 año para que el promedio de 50 días (SMA50) tenga suficientes datos
    df = ticker_obj.history(period="1y") 
    
    if df.empty or len(df) < 50: return None
    
    # --- Cálculos Técnicos ---
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # Cálculo del RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EXTRACCIÓN CRÍTICA: Convertimos a número simple (float)
    precio = float(df['Close'].iloc[-1])
    rsi = float(df['RSI'].iloc[-1])
    sma50 = float(df['SMA50'].iloc[-1])
    
    # --- Datos Fundamentales ---
    info = ticker_obj.info
    pe_ratio = info.get('trailingPE', 'N/A')
    div_yield = info.get('dividendYield', 0)
    div_yield = f"{div_yield * 100:.2f}%" if div_yield else "0%"

    # --- Lógica de Señal Corregida ---
    if rsi < 35 and precio > sma50: 
        semaforo = "🟢 COMPRA (DIP)"
    elif rsi > 70: 
        semaforo = "🔴 VENTA / CARO"
    elif precio > sma50: 
        semaforo = "🟡 MANTENER"
    else: 
        semaforo = "⚪ NEUTRAL"
    
    return {
        "Ticker": symbol,
        "Precio": round(precio, 2),
        "RSI": round(rsi, 2),
        "P/E Ratio": pe_ratio,
        "Dividendos": div_yield,
        "Señal": semaforo
    }
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
