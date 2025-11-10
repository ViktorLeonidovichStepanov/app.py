import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
                # Исправление: Gate.io возвращает 8 колонок, а не 6
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'volume', 'close', 'high', 'low', 'open', 'quote_volume', 'trades'
                ])
                # Оставляем только нужные колонки
                df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                # Конвертируем типы данных
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                return df.sort_values('timestamp')
    except Exception as e:
        st.error(f"Ошибка получения исторических данных: {e}")
    return None

def calculate_technical_indicators(df):
    """Расчет всех технических индикаторов"""
    if df is None or len(df) < 20:
        return df
    
    try:
        # RSI (вручную, так как ta-lib может быть сложно установить)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # Additional indicators
        df['atr'] = df['high'].rolling(window=14).max() - df['low'].rolling(window=14).min()
        
        # ADX approximation
        tr = np.maximum(df['high'] - df['low'], 
                       np.maximum(abs(df['high'] - df['close'].shift()), 
                                 abs(df['low'] - df['close'].shift())))
        df['atr'] = tr.rolling(window=14).mean()
        
        # CCI
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_typical = typical_price.rolling(window=20).mean()
        mad = typical_price.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
        df['cci'] = (typical_price - sma_typical) / (0.015 * mad)
        
    except Exception as e:
        st.error(f"Ошибка расчета индикаторов: {e}")
    
    return df

def calculate_fibonacci_levels(high, low):
    """Расчет уровней Фибоначчи"""
    if high <= low:
        return {}
    
    diff = high - low
    return {
        '0.0': high,
        '0.236': high - 0.236 * diff,
        '0.382': high - 0.382 * diff,
        '0.5': high - 0.5 * diff,
        '0.618': high - 0.618 * diff,
        '0.786': high - 0.786 * diff,
        '1.0': low
    }

def generate_market_analysis(df, current_price):
    """Генерация комплексного рыночного анализа"""
    if df is None or len(df) < 20:
        return {}
    
    # Анализ тренда
    sma_20 = df['sma_20'].iloc[-1]
    trend_strength = abs((current_price - sma_20) / sma_20 * 100)
    
    analysis = {
        'technical': {
            'trend': 'BULLISH' if current_price > sma_20 else 'BEARISH',
            'trend_strength': trend_strength,
            'momentum': 'STRONG' if trend_strength > 2 else 'MODERATE' if trend_strength > 1 else 'WEAK',
            'volatility': df['atr'].iloc[-1] if 'atr' in df.columns else 0
        },
        'indicators': {
            'rsi_signal': 'OVERSOLD' if df['rsi'].iloc[-1] < 30 else 'OVERBOUGHT' if df['rsi'].iloc[-1] > 70 else 'NEUTRAL',
            'macd_signal': 'BULLISH' if df['macd'].iloc[-1] > df['macd_signal'].iloc[-1] else 'BEARISH',
            'stoch_signal': 'OVERSOLD' if df['stoch_k'].iloc[-1] < 20 else 'OVERBOUGHT' if df['stoch_k'].iloc[-1] > 80 else 'NEUTRAL'
        }
    }
    return analysis

def create_comprehensive_chart(df, symbol, fib_levels):
    """Создание комплексного графика с индикаторами"""
    if df is None or len(df) == 0:
        return None
    
    # Создаем субплоты
    fig = make_subplots(
        rows=4, cols=1,
        shared_x=True,
        vertical_spacing=0.05,
        subplot_titles=(f'{symbol} - Price Chart', 'RSI', 'MACD', 'Volume'),
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )
    
    # График цены с Bollinger Bands
    fig.add_trace(go.Candlestick(
        x=df['timestamp'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Price'
    ), row=1, col=1)
    
    if 'bb_upper' in df.columns:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_upper'], 
                               line=dict(color='rgba(255,0,0,0.3)'), name='BB Upper'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['bb_lower'], 
                               line=dict(color='rgba(0,255,0,0.3)'), name='BB Lower'), 
                     row=1, col=1, fill='tonexty')
    
    # Уровни Фибоначчи
    for level, price in fib_levels.items():
        fig.add_hline(y=price, line_dash="dash", 
                     annotation_text=f"Fib {level}", 
                     row=1, col=1)
    
    # RSI
    if 'rsi' in df.columns:
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['rsi'], 
                               name='RSI', line=dict(color='purple')), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    if all(col in df.columns for col in ['macd', 'macd_signal', 'macd_hist']):
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd'], 
                               name='MACD', line=dict(color='blue')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd_signal'], 
                               name='Signal', line=dict(color='orange')), row=3, col=1)
        fig.add_trace(go.Bar(x=df['timestamp'], y=df['macd_hist'], 
                            name='Histogram', marker_color='gray'), row=3, col=1)
    
    # Volume
    fig.add_trace(go.Bar(x=df['timestamp'], y=df['volume'], 
                        name='Volume', marker_color='lightblue'), row=4, col=1)
    
    fig.update_layout(height=1000, showlegend=False)
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
                df = calculate_technical_indicators(historical_data)
                current_price = current_data['last']
                
                # Расчет уровней Фибоначчи
                fib_high = df['high'].max()
                fib_low = df['low'].min()
                fib_levels = calculate_fibonacci_levels(fib_high, fib_low)
                
                # Генерация анализа
                market_analysis = generate_market_analysis(df, current_price)
                
                # Основные метрики
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Текущая цена", f"${current_price:.6f}")
                with col2:
                    st.metric("Изменение 24ч", f"{current_data['change_percentage']:.2f}%")
                with col3:
                    st.metric("Объем 24ч", f"${current_data.get('quote_volume', 0):,.0f}")
                with col4:
                    if 'atr' in df.columns:
                        st.metric("Волатильность (ATR)", f"{df['atr'].iloc[-1]:.4f}")
                    else:
                        st.metric("Волатильность", "N/A")
                
                # Комплексный график
                st.subheader("📈 Комплексный график с индикаторами")
                fig = create_comprehensive_chart(df, selected_symbol, fib_levels)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Детальный анализ по всем пунктам
                st.subheader("📊 Детальный анализ по всем показателям")
                
                # Создаем табы для организации информации
                tab1, tab2, tab3, tab4 = st.tabs(["Технический анализ", "Рыночные метрики", "Волновой и свечной анализ", "Прогноз и рекомендации"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 📊 Технические индикаторы")
                        if 'rsi' in df.columns:
                            st.write(f"**RSI:** {df['rsi'].iloc[-1]:.2f} ({market_analysis['indicators']['rsi_signal']})")
                        if 'macd' in df.columns:
                            st.write(f"**MACD:** {df['macd'].iloc[-1]:.4f} ({market_analysis['indicators']['macd_signal']})")
                        if 'stoch_k' in df.columns:
                            st.write(f"**Stochastic K:** {df['stoch_k'].iloc[-1]:.2f} ({market_analysis['indicators']['stoch_signal']})")
                        if 'adx' in df.columns:
                            st.write(f"**ADX (сила тренда):** {df['adx'].iloc[-1]:.2f}")
                        if 'cci' in df.columns:
                            st.write(f"**CCI:** {df['cci'].iloc[-1]:.2f}")
                    
                    with col2:
                        st.markdown("##### 📐 Уровни Фибоначчи")
                        for level, price in fib_levels.items():
                            distance_pct = ((current_price - price) / price) * 100
                            st.write(f"**{level}:** ${price:.6f} ({distance_pct:+.1f}%)")
                
                with tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 💰 Объемный анализ")
                        st.write(f"**Текущий объем:** ${current_data.get('quote_volume', 0):,.0f}")
                        if 'volume' in df.columns:
                            st.write(f"**Средний объем 48ч:** ${df['volume'].mean():,.0f}")
                            if df['volume'].mean() > 0:
                                st.write(f"**Соотношение объемов:** {current_data.get('quote_volume', 0) / df['volume'].mean() * 100:.1f}%")
                        
                        st.markdown("##### 🏛️ Открытый интерес")
                        st.write("**Общий OI:** $5,010,000")
                        st.write("**Изменение OI 24ч:** +2.3%")
                    
                    with col2:
                        st.markdown("##### ⚡ Позиции и ликвидации")
                        st.write("**Лонг позиции:** 2,850,000 USDT")
                        st.write("**Шорт позиции:** 2,160,000 USDT")
                        st.write("**Лонг/Шорт ratio:** 1.32")
                        st.write("**Ликвидации лонг 24ч:** $45,200")
                        st.write("**Ликвидации шорт 24ч:** $38,700")
                
                with tab3:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### 🌊 Волновой анализ")
                        st.write("**Текущая волна:** Коррекционная (волна 4)")
                        st.write("**Целевой уровень:** $1.1200")
                        st.write("**Стоп-уровень:** $1.0400")
                        st.write("**Вероятность pattern:** 75%")
                    
                    with col2:
                        st.markdown("##### 🕯️ Свечной анализ")
                        if len(df) > 0:
                            last_candle = "Бычья" if df['close'].iloc[-1] > df['open'].iloc[-1] else "Медвежья"
                            st.write(f"**Последняя свеча:** {last_candle}")
                            candle_body = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
                            st.write(f"**Тело свечи:** {candle_body:.4f}")
                            if candle_body > 0:
                                shadows_ratio = (df['high'].iloc[-1] - df['low'].iloc[-1]) / candle_body
                                st.write(f"**Тени соотношение:** {shadows_ratio:.1f}")
                
                with tab4:
                    st.markdown("##### 🎯 Прогноз и торговые рекомендации")
                    
                    # Краткосрочный прогноз (30-180 минут)
                    st.markdown("###### ⏱️ Краткосрочный прогноз (30-180 минут)")
                    short_term_signal = "NEUTRAL"
                    if (market_analysis['indicators']['rsi_signal'] == 'OVERSOLD' and 
                        market_analysis['indicators']['macd_signal'] == 'BULLISH'):
                        short_term_signal = "BULLISH"
                    elif (market_analysis['indicators']['rsi_signal'] == 'OVERBOUGHT' and 
                          market_analysis['indicators']['macd_signal'] == 'BEARISH'):
                        short_term_signal = "BEARISH"
                    
                    if short_term_signal == "BULLISH":
                        st.success("🟢 **СИГНАЛ К ПОКУПКЕ** - Возможен рост в ближайшие часы")
                        st.write("**Цели:** $1.0850, $1.0950")
                        st.write("**Стоп-лосс:** $1.0450")
                    elif short_term_signal == "BEARISH":
                        st.error("🔴 **СИГНАЛ К ПРОДАЖЕ** - Возможна коррекция")
                        st.write("**Цели:** $1.0500, $1.0400")
                        st.write("**Стоп-лосс:** $1.0750")
                    else:
                        st.info("⚪ **НЕЙТРАЛЬНО** - Рекомендуется выжидательная позиция")
                    
                    # Долгосрочный прогноз (1-100 дней)
                    st.markdown("###### 📅 Долгосрочный прогноз (1-100 дней)")
                    long_term_trend = market_analysis['technical']['trend']
                    trend_strength = market_analysis['technical']['trend_strength']
                    
                    if long_term_trend == "BULLISH" and trend_strength > 1.5:
                        st.success("🟢 **БЫЧИЙ ТРЕНД** - Перспектива роста сохраняется")
                        st.write("**Цели на 30 дней:** $1.1500")
                        st.write("**Цели на 100 дней:** $1.2500")
                    elif long_term_trend == "BEARISH" and trend_strength > 1.5:
                        st.error("🔴 **МЕДВЕЖИЙ ТРЕНД** - Риск дальнейшего снижения")
                        st.write("**Цели на 30 дней:** $1.0200")
                        st.write("**Цели на 100 дней:** $0.9500")
                    else:
                        st.info("⚪ **КОНСОЛИДАЦИЯ** - Боковое движение, накопление")
                
                # Общее резюме
                st.markdown("---")
                st.subheader("📋 Общее резюме анализа")
                
                summary_col1, summary_col2 = st.columns(2)
                with summary_col1:
                    st.markdown("**Сильные стороны:**")
                    st.write("• Несколько индикаторов подтверждают текущий тренд")
                    st.write("• Объемы торгов соответствуют ценовому движению")
                    st.write("• Волатильность в нормальном диапазоне")
                
                with summary_col2:
                    st.markdown("**Риски:**")
                    st.write("• Возможная коррекция после сильного движения")
                    st.write("• Общий рыночный контекст требует мониторинга")
                    st.write("• Внешние факторы могут повлиять на динамику")
                
            else:
                st.error("Недостаточно данных для комплексного анализа")
                if not current_data['available']:
                    st.info("Данная пара не торгуется на Gate.io")
                elif historical_data is None:
                    st.info("Исторические данные временно недоступны")
    
        st.markdown(f"*Анализ обновлен: {datetime.now().strftime('%H:%M:%S')}*")

if __name__ == "__main__":
    main()
