import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from streamlit_searchbox import st_searchbox # <--- Nueva importación

# 1. FUNCIÓN DE BÚSQUEDA REAL EN TIEMPO REAL
def buscar_tickers_en_yahoo(search_term: str):
    if not search_term:
        return []
    try:
        # Consultamos a Yahoo Finance por coincidencias
        yquery = yf.Search(search_term, max_results=8)
        # Formateamos la sugerencia como "AAPL - Apple Inc."
        return [f"{q['symbol']} - {q['shortname']}" for q in yquery.quotes]
    except:
        return []

# 2. BARRA LATERAL CON BUSCADOR DINÁMICO
st.sidebar.header("🔍 Buscador Universal")

# Este cuadro reemplaza al selectbox anterior
ticker_seleccionado_full = st_searchbox(
    buscar_tickers_en_yahoo,
    key="buscador_universal",
    placeholder="Escribe: Nvidia, QQQ, Walmart...",
    label="Busca cualquier activo del mundo:"
)

# Extraemos solo el Ticker (la parte antes del guion)
ticker_final = ""
if ticker_seleccionado_full:
    ticker_final = ticker_seleccionado_full.split(" - ")[0]

# --- El resto de tu lógica de procesamiento sigue igual ---
# Solo asegúrate de usar `ticker_final` en tu lista_final

# 3. FUNCIÓN DE PROCESAMIENTO (CON CIERRE CORRECTO)
def procesar_ticker(symbol):
    try:
        t_obj = yf.Ticker(symbol)
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
        
        precio = float(df['Close'].iloc[-1].item())
        rsi = float(df['RSI'].iloc[-1].item())
        sma50 = float(df['SMA50'].iloc[-1].item())
        
        # Datos Fundamentales
        info = t_obj.info
        pe_ratio = info.get('trailingPE', 'N/A')
        div_yield = info.get('dividendYield', 0)
        div_str = f"{div_yield * 100:.2f}%" if div_yield else "0%"

        # --- LÓGICA ESTRICTA ---
        # Caso 1: Compra en el "Dip" (RSI bajo pero tendencia sana)
        if rsi < 32 and precio > (sma50 * 0.97):
            semaforo = "🟢 COMPRA (DIP)"
        # Caso 2: Sobrecompra (Demasiado caro)
        elif rsi > 68:
            semaforo = "🔴 VENTA / CARO"
        # Caso 3: Tendencia Alcista Saludable
        elif precio > sma50 and 40 < rsi < 60:
            semaforo = "🔵 ALCISTA SÓLIDO"
        # Caso 4: Debilidad / Tendencia Bajista
        elif precio < (sma50 * 0.95):
            semaforo = "💀 EVITAR / BAJISTA"
        else:
            semaforo = "⚪ NEUTRAL"
        
        return {
            "Ticker": symbol, "Precio": round(precio, 2), "RSI": round(rsi, 2),
            "P/E": pe_ratio, "Div": div_str, "Señal": semaforo
        }
    except Exception as e:
        return None # Si hay error, el ticker simplemente no aparece

# 4. UNIFICAR Y EJECUTAR
lista_final = [ticker_buscado]
if tickers_manuales:
    adicionales = [t.strip().upper() for t in tickers_manuales.split(",") if t.strip()]
    lista_final.extend(adicionales)
lista_final = list(set(lista_final))

resultados = []
for t in lista_final:
    res = procesar_ticker(t)
    if res:
        resultados.append(res)

# 5. MOSTRAR RESULTADOS
if resultados:
    st.subheader("📊 Comparativa de Mercado")
    df_res = pd.DataFrame(resultados)
    
    # Estilo visual para la tabla (Mejorado para legibilidad)
    def color_señal(val):
        color_fondo = '#1e1e1e' # Gris oscuro por defecto
        color_texto = '#ffffff' # Blanco por defecto
        
        if 'COMPRA' in val: 
            color_fondo = '#008000' # Verde fuerte
        elif 'VENTA' in val: 
            color_fondo = '#FF0000' # Rojo fuerte
        elif 'ALCISTA' in val: 
            color_fondo = '#0055ff' # Azul vibrante
        elif 'EVITAR' in val:
            color_fondo = '#333333' # Gris muy oscuro
            color_texto = '#ff4b4b' # Texto rojo para peligro
            
        return f'background-color: {color_fondo}; color: {color_texto}; font-weight: bold;'

    # Aplicamos el estilo a la tabla
    st.dataframe(df_res.style.applymap(color_señal, subset=['Señal']), 
                 use_container_width=True, hide_index=True)

    # 6. GRÁFICA DETALLADA
    st.divider()
    st.subheader(f"🔍 Gráfico: {ticker_buscado}")
    data_graf = yf.download(ticker_buscado, period=periodo)
    if not data_graf.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data_graf.index, y=data_graf['Close'].squeeze(), name='Precio'))
        fig.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ingresa tickers en la barra lateral para comenzar.")
