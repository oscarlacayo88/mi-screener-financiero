import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Screener Universal Pro", layout="wide")
st.title("🌎 Screener Financiero Global")

# 2. FUNCIÓN DE BÚSQUEDA DINÁMICA (Yahoo Finance)
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=8)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

# 3. BARRA LATERAL
st.sidebar.header("🔍 Buscador")
seleccion_busqueda = st_searchbox(
    buscar_en_yahoo,
    key="search_global",
    placeholder="Escribe: Apple, Tesla, Walmex...",
    label="Busca cualquier activo:"
)

tickers_manuales = st.sidebar.text_input("O agrega varios (ej: QQQ, VGT):", "")
periodo = st.sidebar.selectbox("Rango Gráfica:", ["6mo", "1y", "2y"], index=1)

# 4. FUNCIÓN DE PROCESAMIENTO
def procesar_ticker(symbol):
    try:
        t_obj = yf.Ticker(symbol)
        df = t_obj.history(period="1y")
        if df.empty or len(df) < 50: return None
        
        # Cálculos
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        precio = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma50 = float(df['SMA50'].iloc[-1])
        
        # Fundamentales
        info = t_obj.info
        pe = info.get('trailingPE', 'N/A')
        div = f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%"

        # Señal Estricta
        if rsi < 32 and precio > (sma50 * 0.97): semaforo = "🟢 COMPRA (DIP)"
        elif rsi > 68: semaforo = "🔴 VENTA / CARO"
        elif precio > sma50 and 40 < rsi < 60: semaforo = "🔵 ALCISTA"
        elif precio < (sma50 * 0.95): semaforo = "💀 EVITAR"
        else: semaforo = "⚪ NEUTRAL"
        
        return {"Ticker": symbol, "Precio": round(precio, 2), "RSI": round(rsi, 2), "P/E": pe, "Div": div, "Señal": semaforo}
    except: return None

# 5. LÓGICA DE LISTA (Aquí estaba el error)
lista_final = []
if seleccion_busqueda:
    lista_final.append(seleccion_busqueda.split(" | ")[0]) # Extrae solo el Ticker
if tickers_manuales:
    adicionales = [t.strip().upper() for t in tickers_manuales.split(",") if t.strip()]
    lista_final.extend(adicionales)

lista_final = list(set(lista_final)) # Quitar duplicados

# 6. RESULTADOS
resultados = []
for t in lista_final:
    res = procesar_ticker(t)
    if res: resultados.append(res)

if resultados:
    st.subheader("📊 Comparativa")
    df_res = pd.DataFrame(resultados)
    
    def color_señal(val):
        color = '#1e1e1e'
        if 'COMPRA' in val: color = '#008000'
        if 'VENTA' in val: color = '#FF0000'
        if 'ALCISTA' in val: color = '#0055ff'
        return f'background-color: {color}; color: white; font-weight: bold'

    st.dataframe(df_res.style.applymap(color_señal, subset=['Señal']), use_container_width=True, hide_index=True)

    # Gráfica del primer ticker de la lista
    st.divider()
    t_graf = lista_final[0]
    st.subheader(f"🔍 Gráfico: {t_graf}")
    data_graf = yf.download(t_graf, period=periodo)
    if not data_graf.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data_graf.index, y=data_graf['Close'].squeeze(), name='Precio'))
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Escribe un nombre o Ticker en el buscador de la izquierda.")
