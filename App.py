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
if resultados:
    df_res = pd.DataFrame(resultados)
    st.table(df_res) 

    # --- SECCIÓN DE GRÁFICA DETALLADA ---
    st.divider()
    st.subheader("🔍 Análisis Visual Detallado")
    
    # El usuario elige uno de los tickers que escribió arriba
    ticker_para_grafica = st.selectbox("Selecciona un activo para ver su gráfico:", lista_tickers)
    
    # Descargamos datos frescos solo para ese activo seleccionado
    datos_grafica = yf.download(ticker_para_grafica, period=periodo, interval="1d")
    
    if not datos_grafica.empty:
        # Creamos una gráfica interactiva profesional
        fig = go.Figure()
        
        # Línea de Precio
        fig.add_trace(go.Scatter(
            x=datos_grafica.index, 
            y=datos_grafica['Close'].squeeze(), 
            name='Precio de Cierre',
            line=dict(color='#1f77b4', width=2)
        ))
        
        # Promedio de 50 días para ver la tendencia
        sma50_graf = datos_grafica['Close'].rolling(window=50).mean()
        fig.add_trace(go.Scatter(
            x=datos_grafica.index, 
            y=sma50_graf.squeeze(), 
            name='Tendencia (SMA 50)',
            line=dict(color='orange', dash='dot')
        ))

        fig.update_layout(
            title=f"Histórico de {ticker_para_grafica}",
            xaxis_title="Fecha",
            yaxis_title="Precio (USD)",
            template="plotly_dark", # Se ve más profesional en negro
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se pudieron cargar los datos para la gráfica.")
