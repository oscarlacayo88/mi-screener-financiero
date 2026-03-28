import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN Y TABS
st.set_page_config(page_title="Screener Equity Research", layout="wide")
st.title("🎯 Análisis de Instituciones y Target Prices")

# 2. FUNCIÓN DE BÚSQUEDA (Mantenemos la anterior)
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=5)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

# 3. BARRA LATERAL
st.sidebar.header("🔍 Activo a Analizar")
seleccion = st_searchbox(buscar_en_yahoo, key="search_research", label="Busca una acción:")

# 4. PROCESAMIENTO DE DATOS DE RESEARCH
if seleccion:
    ticker_simbolo = seleccion.split(" | ")[0]
    t_obj = yf.Ticker(ticker_simbolo)
    info = t_obj.info
    
    # Creamos pestañas para organizar la info
    tab1, tab2, tab3 = st.tabs(["📊 Screener Técnico", "🏛️ Equity Research", "📈 Gráfico Histórico"])

    with tab1:
        st.subheader("Indicadores Rápidos")
        precio = info.get('currentPrice', 0)
        # (Aquí iría tu lógica de RSI y SMA50 que ya tenemos)
        st.metric("Precio Actual", f"${precio} USD", delta=f"{info.get('revenueGrowth', 0)*100:.1f}% Growth")

    with tab2:
        st.subheader(f"Opinión de Instituciones sobre {ticker_simbolo}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            low = info.get('targetLowPrice', 'N/A')
            st.metric("Target Mínimo", f"${low}")
        with col2:
            avg = info.get('targetMeanPrice', 'N/A')
            st.metric("Target Promedio", f"${avg}", help="Promedio de todos los analistas")
        with col3:
            high = info.get('targetHighPrice', 'N/A')
            st.metric("Target Máximo", f"${high}")

        st.divider()
        st.write("### 📋 Desglose de Recomendaciones Recientes")
        
        # Intentamos obtener la tabla de quién establece qué
        try:
            recom = t_obj.recommendations
            if recom is not None and not recom.empty:
                # Limpiamos la tabla para que sea legible
                recom_display = recom.tail(10).copy() # Últimas 10 actualizaciones
                st.table(recom_display[['Firm', 'To Grade', 'Action']])
            else:
                st.info("Yahoo Finance no proporciona el desglose detallado de firmas para este ticker, pero el consenso es: " + info.get('recommendationKey', 'N/A').upper())
        except:
            st.warning("No se pudo cargar el desglose detallado de firmas.")

    with tab3:
        # Aquí va tu código de la gráfica interactiva que ya funciona
        st.write("Gráfica interactiva cargando...")
        # (Copia aquí tu bloque de fig = go.Figure()...)

else:
    st.info("Selecciona una acción en el buscador de la izquierda para ver el análisis de los bancos de inversión.")
