import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Screener Pro con Target Prices", layout="wide")
st.title("🚀 Screener Financiero: Análisis de Analistas y Drivers")

# 2. FUNCIÓN DE BÚSQUEDA DINÁMICA
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=8)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

# 3. FUNCIÓN DE PROCESAMIENTO MEJORADA
def procesar_ticker(symbol):
    try:
        t_obj = yf.Ticker(symbol)
        df = t_obj.history(period="1y")
        if df.empty: return None
        
        # --- Análisis Técnico ---
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        precio_usd = float(df['Close'].iloc[-1].item())
        rsi = float(df['RSI'].iloc[-1].item())
        sma50 = float(df['SMA50'].iloc[-1].item())
        
        # --- Datos de Analistas y Drivers ---
        info = t_obj.info
        target_price = info.get('targetMeanPrice', 0)
        upside = ((target_price - precio_usd) / precio_usd * 100) if target_price else 0
        resumen = info.get('longBusinessSummary', "Sin descripción disponible.")
        
        # Lógica de Señal
        if rsi < 32 and precio_usd > (sma50 * 0.97): semaforo = "🟢 COMPRA"
        elif rsi > 68: semaforo = "🔴 VENTA"
        else: semaforo = "⚪ NEUTRAL"
        
        return {
            "Ticker": symbol,
            "Precio Actual": round(precio_usd, 2),
            "Target Price (Avg)": f"${target_price}" if target_price else "N/A",
            "Upside Potencial": f"{upside:.2f}%" if upside else "N/A",
            "RSI": round(rsi, 2),
            "Señal": semaforo,
            "Drivers": resumen
        }
    except: return None

# 4. BARRA LATERAL
st.sidebar.header("🔍 Configuración")
seleccion = st_searchbox(buscar_en_yahoo, key="search", label="Busca un activo:")
tickers_extra = st.sidebar.text_input("Otros Tickers:", "")
periodo = st.sidebar.selectbox("Rango Gráfica:", ["1y", "2y", "3y", "5y"])

# 5. UNIFICAR Y EJECUTAR
lista = []
if seleccion: lista.append(seleccion.split(" | ")[0])
if tickers_extra: lista.extend([t.strip().upper() for t in tickers_extra.split(",")])
lista = list(set(lista))

resultados = []
for t in lista:
    res = procesar_ticker(t)
    if res: resultados.append(res)

# 6. MOSTRAR RESULTADOS
if resultados:
    st.subheader("📊 Comparativa de Mercado y Analistas")
    df_res = pd.DataFrame(resultados)
    
    # Mostramos la tabla (sin la columna de Drivers para que no se vea gigante)
    st.dataframe(df_res.drop(columns=['Drivers']), use_container_width=True, hide_index=True)

    # 7. DRIVERS DE CRECIMIENTO (Expander por cada ticker)
    st.divider()
    st.subheader("💡 Drivers de Crecimiento y Tesis de Inversión")
    
    for r in resultados:
        with st.expander(f"¿Por qué invertir en {r['Ticker']}?"):
            st.write(f"**Análisis de Analistas:** El precio objetivo promedio es de **{r['Target Price (Avg)']}**, lo que representa un retorno esperado del **{r['Upside Potencial']}**.")
            st.write("**Resumen del Negocio:**")
            st.info(r['Drivers'])

    # 8. GRÁFICA
    st.divider()
    t_graf = lista[0]
    data_graf = yf.download(t_graf, period=periodo)
    if not data_graf.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data_graf.index, y=data_graf['Close'].squeeze(), name='Precio'))
        fig.update_layout(template="plotly_dark", height=400, title=f"Histórico: {t_graf}")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Busca un activo para ver el Target Price y sus Drivers.")
