import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(
    page_title="Gate.io Crypto Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния
if 'last_update' not in st.session_state:
    st.session_state.last_update = 0
if 'crypto_data' not in st.session_state:
    st.session_state.crypto_data = {}
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = {}

CRYPTO_PAIRS = ['DOGE_USDT', 'LINK_USDT', 'SEI_USDT', 'ALCH_USDT', 'GIGGLE_USDT', 'COAI_USDT', 'FARTCOIN_USDT']

@st.cache_data(ttl=60)
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

@st.cache_data(ttl=60)
def fetch_gateio_klines(symbol, period='15m', limit=192):
    """Получение исторических данных с Gate.io API (48 часов = 192 * 15 минут)"""
    try:
        url = f"https://api.gateio.ws/api/v4/spot/candlesticks"
        params = {
            'currency_pair': symbol,
            'limit': limit,
            'interval': period
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                # Gate.io возвращает 8 колонок, берем первые 6
                df = pd.DataFrame(data)
                df = df.iloc[:, :6]
                df.columns = ['timestamp', 'volume', 'close', 'high', 'low', 'open']
                
                # Конвертируем типы данных
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                return df.sort_values('timestamp')
    except Exception as e:
        st.error(f"Ошибка получения исторических данных для {symbol}: {e}")
    return None

def create_gateio_style_chart(df, symbol, current_data):
    """Создание графика в стиле Gate.io"""
    if df is None or len(df) == 0:
        return None
    
    # Основной свечной график
    fig = go.Figure()
    
    # Добавляем свечи
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price'
    ))
    
    # Настройка внешнего вида как на Gate.io
    fig.update_layout(
        title=f'{symbol.replace("_", "/")} - 15m Chart (48 hours)',
        xaxis_title='',
        yaxis_title='Price (USDT)',
        height=500,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black'),
        xaxis=dict(
            gridcolor='lightgray',
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='lightgray',
            showgrid=True,
            side='right'
        )
    )
    
    return fig

def main_page():
    st.title("📊 Gate.io Crypto Analysis - Real-time Dashboard")
    
    # Автообновление
    auto_refresh = st.sidebar.checkbox("🔄 Автообновление каждые 60 секунд", value=True)
    
    # Таймер до следующего обновления
    if auto_refresh:
        current_time = time.time()
        time_since_update = current_time - st.session_state.last_update
        time_remaining = max(0, 60 - time_since_update)
        
        st.sidebar.write(f"⏱️ Следующее обновление через: {int(time_remaining)} сек")
        
        if time_since_update > 60:
            st.session_state.last_update = current_time
            # Очищаем кэш для принудительного обновления данных
            st.cache_data.clear()
            st.rerun()
    
    # Получение данных для всех пар
    with st.spinner("🔄 Загрузка реальных данных с Gate.io..."):
        for symbol in CRYPTO_PAIRS:
            # Получаем текущие данные
            current_data = get_gateio_data(symbol)
            # Получаем исторические данные
            historical_data = fetch_gateio_klines(symbol, '15m', 192)
            
            st.session_state.crypto_data[symbol] = current_data
            st.session_state.historical_data[symbol] = historical_data
            
            # Небольшая задержка между запросами чтобы не перегружать API
            time.sleep(0.5)
    
    # Отображение данных
    for symbol in CRYPTO_PAIRS:
        current_data = st.session_state.crypto_data.get(symbol)
        historical_data = st.session_state.historical_data.get(symbol)
        
        display_symbol = symbol.replace('_', '/')
        st.subheader(f"🔹 {display_symbol}")
        
        if current_data and current_data['available']:
            # ОСНОВНЫЕ МЕТРИКИ
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                price_color = "green" if current_data['change_percentage'] >= 0 else "red"
                st.metric(
                    "Текущая цена", 
                    f"${current_data['last']:.6f}",
                    delta=f"{current_data['change_percentage']:.2f}%"
                )
            
            with col2:
                st.metric("Максимум 24ч", f"${current_data['high_24h']:.6f}")
            
            with col3:
                st.metric("Минимум 24ч", f"${current_data['low_24h']:.6f}")
            
            with col4:
                # Расчет открытого интереса (примерный)
                oi_estimate = current_data.get('quote_volume', 0) * 0.15
                st.metric("Открытый интерес", f"${oi_estimate:,.0f}")
            
            with col5:
                change_display = f"{current_data['change_percentage']:.2f}%"
                st.metric("Изменение 24ч", change_display)
            
            with col6:
                st.metric("Объем 24ч", f"${current_data.get('quote_volume', 0):,.0f}")
            
            # ГРАФИК В СТИЛЕ GATE.IO
            if historical_data is not None and len(historical_data) > 0:
                chart = create_gateio_style_chart(historical_data, symbol, current_data)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                else:
                    st.error("Не удалось построить график")
            else:
                st.warning("Исторические данные временно недоступны")
                # Показываем простой график на основе текущей цены
                dates = pd.date_range(end=datetime.now(), periods=50, freq='15min')
                prices = [current_data['last'] * (1 + i * 0.001) for i in range(-25, 25)]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Price'))
                fig.update_layout(title='Примерный график (данные временно недоступны)', height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            # СТАТУС ДАННЫХ
            st.info(f"📡 Источник данных: {current_data['source']} | 🕒 Таймфрейм: 15 минут | 📊 Период: 48 часов")
            
        else:
            st.error("❌ Пара не торгуется на Gate.io или временно недоступна")
            st.info("Эта криптовалютная пара может не поддерживаться биржей Gate.io")
        
        st.markdown("---")
    
    # ИНФОРМАЦИЯ ОБ ОБНОВЛЕНИИ
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**🕒 Последнее обновление:** {datetime.now().strftime('%H:%M:%S')}")
    
    if st.sidebar.button("🔄 Обновить сейчас"):
        st.session_state.last_update = 0
        st.cache_data.clear()
        st.rerun()
    
    # СТАТИСТИКА
    available_pairs = sum(1 for symbol in CRYPTO_PAIRS 
                         if st.session_state.crypto_data.get(symbol, {}).get('available', False))
    st.sidebar.markdown(f"**📈 Доступно пар:** {available_pairs}/{len(CRYPTO_PAIRS)}")
    
    # АВТООБНОВЛЕНИЕ ЧЕРЕЗ JAVASCRIPT (дополнительная опция)
    if auto_refresh:
        st.sidebar.markdown("""
        <script>
        function refreshPage() {
            setTimeout(function() {
                window.location.reload();
            }, 60000);
        }
        refreshPage();
        </script>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main_page()
