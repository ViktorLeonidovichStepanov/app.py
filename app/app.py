import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="Crypto Analysis",
    page_icon="📊",
    layout="wide"
)

# Инициализация состояния для автообновления
if 'last_update' not in st.session_state:
    st.session_state.last_update = 0

CRYPTO_PAIRS = ['DOGE_USDT', 'LINK_USDT', 'SEI_USDT', 'ALCH_USDT', 'GIGGLE_USDT', 'COAI_USDT', 'FARTCOIN_USDT']

def get_gateio_data(symbol):
    """
    Получение данных с Gate.io API.
    Внимание: Некоторые пары (COAI, FARTCOIN и др.) могут не существовать,
    поэтому для них будет возвращена ошибка.
    """
    try:
        url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={symbol}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                ticker = data[0]
                return {
                    'symbol': symbol,
                    'last': float(ticker.get('last', 0)),
                    'change_percentage': float(ticker.get('change_percentage', 0)),
                    'high_24h': float(ticker.get('high_24h', 0)),
                    'low_24h': float(ticker.get('low_24h', 0)),
                    'quote_volume': float(ticker.get('quote_volume', 0)),
                    'source': 'Gate.io',
                    'available': True
                }
        # Если пара не найдена (API возвращает пустой список или ошибку)
        return {
            'symbol': symbol,
            'available': False,
            'error': 'Пара не найдена на Gate.io'
        }
    except Exception as e:
        return {
            'symbol': symbol,
            'available': False,
            'error': f'Ошибка запроса: {str(e)}'
        }

def main():
    st.title("📊 Обзор криптовалютных пар")
    st.markdown("Данные с биржи Gate.io")
    
    # Автообновление
    auto_refresh = st.sidebar.checkbox("Автообновление (60 сек)", value=True)
    
    if auto_refresh:
        current_time = time.time()
        if current_time - st.session_state.last_update > 60:
            st.session_state.last_update = current_time
            st.rerun()
    
    # Получение и отображение данных
    for symbol in CRYPTO_PAIRS:
        data = get_gateio_data(symbol)
        
        st.subheader(f"🔹 {symbol.replace('_', '/')}")
        
        if data['available']:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Цена", 
                    f"${data['last']:.6f}", 
                    f"{data['change_percentage']:.2f}%"
                )
            
            with col2:
                st.metric("Макс. 24ч", f"${data['high_24h']:.6f}")
            
            with col3:
                st.metric("Мин. 24ч", f"${data['low_24h']:.6f}")
            
            with col4:
                st.metric("Объем", f"${data['quote_volume']:,.0f}")
            
            # Простой график на основе изменения цены
            chart_data = pd.DataFrame({
                'Время': range(24),
                'Цена': [data['last'] * (1 + data['change_percentage']/100 * i/24) for i in range(24)]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_data['Время'], y=chart_data['Цена'], mode='lines', name='Цена'))
            fig.update_layout(title=f"Динамика {symbol.replace('_', '/')}", height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error(f"❌ {data.get('error', 'Пара недоступна')}")
        
        st.markdown("---")
    
    # Время обновления и ручное обновление
    st.sidebar.markdown(f"**Последнее обновление:** {datetime.now().strftime('%H:%M:%S')}")
    if st.sidebar.button("🔄 Обновить вручную"):
        st.session_state.last_update = time.time()
        st.rerun()

if __name__ == "__main__":
    main()