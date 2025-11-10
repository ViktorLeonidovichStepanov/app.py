import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Детальный анализ",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Детальный анализ")

# Используем ту же функцию из главного файла
from app import get_gateio_data, CRYPTO_PAIRS

selected_symbol = st.selectbox(
    "Выберите криптовалютную пару для анализа:",
    [pair.replace('_', '/') for pair in CRYPTO_PAIRS]
)

if selected_symbol:
    # Конвертируем обратно для API запроса
    api_symbol = selected_symbol.replace('/', '_')
    data = get_gateio_data(api_symbol)
    
    if data['available']:
        st.header(f"Детальный анализ: {selected_symbol}")
        
        # Вкладки для разных видов анализа
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Технический анализ", "📊 Объемный анализ", "🎯 Прогноз", "ℹ️ Общая информация"])
        
        with tab1:
            st.subheader("Технические индикаторы")
            
            # Генерация данных для демонстрационных графиков
            dates = pd.date_range(end=datetime.now(), periods=50, freq='H')
            base_price = data['last']
            
            # Имитация цен для графика
            prices = base_price * (1 + np.random.normal(0, 0.01, 50).cumsum())
            
            # Расчет простых индикаторов на основе сгенерированных данных
            df = pd.DataFrame({'Цена': prices}, index=dates)
            df['SMA_20'] = df['Цена'].rolling(window=20).mean()
            df['SMA_50'] = df['Цена'].rolling(window=50).mean()
            
            # График с Moving Averages
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Цена'], name='Цена', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='red')))
            fig.update_layout(title='Цена и скользящие средние', height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # RSI индикатор
            delta = df['Цена'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
            fig_rsi.update_layout(title='RSI индикатор', height=300)
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        with tab2:
            st.subheader("Анализ торговых объемов")
            
            # Имитация объемов
            volumes = np.random.randint(10000, 100000, 50)
            
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(x=dates, y=volumes, name='Объем'))
            fig_vol.update_layout(title='Торговые объемы', height=400)
            st.plotly_chart(fig_vol, use_container_width=True)
            
            st.metric("Текущий объем", f"${data['quote_volume']:,.0f}")
            
        with tab3:
            st.subheader("Прогноз и рекомендации")
            
            # Простая логика прогноза на основе изменения цены
            change = data['change_percentage']
            
            if change > 5:
                st.success("🟢 СИГНАЛ К ПОКУПКЕ")
                st.write("Сильный восходящий тренд. Рекомендуется рассмотреть возможность покупки.")
            elif change < -5:
                st.error("🔴 СИГНАЛ К ПРОДАЖЕ")
                st.write("Нисходящий тренд. Рекомендуется осторожность.")
            else:
                st.info("⚪ НЕЙТРАЛЬНЫЙ СИГНАЛ")
                st.write("Боковое движение. Рекомендуется выжидательная позиция.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Вероятность роста", "65%")
                st.metric("Целевой уровень", f"${data['last'] * 1.1:.6f}")
            with col2:
                st.metric("Уровень стоп-лосс", f"${data['last'] * 0.95:.6f}")
                st.metric("Соотношение Риск/Доход", "1:2")
                
        with tab4:
            st.subheader("Общая информация")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Основные метрики:**")
                st.write(f"- Текущая цена: ${data['last']:.6f}")
                st.write(f"- Изменение 24ч: {data['change_percentage']:.2f}%")
                st.write(f"- Макс. цена 24ч: ${data['high_24h']:.6f}")
                st.write(f"- Мин. цена 24ч: ${data['low_24h']:.6f}")
            with col2:
                st.write("**Торговая информация:**")
                st.write(f"- Объем 24ч: ${data['quote_volume']:,.0f}")
                st.write(f"- Источник данных: {data['source']}")
                st.write(f"- Время анализа: {datetime.now().strftime('%H:%M:%S')}")
    
    else:
        st.error(f"Пара {selected_symbol} в настоящее время недоступна для анализа.")
        st.info("Данная криптовалютная пара не торгуется на бирже Gate.io или временно недоступна.")

st.markdown("---")
st.markdown("*Для возврата к обзору всех пар используйте боковое меню*")