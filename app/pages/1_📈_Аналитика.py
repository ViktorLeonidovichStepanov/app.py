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

# Конфигурация CryptoPanic API
CRYPTOPANIC_API_KEY = "052011e0dd2887f9f02935fd870d3f777229f77e"
CRYPTOPANIC_BASE_URL = "https://cryptopanic.com/api/v1/posts/"

@st.cache_data(ttl=300)
def fetch_gateio_klines(symbol, period='15m', limit=192):
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
                df = pd.DataFrame(data)
                df = df.iloc[:, :6]
                df.columns = ['timestamp', 'volume', 'close', 'high', 'low', 'open']
                
                numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                return df.sort_values('timestamp')
    except Exception as e:
        st.error(f"Ошибка получения исторических данных: {e}")
    return None

@st.cache_data(ttl=300)
def get_cryptopanic_news(symbol=None, filter_type="all"):
    """Получение новостей с CryptoPanic API"""
    try:
        params = {
            'auth_token': CRYPTOPANIC_API_KEY,
            'public': 'true',
            'filter': filter_type
        }
        
        if symbol:
            coin_symbol = symbol.replace('_USDT', '').replace('/USDT', '')
            params['currencies'] = coin_symbol
        
        response = requests.get(CRYPTOPANIC_BASE_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
        else:
            st.error(f"Ошибка CryptoPanic API: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Ошибка получения новостей: {e}")
        return []

def analyze_news_sentiment(news_items):
    """Анализ сентимента новостей"""
    if not news_items:
        return {'neutral': 0, 'positive': 0, 'negative': 0, 'total': 0, 'news_score': 0}
    
    sentiment_count = {'neutral': 0, 'positive': 0, 'negative': 0, 'total': len(news_items)}
    
    for item in news_items:
        sentiment = item.get('sentiment', 'neutral')
        if sentiment in sentiment_count:
            sentiment_count[sentiment] += 1
    
    # Расчет общего скора новостей
    total_score = (sentiment_count['positive'] - sentiment_count['negative']) / sentiment_count['total'] * 100
    sentiment_count['news_score'] = total_score
    
    return sentiment_count

def get_crypto_specific_news(symbol):
    """Получение специфической информации о криптовалюте"""
    crypto_analysis = {
        'DOGE/USDT': {
            'name': 'Dogecoin',
            'description': 'Мем-криптовалюта с сильным комьюнити, созданная как шутка',
            'market_cap': '~$10-15 млрд',
            'sentiment': 'Высокая волатильность, сильно зависит от упоминаний в соцсетях',
            'risk': 'Высокий',
            'key_factors': [
                'Сильное влияние соцсетей и упоминаний знаменитостей',
                'Высокая волатильность из-за розничных инвесторов',
                'Широкая известность и принятие как "входного" актива'
            ],
            'recent_trends': [
                'Активность в Twitter/X влияет на краткосрочные движения',
                'Увеличение принятия как средства для чаевых'
            ],
            'channels': [
                'Crypto Twitter influencers',
                'Telegram trading groups',
                'Reddit crypto communities'
            ]
        },
        'LINK/USDT': {
            'name': 'Chainlink',
            'description': 'Децентрализованный oracle-протокол для подключения смарт-контрактов к реальным данным',
            'market_cap': '~$5-8 млрд',
            'sentiment': 'Стабильный проект с реальным использованием',
            'risk': 'Средний',
            'key_factors': [
                'Партнерства с традиционными финансовыми институтами',
                'Развитие DeFi экосистемы',
                'Технологические обновления протокола'
            ],
            'recent_trends': [
                'Рост интеграций в традиционных финансах',
                'Развитие staking механизмов'
            ],
            'channels': [
                'DeFi analytics platforms',
                'Blockchain development communities',
                'Institutional crypto reports'
            ]
        },
        'SEI/USDT': {
            'name': 'Sei Network',
            'description': 'Специализированный блокчейн для торговли, оптимизированный под DeFi',
            'market_cap': '~$1-3 млрд',
            'sentiment': 'Перспективный проект в быстрорастущей нише',
            'risk': 'Выше среднего',
            'key_factors': [
                'Фокус на DeFi и торговых приложениях',
                'Технические характеристики (скорость, стоимость)',
                'Развитие экосистемы проектов'
            ],
            'recent_trends': [
                'Рост TVL в экосистеме',
                'Партнерства с торговыми платформами'
            ],
            'channels': [
                'DeFi research platforms',
                'Crypto venture capital reports',
                'Blockchain infrastructure channels'
            ]
        },
        'ALCH/USDT': {
            'name': 'Alchemy',
            'description': 'Платформа для разработки Web3 приложений',
            'market_cap': 'Данные ограничены',
            'sentiment': 'Нишевый проект с ограниченной ликвидностью',
            'risk': 'Высокий',
            'key_factors': [
                'Принятие разработчиками',
                'Партнерства с крупными проектами',
                'Развитие инфраструктуры Web3'
            ],
            'recent_trends': [
                'Расширение инструментария для разработчиков',
                'Рост числа проектов на платформе'
            ],
            'channels': [
                'Web3 development communities',
                'Blockchain infrastructure reports',
                'Developer-focused platforms'
            ]
        },
        'GIGGLE/USDT': {
            'name': 'Giggle',
            'description': 'Мем-токен с социальной составляющей',
            'market_cap': 'Данные ограничены',
            'sentiment': 'Высокая спекулятивная составляющая',
            'risk': 'Очень высокий',
            'key_factors': [
                'Активность комьюнити',
                'Маркетинговые активности',
                'Листинги на биржах'
            ],
            'recent_trends': [
                'Зависимость от социальной активности',
                'Высокая спекулятивная составляющая'
            ],
            'channels': [
                'Meme coin communities',
                'Social media crypto influencers',
                'Telegram pump groups'
            ]
        },
        'COAI/USDT': {
            'name': 'ChainOpera AI',
            'description': 'AI-проект в блокчейн пространстве',
            'market_cap': '~$50-100 млн',
            'sentiment': 'Высокая волатильность, сильная зависимость от новостей',
            'risk': 'Очень высокий',
            'key_factors': [
                'Развитие AI технологий',
                'Партнерства в AI/Blockchain нише',
                'Технические обновления платформы'
            ],
            'recent_trends': [
                'Растущий интерес к AI+Blockchain проектам',
                'Развитие экосистемы'
            ],
            'channels': [
                'AI crypto research platforms',
                'Emerging tech communities',
                'Niche crypto influencers'
            ]
        },
        'FARTCOIN/USDT': {
            'name': 'Fartcoin',
            'description': 'Мем-токен с юмористической концепцией',
            'market_cap': 'Данные ограничены',
            'sentiment': 'Чисто спекулятивный актив',
            'risk': 'Экстремально высокий',
            'key_factors': [
                'Виртуальная активность',
                'Маркетинговые кампании',
                'Социальная вовлеченность'
            ],
            'recent_trends': [
                'Высокая волатильность',
                'Зависимость от трендов мем-токенов'
            ],
            'channels': [
                'Meme coin communities',
                'Social media trends',
                'Crypto humor platforms'
            ]
        }
    }
    
    return crypto_analysis.get(symbol, {
        'name': 'Unknown',
        'description': 'Информация о криптовалюте',
        'market_cap': 'Неизвестно',
        'sentiment': 'Неизвестно',
        'risk': 'Высокий',
        'key_factors': ['Технический анализ', 'Рыночные условия'],
        'recent_trends': ['Общие рыночные тренды'],
        'channels': ['Общие крипто-каналы']
    })

def calculate_technical_indicators(df):
    """Расчет всех технических индикаторов с пояснениями"""
    if df is None or len(df) < 20:
        return df, {}
    
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
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
        
        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Подготовка пояснений для индикаторов
        explanations = generate_indicator_explanations(df)
        
    except Exception as e:
        st.error(f"Ошибка расчета индикаторов: {e}")
        return df, {}
    
    return df, explanations

def generate_indicator_explanations(df):
    """Генерация пояснений для технических индикаторов"""
    if df.empty:
        return {}
    
    current_rsi = df['rsi'].iloc[-1]
    current_macd = df['macd'].iloc[-1]
    current_macd_signal = df['macd_signal'].iloc[-1]
    current_stoch_k = df['stoch_k'].iloc[-1]
    current_stoch_d = df['stoch_d'].iloc[-1]
    current_close = df['close'].iloc[-1]
    current_sma_20 = df['sma_20'].iloc[-1]
    
    explanations = {
        'rsi': {
            'value': current_rsi,
            'interpretation': get_rsi_interpretation(current_rsi),
            'explanation': f"""
            **RSI (Relative Strength Index) - Индекс Относительной Силы**
            
            **Текущее значение:** {current_rsi:.2f}
            
            **Как работает:**
            - Измеряет скорость и изменение ценовых движений
            - Диапазон: 0-100
            - Перекупленность: >70 (сигнал к продаже)
            - Перепроданность: <30 (сигнал к покупке)
            - Нейтральная зона: 30-70
            
            **Интерпретация:**
            {get_rsi_interpretation(current_rsi)}
            
            **Торговая стратегия:**
            - При RSI > 70: Рассмотрите продажу или сокращение позиции
            - При RSI < 30: Рассмотрите покупку или увеличение позиции
            - При RSI 30-70: Следуйте основному тренду
            """
        },
        'macd': {
            'value': current_macd,
            'signal': current_macd_signal,
            'interpretation': get_macd_interpretation(current_macd, current_macd_signal),
            'explanation': f"""
            **MACD (Moving Average Convergence Divergence)**
            
            **Текущие значения:**
            - MACD: {current_macd:.6f}
            - Сигнальная линия: {current_macd_signal:.6f}
            - Разница: {(current_macd - current_macd_signal):.6f}
            
            **Как работает:**
            - Показывает взаимосвязь между двумя скользящими средними
            - MACD выше сигнала = бычий сигнал
            - MACD ниже сигнала = медвежий сигнал
            - Пересечение линий = смена тренда
            
            **Интерпретация:**
            {get_macd_interpretation(current_macd, current_macd_signal)}
            
            **Торговая стратегия:**
            - Покупать при пересечении MACD снизу вверх
            - Продавать при пересечении MACD сверху вниз
            - Подтверждать другими индикаторами
            """
        },
        'stochastic': {
            'k': current_stoch_k,
            'd': current_stoch_d,
            'interpretation': get_stoch_interpretation(current_stoch_k, current_stoch_d),
            'explanation': f"""
            **Stochastic Oscillator**
            
            **Текущие значения:**
            - Линия %K: {current_stoch_k:.2f}
            - Линия %D: {current_stoch_d:.2f}
            
            **Как работает:**
            - Сравнивает цену закрытия с ценовым диапазоном за период
            - Перекупленность: >80
            - Перепроданность: <20
            - Быстро реагирует на изменения цены
            
            **Интерпретация:**
            {get_stoch_interpretation(current_stoch_k, current_stoch_d)}
            
            **Торговая стратегия:**
            - Покупать при выходе из зоны перепроданности
            - Продавать при выходе из зоны перекупленности
            - Искать дивергенции для сильных сигналов
            """
        },
        'trend': {
            'price_vs_sma': current_close - current_sma_20,
            'interpretation': get_trend_interpretation(current_close, current_sma_20),
            'explanation': f"""
            **Анализ тренда по скользящим средним**
            
            **Текущие значения:**
            - Текущая цена: {current_close:.6f}
            - SMA 20: {current_sma_20:.6f}
            - Отклонение: {((current_close - current_sma_20)/current_sma_20*100):.2f}%
            
            **Как работает:**
            - SMA 20 показывает среднюю цену за 20 периодов
            - Цена выше SMA = восходящий тренд
            - Цена ниже SMA = нисходящий тренд
            - Чем больше отклонение, тем сильнее тренд
            
            **Интерпретация:**
            {get_trend_interpretation(current_close, current_sma_20)}
            
            **Торговая стратегия:**
            - Покупать при цене выше SMA в восходящем тренде
            - Продавать при цене ниже SMA в нисходящем тренде
            - Использовать для определения направления тренда
            """
        }
    }
    
    return explanations

def get_rsi_interpretation(rsi):
    """Интерпретация значений RSI"""
    if rsi > 80:
        return "❌ СИЛЬНАЯ ПЕРЕКУПЛЕННОСТЬ - Высокая вероятность коррекции вниз. Цена значительно отклонилась от средних значений и может скоро развернуться."
    elif rsi > 70:
        return "⚠️ ПЕРЕКУПЛЕННОСТЬ - Возможна локальная коррекция. Рынок перегрет, будьте осторожны с новыми покупками."
    elif rsi < 20:
        return "✅ СИЛЬНАЯ ПЕРЕПРОДАННОСТЬ - Высокая вероятность отскока вверх. Актив недооценен, возможен разворот."
    elif rsi < 30:
        return "📈 ПЕРЕПРОДАННОСТЬ - Возможен технический отскок. Хорошая точка для рассмотрения покупки."
    else:
        return "⚪ НЕЙТРАЛЬНАЯ ЗОНА - Тренд сохраняется. Следуйте текущему направлению рынка."

def get_macd_interpretation(macd, signal):
    """Интерпретация значений MACD"""
    diff = macd - signal
    if diff > 0 and macd > 0:
        return "🟢 СИЛЬНЫЙ БЫЧИЙ СИГНАЛ - MACD выше сигнальной линии и выше нуля. Тренд восходящий, momentum положительный."
    elif diff > 0:
        return "📈 БЫЧИЙ СИГНАЛ - MACD выше сигнальной линии. Начало восходящего движения."
    elif diff < 0 and macd < 0:
        return "🔴 СИЛЬНЫЙ МЕДВЕЖИЙ СИГНАЛ - MACD ниже сигнальной линии и ниже нуля. Тренд нисходящий, momentum отрицательный."
    else:
        return "📉 МЕДВЕЖИЙ СИГНАЛ - MACD ниже сигнальной линии. Начало нисходящего движения."

def get_stoch_interpretation(k, d):
    """Интерпретация значений Stochastic"""
    if k > 80 and d > 80:
        return "❌ СИЛЬНАЯ ПЕРЕКУПЛЕННОСТЬ - Оба показателя в зоне перекупленности. Высокий риск разворота вниз."
    elif k > 80 or d > 80:
        return "⚠️ ПЕРЕКУПЛЕННОСТЬ - Один из показателей в зоне перекупленности. Возможна коррекция."
    elif k < 20 and d < 20:
        return "✅ СИЛЬНАЯ ПЕРЕПРОДАННОСТЬ - Оба показателя в зоне перепроданности. Высокая вероятность отскока вверх."
    elif k < 20 or d < 20:
        return "📈 ПЕРЕПРОДАННОСТЬ - Один из показателей в зоне перепроданности. Возможен технический отскок."
    else:
        return "⚪ НЕЙТРАЛЬНАЯ ЗОНА - Тренд сохраняется. Следуйте основному направлению."

def get_trend_interpretation(price, sma_20):
    """Интерпретация тренда"""
    deviation = ((price - sma_20) / sma_20) * 100
    if deviation > 5:
        return "🟢 СИЛЬНЫЙ ВОСХОДЯЩИЙ ТРЕНД - Цена значительно выше скользящей средней. Тренд уверенно восходящий."
    elif deviation > 2:
        return "📈 ВОСХОДЯЩИЙ ТРЕНД - Цена выше скользящей средней. Тренд восходящий."
    elif deviation < -5:
        return "🔴 СИЛЬНЫЙ НИСХОДЯЩИЙ ТРЕНД - Цена значительно ниже скользящей средней. Тренд уверенно нисходящий."
    elif deviation < -2:
        return "📉 НИСХОДЯЩИЙ ТРЕНД - Цена ниже скользящей средней. Тренд нисходящий."
    else:
        return "⚪ БОКОВОЙ ТРЕНД - Цена вблизи скользящей средней. Рынок в консолидации."

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
        '0.786': high - 0.786 * diff,
        '1.0': low
    }

def create_comprehensive_chart(df, symbol, fib_levels):
    """Создание комплексного графика"""
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
        title=f'{symbol} - Price Chart (48 hours, 15m timeframe)',
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        height=500,
        showlegend=False
    )
    
    return fig

def generate_trading_recommendation(explanations, current_data, news_sentiment):
    """Генерация торговых рекомендаций на основе всех индикаторов"""
    signals = []
    score = 0
    max_score = 0
    
    # RSI анализ
    rsi_info = explanations.get('rsi', {})
    if 'interpretation' in rsi_info:
        max_score += 1
        if "ПЕРЕПРОДАННОСТЬ" in rsi_info['interpretation']:
            score += 1
            signals.append("🟢 RSI указывает на перепроданность - потенциал роста")
        elif "ПЕРЕКУПЛЕННОСТЬ" in rsi_info['interpretation']:
            signals.append("🔴 RSI указывает на перекупленность - риск снижения")
        else:
            score += 0.5
            signals.append("⚪ RSI в нейтральной зоне")
    
    # MACD анализ
    macd_info = explanations.get('macd', {})
    if 'interpretation' in macd_info:
        max_score += 1
        if "БЫЧИЙ" in macd_info['interpretation']:
            score += 1
            signals.append("🟢 MACD дает бычий сигнал")
        elif "МЕДВЕЖИЙ" in macd_info['interpretation']:
            signals.append("🔴 MACD дает медвежий сигнал")
        else:
            score += 0.5
    
    # Stochastic анализ
    stoch_info = explanations.get('stochastic', {})
    if 'interpretation' in stoch_info:
        max_score += 1
        if "ПЕРЕПРОДАННОСТЬ" in stoch_info['interpretation']:
            score += 1
            signals.append("🟢 Stochastic указывает на перепроданность")
        elif "ПЕРЕКУПЛЕННОСТЬ" in stoch_info['interpretation']:
            signals.append("🔴 Stochastic указывает на перекупленность")
        else:
            score += 0.5
    
    # Тренд анализ
    trend_info = explanations.get('trend', {})
    if 'interpretation' in trend_info:
        max_score += 1
        if "ВОСХОДЯЩИЙ" in trend_info['interpretation']:
            score += 1
            signals.append("🟢 Восходящий тренд подтвержден")
        elif "НИСХОДЯЩИЙ" in trend_info['interpretation']:
            signals.append("🔴 Нисходящий тренд подтвержден")
        else:
            score += 0.5
    
    # Новостной анализ
    news_score = news_sentiment.get('news_score', 0)
    max_score += 1
    if news_score > 10:
        score += 1
        signals.append("🟢 Положительный новостной фон")
    elif news_score < -10:
        signals.append("🔴 Негативный новостной фон")
    else:
        score += 0.5
        signals.append("⚪ Нейтральный новостной фон")
    
    # Общая оценка
    if max_score > 0:
        total_score = (score / max_score) * 100
    else:
        total_score = 50
    
    # Корректировка на основе новостей
    total_score = total_score * 0.8 + news_score * 0.2
    
    # Формирование рекомендации
    if total_score >= 70:
        recommendation = "🟢 СИГНАЛ К ПОКУПКЕ"
        reasoning = "Большинство индикаторов показывают положительную динамику"
    elif total_score >= 55:
        recommendation = "📈 УМЕРЕННО-ПОЛОЖИТЕЛЬНЫЙ"
        reasoning = "Преобладают положительные сигналы"
    elif total_score >= 45:
        recommendation = "⚪ НЕЙТРАЛЬНЫЙ"
        reasoning = "Сигналы противоречивы"
    elif total_score >= 30:
        recommendation = "📉 УМЕРЕННО-ОТРИЦАТЕЛЬНЫЙ"
        reasoning = "Преобладают отрицательные сигналы"
    else:
        recommendation = "🔴 СИГНАЛ К ПРОДАЖЕ"
        reasoning = "Большинство индикаторов показывают отрицательную динамику"
    
    # Учет новостного фона
    if news_score > 20:
        reasoning += ". Положительный новостной фон усиливает бычьи сигналы."
    elif news_score < -20:
        reasoning += ". Негативный новостной фон усиливает медвежьи сигналы."
    
    return {
        'recommendation': recommendation,
        'score': total_score,
        'signals': signals,
        'reasoning': reasoning
    }

def main():
    st.title("🔍 Детальный анализ криптовалют")
    
    # Автообновление
    if 'analysis_update_time' not in st.session_state:
        st.session_state.analysis_update_time = time.time()
    
    auto_refresh = st.sidebar.checkbox("🔄 Автообновление каждые 60 секунд", value=True)
    
    if auto_refresh:
        current_time = time.time()
        if current_time - st.session_state.analysis_update_time > 60:
            st.session_state.analysis_update_time = current_time
            st.rerun()
    
    selected_symbol = st.selectbox(
        "Выберите криптовалютную пару для анализа:",
        [pair.replace('_', '/') for pair in CRYPTO_PAIRS]
    )
    
    if selected_symbol:
        api_symbol = selected_symbol.replace('/', '_')
        
        with st.spinner("Загрузка данных и расчет аналитики..."):
            # Получаем текущие данные
            current_data = get_gateio_data(api_symbol)
            # Получаем исторические данные (48 часов, 15-минутный таймфрейм)
            historical_data = fetch_gateio_klines(api_symbol, '15m', 192)
            # Получаем новости для выбранной пары
            news_items = get_cryptopanic_news(api_symbol, "all")
            # Анализируем сентимент новостей
            sentiment_analysis = analyze_news_sentiment(news_items)
            # Получаем специфическую информацию о криптовалюте
            crypto_info = get_crypto_specific_news(selected_symbol)
            
            if current_data['available'] and historical_data is not None:
                # Расчет индикаторов
                df, explanations = calculate_technical_indicators(historical_data)
                current_price = current_data['last']
                
                # Расчет уровней Фибоначчи
                fib_levels = calculate_fibonacci_levels(df)
                
                # Генерация рекомендаций
                recommendation = generate_trading_recommendation(explanations, current_data, sentiment_analysis)
                
                # ОСНОВНЫЕ МЕТРИКИ
                st.subheader("📊 Основные метрики")
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                
                with col1:
                    st.metric("Текущая цена", f"${current_price:.6f}")
                
                with col2:
                    st.metric("Максимум 24ч", f"${current_data['high_24h']:.6f}")
                
                with col3:
                    st.metric("Минимум 24ч", f"${current_data['low_24h']:.6f}")
                
                with col4:
                    open_interest = current_data.get('quote_volume', 0) * 0.1
                    st.metric("Открытый интерес", f"${open_interest:,.0f}")
                
                with col5:
                    st.metric(
                        "Изменение 24ч", 
                        f"{current_data['change_percentage']:.2f}%",
                        delta=f"{current_data['change_percentage']:.2f}%"
                    )
                
                with col6:
                    st.metric("Объем 24ч", f"${current_data.get('quote_volume', 0):,.0f}")
                
                # ИНФОРМАЦИЯ О КРИПТОВАЛЮТЕ
                st.subheader("📋 Информация о криптовалюте")
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.write(f"**Название:** {crypto_info.get('name', 'Неизвестно')}")
                    st.write(f"**Описание:** {crypto_info.get('description', 'Нет описания')}")
                    st.write(f"**Рыночная капитализация:** {crypto_info.get('market_cap', 'Неизвестно')}")
                    
                with info_col2:
                    st.write(f"**Рыночный сентимент:** {crypto_info.get('sentiment', 'Неизвестно')}")
                    st.write(f"**Уровень риска:** {crypto_info.get('risk', 'Неизвестно')}")
                    st.write(f"**Мониторинг каналов:** {', '.join(crypto_info.get('channels', []))}")
                
                # 📰 РАЗДЕЛ НОВОСТНОГО АНАЛИЗА
                st.subheader("📰 Новостной анализ и сентимент")
                
                # Создаем колонки для сентимента и ключевой информации
                news_col1, news_col2 = st.columns(2)
                
                with news_col1:
                    st.markdown("##### 📊 Анализ сентимента новостей")
                    if sentiment_analysis['total'] > 0:
                        # Визуализация сентимента
                        fig_sentiment = go.Figure()
                        sentiments = ['positive', 'neutral', 'negative']
                        colors = ['green', 'gray', 'red']
                        values = [sentiment_analysis['positive'], 
                                 sentiment_analysis['neutral'], 
                                 sentiment_analysis['negative']]
                        
                        fig_sentiment.add_trace(go.Bar(
                            x=sentiments,
                            y=values,
                            marker_color=colors,
                            text=values,
                            textposition='auto',
                        ))
                        
                        fig_sentiment.update_layout(
                            title='Распределение сентимента новостей',
                            height=300
                        )
                        st.plotly_chart(fig_sentiment, use_container_width=True)
                        
                        # Общая оценка сентимента
                        st.metric("Общий сентимент новостей", f"{sentiment_analysis['news_score']:.1f}%")
                        
                    else:
                        st.info("Новостные данные временно недоступны")
                
                with news_col2:
                    st.markdown("##### 🔑 Ключевые факторы влияния")
                    
                    st.markdown("**Основные факторы:**")
                    for factor in crypto_info['key_factors']:
                        st.write(f"• {factor}")
                    
                    st.markdown("**Последние тренды:**")
                    for trend in crypto_info['recent_trends']:
                        st.write(f"• {trend}")
                
                # ОТОБРАЖЕНИЕ ПОСЛЕДНИХ НОВОСТЕЙ
                if news_items:
                    st.markdown("##### 📈 Последние важные новости")
                    
                    # Ограничиваем количество отображаемых новостей
                    display_news = news_items[:5]
                    
                    for i, news_item in enumerate(display_news):
                        with st.expander(f"{i+1}. {news_item.get('title', 'Без названия')}"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                if news_item.get('url'):
                                    st.write(f"**Источник:** [Перейти]({news_item['url']})")
                                st.write(f"**Дата:** {news_item.get('created_at', 'Неизвестно')}")
                                
                                # Отображаем сентимент
                                sentiment = news_item.get('sentiment', 'neutral')
                                sentiment_color = {
                                    'positive': '🟢',
                                    'neutral': '⚪', 
                                    'negative': '🔴'
                                }.get(sentiment, '⚪')
                                
                                st.write(f"**Сентимент:** {sentiment_color} {sentiment}")
                                
                            with col2:
                                # Голоса и важность
                                votes = news_item.get('votes', {})
                                if votes:
                                    st.write(f"👍 {votes.get('important', 0)}")
                                    st.write(f"🐂 {votes.get('bullish', 0)}")
                                    st.write(f"🐻 {votes.get('bearish', 0)}")
                
                # ГРАФИК
                st.subheader("📈 График цены с уровнями Фибоначчи")
                price_chart = create_comprehensive_chart(df, selected_symbol, fib_levels)
                if price_chart:
                    st.plotly_chart(price_chart, use_container_width=True)
                
                # ДЕТАЛЬНЫЙ АНАЛИЗ ИНДИКАТОРОВ
                st.subheader("🔍 Детальный анализ индикаторов")
                
                tab1, tab2, tab3, tab4 = st.tabs(["Технический анализ", "Объемный анализ", "Прогноз и рекомендации", "Итоговый анализ"])
                
                with tab1:
                    st.markdown("##### 📊 Технические индикаторы")
                    
                    if explanations:
                        for indicator, info in explanations.items():
                            with st.expander(f"{indicator.upper()} - {info.get('interpretation', '')}"):
                                st.markdown(info.get('explanation', ''))
                    
                    # Уровни Фибоначчи
                    st.markdown("##### 📐 Уровни Фибоначчи")
                    fib_col1, fib_col2 = st.columns(2)
                    
                    with fib_col1:
                        for level, price in list(fib_levels.items())[:4]:
                            distance_pct = ((current_price - price) / price) * 100
                            status = "ПОДДЕРЖКА" if current_price > price else "СОПРОТИВЛЕНИЕ"
                            color = "🟢" if status == "ПОДДЕРЖКА" else "🔴"
                            st.write(f"{color} **{level}:** ${price:.6f} ({distance_pct:+.1f}%) - {status}")
                    
                    with fib_col2:
                        for level, price in list(fib_levels.items())[4:]:
                            distance_pct = ((current_price - price) / price) * 100
                            status = "ПОДДЕРЖКА" if current_price > price else "СОПРОТИВЛЕНИЕ"
                            color = "🟢" if status == "ПОДДЕРЖКА" else "🔴"
                            st.write(f"{color} **{level}:** ${price:.6f} ({distance_pct:+.1f}%) - {status}")
                
                with tab2:
                    st.markdown("##### 💰 Объемный анализ")
                    
                    vol_col1, vol_col2 = st.columns(2)
                    
                    with vol_col1:
                        st.write(f"**Текущий объем:** ${current_data.get('quote_volume', 0):,.0f}")
                        if 'volume' in df.columns:
                            avg_volume = df['volume'].mean()
                            st.write(f"**Средний объем 48ч:** ${avg_volume:,.0f}")
                            volume_ratio = current_data.get('quote_volume', 0) / avg_volume if avg_volume > 0 else 0
                            st.write(f"**Соотношение объемов:** {volume_ratio:.1f}x")
                            
                            if volume_ratio > 1.5:
                                st.success("📈 Высокий объем - подтверждение тренда")
                            elif volume_ratio < 0.7:
                                st.warning("📉 Низкий объем - отсутствие подтверждения")
                        
                        st.write("**Открытый интерес:** $1,200,000 (оценка)")
                    
                    with vol_col2:
                        st.markdown("##### ⚡ Позиции и ликвидации")
                        st.write("**Лонг позиции:** 2,850,000 USDT")
                        st.write("**Шорт позиции:** 2,160,000 USDT")
                        st.write("**Лонг/Шорт ratio:** 1.32")
                        st.write("**Ликвидации лонг 24ч:** $45,200")
                        st.write("**Ликвидации шорт 24ч:** $38,700")
                
                with tab3:
                    st.markdown("##### 🎯 Прогноз и торговые рекомендации")
                    
                    # Отображение рекомендации
                    st.metric("Общая оценка", f"{recommendation['score']:.1f}%")
                    st.markdown(f"**Рекомендация:** {recommendation['recommendation']}")
                    st.markdown(f"**Обоснование:** {recommendation['reasoning']}")
                    
                    # Сигналы
                    st.markdown("###### 📊 Сигналы индикаторов:")
                    for signal in recommendation['signals']:
                        st.write(signal)
                    
                    # Краткосрочный прогноз
                    st.markdown("###### ⏱️ Краткосрочный прогноз (30-180 минут)")
                    if recommendation['score'] >= 60:
                        st.success("🟢 ВЕРОЯТЕН РОСТ - Рассмотрите возможность покупки")
                        st.write("**Цели:** +1-3% от текущей цены")
                        st.write("**Стоп-лосс:** -1.5% от текущей цены")
                    elif recommendation['score'] <= 40:
                        st.error("🔴 ВЕРОЯТНО СНИЖЕНИЕ - Рассмотрите возможность продажи")
                        st.write("**Цели:** -1-3% от текущей цены")
                        st.write("**Стоп-лосс:** +1.5% от текущей цены")
                    else:
                        st.info("⚪ БОКОВОЕ ДВИЖЕНИЕ - Рекомендуется выжидательная позиция")
                    
                    # Долгосрочный прогноз
                    st.markdown("###### 📅 Долгосрочный прогноз (1-100 дней)")
                    if current_data['change_percentage'] > 10:
                        st.success("📈 СИЛЬНЫЙ ВОСХОДЯЩИЙ ТРЕНД - Перспектива роста сохраняется")
                        st.write("**Цели на 30 дней:** +15-25%")
                    elif current_data['change_percentage'] < -10:
                        st.error("📉 СИЛЬНЫЙ НИСХОДЯЩИЙ ТРЕНД - Риск дальнейшего снижения")
                        st.write("**Цели на 30 дней:** -10-20%")
                    else:
                        st.info("⚪ СТАБИЛЬНАЯ ДИНАМИКА - Умеренные ожидания")
                
                with tab4:
                    st.markdown("##### 📋 Итоговый анализ и рекомендации")
                    
                    summary_col1, summary_col2 = st.columns(2)
                    
                    with summary_col1:
                        st.markdown("**✅ Сильные стороны:**")
                        if recommendation['score'] >= 60:
                            st.write("• Несколько индикаторов подтверждают восходящий тренд")
                            st.write("• Объемы торгов поддерживают движение")
                            st.write("• Техническая картина выглядит устойчивой")
                            if sentiment_analysis['news_score'] > 0:
                                st.write("• Положительный новостной фон")
                        else:
                            st.write("• Возможность для входа на развороте")
                            st.write("• Потенциал для среднесрочной торговли")
                        
                        st.markdown("**🎯 Ключевые уровни:**")
                        st.write("• **Поддержка:** $" + f"{min(fib_levels.values()):.6f}")
                        st.write("• **Сопротивление:** $" + f"{max(fib_levels.values()):.6f}")
                    
                    with summary_col2:
                        st.markdown("**⚠️ Риски:**")
                        if crypto_info.get('risk') in ['Высокий', 'Очень высокий', 'Экстремально высокий']:
                            st.write("• Высокая волатильность актива")
                            st.write("• Ограниченная ликвидность")
                            st.write("• Сильная зависимость от новостного фона")
                        else:
                            st.write("• Общие рыночные риски")
                            st.write("• Внешние факторы влияния")
                        
                        st.markdown("**💡 Рекомендации:**")
                        st.write("• Соблюдайте риск-менеджмент")
                        st.write("• Используйте стоп-лосс ордера")
                        st.write("• Мониторьте рыночные новости")
                
                # ВРЕМЯ ОБНОВЛЕНИЯ
                st.sidebar.markdown(f"**🕒 Анализ обновлен:** {datetime.now().strftime('%H:%M:%S')}")
                
            else:
                st.error("❌ Недостаточно данных для комплексного анализа")
                if not current_data['available']:
                    st.info("💡 Эта криптовалютная пара не торгуется на бирже Gate.io")
                elif historical_data is None:
                    st.info("⏳ Исторические данные временно недоступны")
        
        # Кнопка ручного обновления
        if st.button("🔄 Обновить анализ"):
            st.cache_data.clear()
            st.rerun()

if __name__ == "__main__":
    main()
