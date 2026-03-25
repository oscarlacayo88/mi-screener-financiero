import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Screener Financiero Pro", layout="wide")

st.title("🚀 Screener de Inversión Multiactivo")
st.markdown("Analizador técnico y fundamental en tiempo real.")

# 2. BARRA LATERAL (INPUTS)
st.sidebar.header("Panel de Control")
tickers_input = st.sidebar.text_input("Lista de Tickers (separados por coma):", "QQQ, VGT, AAPL, MSFT")
periodo = st.sidebar.selectbox("Rango de la Gráfica:", ["6mo", "1y", "2y", "5y"], index=1)

# 3. FUNCIÓN DE PROCESAMIENTO
def procesar_ticker(symbol):
    try:
        t_obj = yf.Ticker(symbol)
        # Bajamos 1 año para asegurar que el SMA50 tenga datos
        df = t_obj.history(period="1y")
        
        if df.empty or len(df) < 50:
            return None
        
        # Cálculos Técnicos
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Valores finales (Asegurando que sean números simples)
        precio = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma50 = float(df['SMA50'].iloc[-1])
        
        # Datos Fundamentales
        info = t_obj.info
        pe_ratio = info.get('trailingPE', 'N/A')
        div_yield = info.get('dividendYield', 0)
        div_str = f"{div_yield * 100:.2f}%" if div_yield else "0%"

        # Lógica de Señal
        if rsi < 35 and precio > sma50: semaforo = "🟢 COMPRA (DIP)"
        elif rsi > 70: semaforo = "🔴 VENTA / CARO"
        elif precio > sma50: semaforo = "🟡 MANTENER"
        else: semaforo = "⚪ NEUTRAL"
        
        return {
            "Ticker": symbol,
            "Precio": round(precio, 2),
            "RSI": round(rsi, 2),
            "P/E Ratio": pe_ratio,
            "Dividendos": div_str,
            "Señal": semaforo
        }
    except:
        return None

# 4. EJECUCIÓN Y TABLA
lista_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
resultados = [] # <--- AQUÍ SE DEFINE LA VARIABLE PARA EVITAR EL ERROR

for t in lista_tickers:
    res = procesar_ticker(t)
    if res:
        resultados.append(res)

if resultados:
    st.subheader("📊 Comparativa de Mercado")
    df_res = pd.DataFrame(resultados)
    st.dataframe(df_res, use_container_width=True, hide_index=True)

    # 5. SECCIÓN DE GRÁFICA
    st.divider()
    st.subheader("🔍 Análisis Visual Detallado")
    ticker_sel = st.selectbox("Selecciona un activo para ver su gráfico:", lista_tickers)
    
    data_graf = yf.download(ticker_sel, period=periodo, interval="1d")
    
    if not data_graf.empty:
        fig = go.Figure()
        # Precio
        fig.add_trace(go.Scatter(x=data_graf.index, y=data_graf['Close'].squeeze(), 
                                 name='Precio', line=dict(color='#00ffcc')))
        # SMA50
        sma_graf = data_graf['Close'].rolling(window=50).mean()
        fig.add_trace(go.Scatter(x=data_graf.index, y=sma_graf.squeeze(), 
                                 name='Tendencia (50d)', line=dict(color='orange', dash='dot')))
        
        fig.update_layout(template="plotly_dark", height=500, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Escribe tickers válidos para empezar el análisis.")
