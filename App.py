import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Screener Equity Research Pro", layout="wide")
st.title("🎯 Terminal de Análisis: Precios Objetivo y Firmas")

# 2. BUSCADOR DINÁMICO
def buscar_en_yahoo(search_term: str):
    if not search_term or len(search_term) < 2: return []
    try:
        yquery = yf.Search(search_term, max_results=6)
        return [f"{q['symbol']} | {q.get('shortname', '')}" for q in yquery.quotes]
    except: return []

st.sidebar.header("🔍 Selección de Activo")
seleccion = st_searchbox(buscar_en_yahoo, key="search_v3", label="Busca una acción (ej: MSFT):")
periodo_graf = st.sidebar.selectbox("Rango Visual:", ["1y", "2y", "5y"], index=0)

# 3. PROCESAMIENTO PRINCIPAL
if seleccion:
    ticker_id = seleccion.split(" | ")[0]
    
    # Descarga de datos previa (Fuera de los tabs para evitar que se quede cargando)
    with st.spinner(f"Cargando datos de {ticker_id}..."):
        t_obj = yf.Ticker(ticker_id)
        hist = t_obj.history(period=periodo_graf)
        info = t_obj.info
        
    if not hist.empty:
        # PESTAÑAS
        tab1, tab2, tab3 = st.tabs(["📊 Resumen y Señal", "🏛️ Equity Research", "📈 Gráfico Interactivo"])

        with tab1:
            col_a, col_b = st.columns(2)
            with col_a:
                precio_actual = info.get('currentPrice', hist['Close'].iloc[-1])
                st.metric("Precio Actual", f"${precio_actual:.2f} USD")
            with col_b:
                # Lógica de RSI rápida
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
                st.metric("RSI (14d)", f"{rsi:.2f}")

      with tab2:
            st.subheader("🎯 Consenso de Equity Research")
            c1, c2, c3 = st.columns(3)
            
            # Precios Objetivo
            t_low = info.get('targetLowPrice', 'N/A')
            t_mean = info.get('targetMeanPrice', 'N/A')
            t_high = info.get('targetHighPrice', 'N/A')
            
            c1.metric("Target Mínimo", f"${t_low}")
            c2.metric("Target Promedio", f"${t_mean}")
            c3.metric("Target Máximo", f"${t_high}")

            st.divider()
            
            # --- NUEVA LÓGICA DE RESPALDO PARA FIRMAS ---
            st.subheader("📊 Sentimiento del Mercado")
            
            try:
                # Intentamos obtener el conteo de recomendaciones (Buy, Hold, Sell)
                recom_summary = info.get('recommendationMean', 'N/A')
                recom_key = info.get('recommendationKey', 'N/A').upper()
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.write(f"**Consenso Actual:** {recom_key}")
                    st.write(f"**Puntuación (1-5):** {recom_summary}")
                    st.caption("1.0 = Compra Fuerte | 5.0 = Venta Fuerte")

                # Intentamos mostrar la tabla de firmas con un método alternativo
                recomendas = t_obj.get_recommendations() # Usamos la función directa
                
                if recomendas is not None and not recomendas.empty:
                    st.write("### 📋 Desglose de Firmas Analistas")
                    # Limpiamos y mostramos solo lo relevante
                    df_slim = recomendas.tail(10).reset_index()
                    # Si las columnas esperadas no existen, mostramos lo que haya
                    st.dataframe(df_slim, use_container_width=True)
                else:
                    # Si la tabla falla, mostramos los datos fundamentales de crecimiento
                    st.warning("⚠️ El desglose detallado por firmas no está disponible públicamente para este activo.")
                    st.info(f"**Tip de Analista:** El crecimiento de ingresos reportado es del {info.get('revenueGrowth', 0)*100:.1f}% y el margen operativo es del {info.get('operatingMargins', 0)*100:.1f}%.")
            
            except Exception as e:
                st.error("No se pudo obtener el desglose de firmas. Mostrando datos de valor:")
                st.write(f"**Precio Actual vs Objetivo:** La acción está a un {((float(t_mean)/precio_actual)-1)*100:.2f}% de su precio objetivo promedio.")

        with tab3:
            # GRÁFICA CORREGIDA (Sin bloqueos de carga)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist['Close'].squeeze(), 
                name='Precio de Cierre',
                line=dict(color='#00ffcc', width=2)
            ))
            
            # Media Móvil 50 para contexto
            hist['SMA50'] = hist['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist['SMA50'].squeeze(), 
                name='SMA 50',
                line=dict(color='orange', dash='dot')
            ))

            fig.update_layout(
                template="plotly_dark",
                height=500,
                margin=dict(l=20, r=20, t=30, b=20),
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("No se encontraron datos históricos para este ticker.")
else:
    st.info("👋 Bienvenida/o. Busca una empresa en el panel izquierdo para desplegar el Equity Research.")
