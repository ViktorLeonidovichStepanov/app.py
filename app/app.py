import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="Gate.io Crypto Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния
if 'last_update' not in st.session_state:
    st.session_state.last_update = 0

CRYPTO_PAIRS = ['DOGE_USDT', 'LINK_USDT', 'SEI_USDT', 'ALCH_USDT', 'GIGGLE_USDT', 'COAI_USDT', 'FARTCOIN_USDT']

def get_gateio_data(symbol):
    """Получение реальных данных с Gate.io API"""
    try:
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                ticker = data[0]
                return {
                    'symbol': symbol,
                    'last': float(ticker['last']),
                    'change_percentage': float(ticker['change_percentage']),
                    'high_24h': float(ticker['high_24h']),
                    'low_24h': float(ticker['low_24h']),
                    'quote_volume': float(ticker['quote_volume']),
                    'base_volume': float(ticker['base_volume']),
                    'source': 'Gate.io',
                    'available': True
                }
    except Exception as e:
        st.error(f"Ошибка получения данных для {symbol}: {str(e)}")
    
    return {
        'symbol': symbol,
        'last': 0,
        'change_percentage': 0,
        'high_24h': 0,
        'low_24h': 0,
        'quote_volume': 0,
        'source': 'Не доступно',
        'available': False
    }

def main_page():
    st.title("📊 Анализ криптовалют - Gate.io")
    
    # Автообновление
    auto_refresh = st.sidebar.checkbox("Автообновление (60 сек)", value=True)
    
    if auto_refresh:
        current_time = time.time()
        if current_time - st.session_state.last_update > 60:
            st.session_state.last_update = current_time
            st.rerun()
    
    # Получение данных
    with st.spinner("Получение данных с Gate.io..."):
        for symbol in CRYPTO_PAIRS:
            data = get_gateio_data(symbol)
            
            st.subheader(f"🔹 {symbol.replace('_', '/')}")
            
            if data['available']:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Текущая цена", 
                        f"${data['last']:.6f}", 
                        f"{data['change_percentage']:.2f}%"
                    )
                
                with col2:
                    st.metric("24ч Максимум", f"${data['high_24h']:.6f}")
                
                with col3:
                    st.metric("24ч Минимум", f"${data['low_24h']:.6f}")
                
                with col4:
                    st.metric("Объем 24ч", f"${data['quote_volume']:,.0f}")
                
                # Простой график (симуляция на основе текущей цены)
                dates = pd.date_range(end=datetime.now(), periods=50, freq='H')
                prices = [data['last'] * (1 + i * 0.001) for i in range(-25, 25)]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Price'))
                fig.update_layout(title=f'График цены {symbol.replace("_", "/")}', height=300)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error("❌ Пара не торгуется на Gate.io или временно недоступна")
            
            st.markdown("---")
    
    # Время обновления
    st.sidebar.markdown(f"**Последнее обновление:** {datetime.now().strftime('%H:%M:%S')}")
    
    if st.sidebar.button("🔄 Обновить вручную"):
        st.session_state.last_update = time.time()
        st.rerun()

if __name__ == "__main__":
    main_page()
