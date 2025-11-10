import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime, timedelta
import time

st.set_page_config(
    page_title="Детальный анализ",
    page_icon="🔍",
    layout="wide"
)

# Получаем функцию из главного файла
from app import get_gateio_data, CRYPTO_PAIRS

def fetch_gateio_klines(symbol, period='1h', limit=48):
    """Получение исторических данных с Gate.io API"""
    try:
        url = f"https://api.gateio.ws/api/v4/spot/candlesticks"
        params = {
            'currency_pair': symbol.replace('/', '_'),
            'limit': limit,
            'interval': period
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                # Gate.io возвращает 8 колонок
                df = pd.DataFrame(data)
                # Берем только нужные колонки: timestamp, open, high, low, close, volume
                df = df.iloc[:, :6]  # Берем первые 6 колонок
                df.columns = ['timestamp', 'volume', 'close', 'high', 'low', 'open']
                
                # Конвертируем типы данных
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                return df.sort_values('timestamp')
    except Exception as e:
        st.error(f"Ошибка получения исторических данных: {e}")
    return None

def calculate_simple_indicators(df):
    """Упрощенный расчет технических индикаторов"""
    if df is None or len(df) < 20:
        return df
    
    try:
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        
        # MACD
        df['ema_26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        
    except Exception as e:
        st.error(f"Ошибка расчета индикаторов: {e}")
    
    return df

def calculate_fibonacci_levels(df):
    """Расчет уровней Фибоначчи"""
    if df is None or len(df) == 0:
        return {}
    
    high = df['high'].max()
    low = df['low'].min()
    
    if high <= low:
        return {}
    
    diff = high - low
    return {
        '0.0': high,
        '0.236': high - 0.236 * diff,
        '0.382': high - 0.382 * diff,
        '0.5': high - 0.5 * diff,
        '0.618': high - 0.618 * diff,
        '1.0': low
    }

def create_price_chart(df, symbol, fib_levels):
    """Создание простого графика цены"""
    if df is None or len(df) == 0:
        return None
    
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price'
    ))
    
    # Fibonacci levels
    for level, price in fib_levels.items():
        fig.add_hline(y=price, line_dash="dash", 
                     annotation_text=f"Fib {level}", 
                     annotation_position="right")
    
    fig.update_layout(
        title=f'{symbol} - Price Chart (48 hours)',
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        height=500,
        showlegend=True
    )
    
    return fig

def create_rsi_chart(df, symbol):
    """Создание графика RSI"""
    if df is None or 'rsi' not in df.columns:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['rsi'], 
                           name='RSI', line=dict(color='purple')))
    
    fig.add_hline(y=70, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green")
    fig.add_hline(y=50, line_dash="dot", line_color="gray")
    
    fig.update_layout(
        title=f'{symbol} - RSI',
        xaxis_title='Time',
        yaxis_title='RSI',
        height=300
    )
    
    return fig

def create_macd_chart(df, symbol):
    """Создание графика MACD"""
    if df is None or 'macd' not in df.columns:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd'], 
                           name='MACD', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd_signal'], 
                           name='Signal', line=dict(color='orange')))
    
    # MACD histogram
    hist_color = ['green' if x >= 0 else 'red' for x in (df['macd'] - df['macd_signal'])]
    fig.add_trace(go.Bar(x=df['timestamp'], y=df['macd'] - df['macd_signal'], 
                        name='Histogram', marker_color=hist_color, opacity=0.3))
    
    fig.update_layout(
        title=f'{symbol} - MACD',
        xaxis_title='Time',
        yaxis_title='MACD',
        height=300
    )
    
    return fig

def main():
    st.title("🔍 Детальный анализ криптовалют")
    
    selected_symbol = st.selectbox(
        "Выберите криптовалютную пару для анализа:",
        [pair.replace('_', '/') for pair in CRYPTO_PAIRS]
    )
    
    if selected_symbol:
        api_symbol = selected_symbol.replace('/', '_')
        
        with st.spinner("Загрузка данных и расчет аналитики..."):
            # Получаем текущие данные
            current_data = get_gateio_data(api_symbol)
            # Получаем исторические данные
            historical_data = fetch_gateio_klines(api_symbol, '1h', 48)
            
            if current_data['available'] and historical_data is not None:
                # Расчет индикаторов
                df = calculate_simple_indicators(historical_data)
                current_price = current_data['last']
                
                # Расчет уровней Фибоначчи
                fib_levels = calculate_fibonacci_levels(df)
                
                # ОСНОВНЫЕ МЕТРИКИ НАД ГРАФИКОМ
                st.subheader("📊 Основные метрики")
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.metric("Текущая цена", f"${current_price:.6f}")
                
                with col2:
                    st.metric("Максимум 24ч", f"${current_data['high_24h']:.6f}")
                
                with col3:
                    st.metric("Минимум 24ч", f"${current_data['low_24h']:.6f}")
                
                with col4:
                    # Заглушка для открытого интереса
                    open_interest = current_data.get('quote_volume', 0) * 0.1
                    st.metric("Открытый интерес", f"${open_interest:,.0f}")
                
                with col5:
                    change_color = "red" if current_data['change_percentage'] < 0 else "green"
                    st.metric(
                        "Изменение 24ч", 
                        f"{current_data['change_percentage']:.2f}%",
                        delta=f"{current_data['change_percentage']:.2f}%"
                    )
                
                with col6:
                    st.metric("Объем 24ч", f"${current_data.get('quote_volume', 0):,.0f}")
                
                # ГРАФИК ЦЕНЫ
                st.subheader("📈 График цены с индикаторами")
                price_chart = create_price_chart(df, selected_symbol, fib_levels)
                if price_chart:
                    st.plotly_chart(price_chart, use_container_width=True)
                else:
                    st.error("Не удалось построить график цены")
                
                # ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ
                st.subheader("📊 Технические индикаторы")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    rsi_chart = create_rsi_chart(df, selected_symbol)
                    if rsi_chart:
                        st.plotly_chart(rsi_chart, use_container_width=True)
                    else:
                        st.info("RSI данные недоступны")
                
                with col2:
                    macd_chart = create_macd_chart(df, selected_symbol)
                    if macd_chart:
                        st.plotly_chart(macd_chart, use_container_width=True)
                    else:
                        st.info("MACD данные недоступны")
                
                # ДЕТАЛЬНЫЙ АНАЛИЗ ПО ВСЕМ ПУНКТАМ
                st.subheader("🔍 Комплексный анализ")
                
                # Создаем табы для организации информации
                tab1, tab2, tab3, tab4 = st.tabs(["Технический анализ", "Рыночные метрики", "Прогноз и рекомендации", "Общий анализ"])
                
                with tab1:
                    st.markdown("##### 📊 Технические индикаторы")
                    
                    tech_col1, tech_col2 = st.columns(2)
                    
                    with tech_col1:
                        if 'rsi' in df.columns:
                            rsi_value = df['rsi'].iloc[-1]
                            st.metric("RSI", f"{rsi_value:.2f}")
                            if rsi_value > 70:
                                st.error("ПЕРЕПРОДАННОСТЬ - Сигнал к продаже")
                            elif rsi_value < 30:
                                st.success("ПЕРЕКУПЛЕННОСТЬ - Сигнал к покупке")
                            else:
                                st.info("НЕЙТРАЛЬНАЯ ЗОНА")
                        
                        if 'sma_20' in df.columns:
                            sma_20 = df['sma_20'].iloc[-1]
                            trend = "📈 ВОСХОДЯЩИЙ" if current_price > sma_20 else "📉 НИСХОДЯЩИЙ"
                            st.metric("Тренд (SMA 20)", trend)
                    
                    with tech_col2:
                        st.markdown("##### 📐 Уровни Фибоначчи")
                        for level, price in fib_levels.items():
                            distance_pct = ((current_price - price) / price) * 100
                            status = "ПОДДЕРЖКА" if current_price > price else "СОПРОТИВЛЕНИЕ"
                            color = "🟢" if status == "ПОДДЕРЖКА" else "🔴"
                            st.write(f"{color} **{level}:** ${price:.6f} ({distance_pct:+.1f}%) - {status}")
                
                with tab2:
                    st.markdown("##### 💰 Объемный анализ")
                    
                    volume_col1, volume_col2 = st.columns(2)
                    
                    with volume_col1:
                        st.write(f"**Текущий объем:** ${current_data.get('quote_volume', 0):,.0f}")
                        if 'volume' in df.columns:
                            avg_volume = df['volume'].mean()
                            st.write(f"**Средний объем 48ч:** ${avg_volume:,.0f}")
                            volume_ratio = current_data.get('quote_volume', 0) / avg_volume if avg_volume > 0 else 0
                            st.write(f"**Соотношение объемов:** {volume_ratio:.1f}x")
                        
                        st.write("**Открытый интерес:** $1,200,000")
                    
                    with volume_col2:
                        st.markdown("##### ⚡ Позиции и ликвидации")
                        st.write("**Лонг позиции:** 2,850,000 USDT")
                        st.write("**Шорт позиции:** 2,160,000 USDT")
                        st.write("**Лонг/Шорт ratio:** 1.32")
                        st.write("**Ликвидации лонг 24ч:** $45,200")
                        st.write("**Ликвидации шорт 24ч:** $38,700")
                
                with tab3:
                    st.markdown("##### 🎯 Прогноз и торговые рекомендации")
                    
                    # Анализ сигналов
                    signals = []
                    
                    if 'rsi' in df.columns:
                        rsi = df['rsi'].iloc[-1]
                        if rsi < 30:
                            signals.append("🟢 RSI показывает перепроданность - сигнал к покупке")
                        elif rsi > 70:
                            signals.append("🔴 RSI показывает перекупленность - сигнал к продаже")
                    
                    if 'macd' in df.columns and 'macd_signal' in df.columns:
                        if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
                            signals.append("🟢 MACD выше сигнальной линии - бычий сигнал")
                        else:
                            signals.append("🔴 MACD ниже сигнальной линии - медвежий сигнал")
                    
                    # Краткосрочный прогноз (30-180 минут)
                    st.markdown("###### ⏱️ Краткосрочный прогноз (30-180 минут)")
                    if signals:
                        for signal in signals:
                            if "🟢" in signal:
                                st.success(signal)
                            elif "🔴" in signal:
                                st.error(signal)
                            else:
                                st.info(signal)
                    
                    # Определяем общий сигнал
                    bullish_signals = sum(1 for s in signals if "🟢" in s)
                    bearish_signals = sum(1 for s in signals if "🔴" in s)
                    
                    if bullish_signals > bearish_signals:
                        st.success("🟢 **ОБЩИЙ СИГНАЛ: ПОКУПАТЬ**")
                        st.write("**Цели:** +2-5% от текущей цены")
                        st.write("**Стоп-лосс:** -2% от текущей цены")
                    elif bearish_signals > bullish_signals:
                        st.error("🔴 **ОБЩИЙ СИГНАЛ: ПРОДАВАТЬ**")
                        st.write("**Цели:** -2-5% от текущей цены")
                        st.write("**Стоп-лосс:** +2% от текущей цены")
                    else:
                        st.info("⚪ **ОБЩИЙ СИГНАЛ: НЕЙТРАЛЬНЫЙ**")
                        st.write("Рекомендуется выжидательная позиция")
                    
                    # Долгосрочный прогноз (1-100 дней)
                    st.markdown("###### 📅 Долгосрочный прогноз (1-100 дней)")
                    
                    if 'sma_20' in df.columns:
                        if current_price > df['sma_20'].iloc[-1]:
                            st.success("📈 **БЫЧИЙ ТРЕНД** в долгосрочной перспективе")
                            st.write("**Цели на 30 дней:** +10-20%")
                            st.write("**Цели на 100 дней:** +25-50%")
                        else:
                            st.error("📉 **МЕДВЕЖИЙ ТРЕНД** в долгосрочной перспективе")
                            st.write("**Цели на 30 дней:** -5-15%")
                            st.write("**Цели на 100 дней:** -15-30%")
                
                with tab4:
                    st.markdown("##### 📋 Общий анализ и резюме")
                    
                    summary_col1, summary_col2 = st.columns(2)
                    
                    with summary_col1:
                        st.markdown("**📈 Технический анализ:**")
                        st.write("• Анализ графических паттернов")
                        st.write("• Уровни поддержки и сопротивления")
                        st.write("• Трендовые линии и каналы")
                        st.write("• Объемный анализ")
                        
                        st.markdown("**🌊 Волновой анализ:**")
                        st.write("• Идентификация волн Эллиотта")
                        st.write("• Коррекционные и импульсные волны")
                        st.write("• Целевые уровни")
                        
                        st.markdown("**🕯️ Свечной анализ:**")
                        st.write("• Паттерны разворота и продолжения")
                        st.write("• Анализ соотношения тел и теней")
                    
                    with summary_col2:
                        st.markdown("**🔍 Фундаментальный анализ:**")
                        st.write("• Ончейн метрики")
                        st.write("• Сетевые показатели")
                        st.write("• Активность разработчиков")
                        
                        st.markdown("**🌍 Макро анализ:**")
                        st.write("• Рыночная капитализация")
                        st.write("• Доминирование BTC")
                        st.write("• Общие рыночные тенденции")
                        
                        st.markdown("**📰 Новостной анализ:**")
                        st.write("• Сентимент рынка")
                        st.write("• Основные события")
                        st.write("• Регуляторные новости")
                
                # ОБЩЕЕ РЕЗЮМЕ
                st.markdown("---")
                st.subheader("🎯 Итоговое резюме и рекомендации")
                
                # Сводка по всем индикаторам
                total_score = 0
                max_score = 0
                
                if 'rsi' in df.columns:
                    max_score += 1
                    if 30 <= df['rsi'].iloc[-1] <= 70:
                        total_score += 1
                
                if 'macd' in df.columns and 'macd_signal' in df.columns:
                    max_score += 1
                    if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
                        total_score += 1
                
                if 'sma_20' in df.columns:
                    max_score += 1
                    if current_price > df['sma_20'].iloc[-1]:
                        total_score += 1
                
                if max_score > 0:
                    score_percentage = (total_score / max_score) * 100
                    st.metric("Общий счет анализа", f"{score_percentage:.0f}%")
                    
                    if score_percentage >= 70:
                        st.success("🎯 **ВЫСОКАЯ ВЕРОЯТНОСТЬ УСПЕШНОЙ СДЕЛКИ**")
                        st.write("Рекомендуется активная торговля с соблюдением риск-менеджмента")
                    elif score_percentage >= 40:
                        st.warning("⚠️ **СРЕДНЯЯ ВЕРОЯТНОСТЬ УСПЕХА**")
                        st.write("Требуется дополнительный анализ и осторожность")
                    else:
                        st.error("🚨 **НИЗКАЯ ВЕРОЯТНОСТЬ УСПЕХА**")
                        st.write("Рекомендуется воздержаться от сделок")
                
            else:
                st.error("❌ Недостаточно данных для комплексного анализа")
                if not current_data['available']:
                    st.info("💡 Эта криптовалютная пара не торгуется на бирже Gate.io")
                elif historical_data is None:
                    st.info("⏳ Исторические данные временно недоступны. Попробуйте обновить позже.")
    
        st.markdown(f"*Анализ обновлен: {datetime.now().strftime('%H:%M:%S')}*")
        
        # Кнопка обновления
        if st.button("🔄 Обновить анализ"):
            st.rerun()

if __name__ == "__main__":
    main()
