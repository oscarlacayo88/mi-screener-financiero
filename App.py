import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Screener Global MXN", layout="wide")
st.title("🌎 Screener Financiero (USD & MXN)")

# 2. FUNCIÓN DE BÚSQUEDA DINÁMICA
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=8)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

# 3. OBTENER TIPO DE CAMBIO (USD/MXN)
@st.cache_data(ttl=3600)
def obtener_tipo_cambio():
    try:
        cva = yf.Ticker("USDMXN=X")
        return float(cva.history(period="1d")['Close'].iloc[-1])
    except: return 18.0 # Valor de respaldo si falla la conexión

tipo_cambio = obtener_tipo_cambio()

# 4. BARRA LATERAL
st.sidebar.header("🔍 Configuración")
seleccion_busqueda = st_searchbox(
    buscar_en_yahoo,
    key="search_global",
    placeholder="Ej: Tesla, Apple, VGT...",
    label="Buscador de Activos:"
)

tickers_manuales = st.sidebar.text_input("Otros Tickers (ej: QQQ, VOO):", "")

# --- NUEVOS RANGOS SOLICITADOS ---
periodo = st.sidebar.selectbox(
    "Rango de la Gráfica:", 
    ["1y", "2y", "3y", "5y"], 
    index=0
)

# 5. FUNCIÓN DE PROCESAMIENTO ESTRICTO
def procesar_ticker(symbol):
    try:
        t_obj = yf.Ticker(symbol)
        df = t_obj.history(period="5y") # Bajamos suficiente historial para SMA
        if df.empty or len(df) < 50: return None
        
        # Cálculos Técnicos
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        precio_usd = float(df['Close'].iloc[-1].item())
        rsi = float(df['RSI'].iloc[-1].item())
        sma50 = float(df['SMA50'].iloc[-1].item())
        
        # Fundamentales
        info = t_obj.info
        pe = info.get('trailingPE', 'N/A')
        div = f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%"

        # Lógica de Señal Estricta
        if rsi < 32 and precio_usd > (sma50 * 0.97): semaforo = "🟢 COMPRA (DIP)"
        elif rsi > 68: semaforo = "🔴 VENTA / CARO"
        elif precio_usd > sma50 and 40 < rsi < 60: semaforo = "🔵 ALCISTA"
        elif precio_usd < (sma50 * 0.95): semaforo = "💀 EVITAR"
        else: semaforo = "⚪ NEUTRAL"
        
        return {
            "Ticker": symbol, 
            "Precio USD": round(precio_usd, 2),
            "Precio MXN": f"${round(precio_usd * tipo_cambio, 2):,}",
            "RSI": round(rsi, 2), 
            "P/E": pe, 
            "Div": div, 
            "Señal": semaforo
        }
    except: return None

# 6. UNIFICAR LISTA
lista_final = []
if seleccion_busqueda:
    lista_final.append(seleccion_busqueda.split(" | ")[0])
if tickers_manuales:
    adicionales = [t.strip().upper() for t in tickers_manuales.split(",") if t.strip()]
    lista_final.extend(adicionales)
lista_final = list(set(lista_final))

# 7. RESULTADOS
resultados = []
for t in lista_final:
    res = procesar_ticker(t)
    if res: resultados.append(res)

if resultados:
    st.subheader(f"📊 Comparativa (Tipo de Cambio: ${tipo_cambio:.2f} MXN)")
    df_res = pd.DataFrame(resultados)
    
    def color_señal(val):
        color = '#1e1e1e'
        if 'COMPRA' in val: color = '#008000'
        elif 'VENTA' in val: color = '#FF0000'
        elif 'ALCISTA' in val: color = '#0055ff'
        return f'background-color: {color}; color: white; font-weight: bold'

    st.dataframe(df_res.style.applymap(color_señal, subset=['Señal']), use_container_width=True, hide_index=True)

    # Gráfica Detallada
    st.divider()
    t_graf = lista_final[0]
    st.subheader(f"🔍 Gráfico Histórico ({periodo}): {t_graf}")
    data_graf = yf.download(t_graf, period=periodo)
    
    if not data_graf.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data_graf.index, y=data_graf['Close'].squeeze(), name='Precio USD'))
        fig.update_layout(template="plotly_dark", height=450, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Usa el buscador para añadir activos al análisis.")
