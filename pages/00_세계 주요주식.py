import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="글로벌 TOP 10 주가 분석",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 세계 주요 주식 TOP 10 최근 1년 분석 대시보드")
st.markdown("글로벌 시장을 리드하는 주요 기업 10개의 최근 1년 주가 변동 및 누적 수익률을 비교합니다.")

# 2. 세계 주요 주식 TOP 10 티커 설정
tickers = {
    "마이크로소프트 (MSFT)": "MSFT",
    "애플 (AAPL)": "AAPL",
    "엔비디아 (NVDA)": "NVDA",
    "구글 (GOOGL)": "GOOGL",
    "아마존 (AMZN)": "AMZN",
    "메타 (META)": "META",
    "테슬라 (TSLA)": "TSLA",
    "버크셔 해서웨이 (BRK-B)": "BRK-B",
    "삼성전자 (005930)": "005930.KS",
    "SK하이닉스 (000660)": "000660.KS"
}

end_date = datetime.today()
start_date = end_date - timedelta(days=365)

# 3. 데이터 로드 및 캐싱 (속도 최적화)
@st.cache_data(ttl=3600)
def load_stock_data():
    combined_df = pd.DataFrame()
    for name, ticker in tickers.items():
        df = yf.download(ticker, start=start_date, end=end_date)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                combined_df[name] = df['Close'][ticker]
            else:
                combined_df[name] = df['Close']
                
    # 국가별 휴장일 시차로 인한 결측치는 직전 데이터로 채움
    combined_df = combined_df.ffill().bfill()
    return combined_df

with St.spinner("야후 파이낸스에서 글로벌 데이터를 가져오는 중입니다..."):
    try:
        price_data = load_stock_data()
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        st.stop()

# --- 사이드바 제어 설정 ---
st.sidebar.header("🔍 대시보드 옵션")
# 기본적으로 모든 종목이 선택되어 있도록 설정
selected_tickers = st.sidebar.multiselect(
    "비교할 종목을 선택하세요 (다중 선택 가능):",
    list(tickers.keys()),
    default=list(tickers.keys())
)

if not selected_tickers:
    st.warning("⚠️ 최소 하나의 종목을 선택해야 그래프가 표시됩니다.")
    st.stop()

# 4. 레이아웃 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 누적 수익률 비교", "💵 종목별 상세 주가", "📋 데이터 통계 및 요약"])

# --- Tab 1: 누적 수익률 비교 (Plotly) ---
with tab1:
    st.subheader("최근 1년 누적 수익률 (%) 비교")
    st.caption("※ 1년 전 첫 거래일 주가를 0%로 맞추어 어떤 종목이 가장 높은 성과를 내었는지 한눈에 비교합니다.")
    
    # 선택된 종목들만 필터링하여 수익률 계산
    filtered_prices = price_data[selected_tickers]
    normalized_data = (filtered_prices / filtered_prices.iloc[0] - 1) * 100
    
    fig1 = go.Figure()
    for col in normalized_data.columns:
        fig1.add_trace(go.Scatter(
            x=normalized_data.index, 
            y=normalized_data[col], 
            mode='lines', 
            name=col,
            hovertemplate='%{sidebar}: <b>%{y:.2f}%</b><extra></extra>'
        ))
        
    fig1.update_layout(
        hovermode="x unified",
        xaxis_title="날짜",
        yaxis_title="누적 수익률 (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        height=600
    )
    st.plotly_chart(fig1, use_container_width=True)

# --- Tab 2: 개별 주가 추이 (Plotly) ---
with tab2:
    st.subheader("종목별 절대 주가 추이")
    # 상세 조회는 단일 종목 선택
    detail_stock = st.selectbox("상세 조회할 종목을 선택하세요:", list(tickers.keys()))
    
    currency = "KRW (원)" if "005930" in detail_stock or "000660" in detail_stock else "USD ($)"
    
    col_chart, col_stat = st.columns([3, 1])
    
    with col_chart:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=price_data.index,
            y=price_data[detail_stock],
            mode='lines',
            name=detail_stock,
            line=dict(color='#2ca02c', width=2.5),
            hovertemplate='날짜: %{x}<br>주가: <b>%{y:,.2f}</b><extra></extra>'
        ))
        fig2.update_layout(
            title=f"{detail_stock} 최근 1년 주가 흐름 ({currency})",
            xaxis_title="날짜",
            yaxis_title=f"주가 ({currency})",
            margin=dict(l=20, r=20, t=40, b=20),
            height=450
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    with col_stat:
        st.markdown("<br><br>", unsafe_allow_html=True)
        current_p = price_data[detail_stock].iloc[-1]
        highest_p = price_data[detail_stock].max()
        lowest_p = price_data[detail_stock].min()
        
        # 전체 데이터 기준 해당 종목의 최종 수익률 계산
        single_norm = (price_data[detail_stock] / price_data[detail_stock].iloc[0] - 1) * 100
        total_return = single_norm.iloc[-1]
        
        fmt = ",.0f" if "KRW" in currency else ",.2f"
        sign = "₩" if "KRW" in currency else "$"
        
        st.metric(label="현재가", value=f"{sign}{current_p:{fmt}}", delta=f"{total_return:+.2f}% (1년)")
        st.metric(label="52주 최고가", value=f"{sign}{highest_p:{fmt}}")
        st.metric(label="52주 최저가", value=f"{sign}{lowest_p:{fmt}}")

# --- Tab 3: 데이터 통계치 요약 ---
with tab3:
    st.subheader("선택한 종목들의 최근 1년 주요 통계치")
    desc = price_data[selected_tickers].describe().T[['max', 'min', 'mean', '50%']]
    desc.columns = ['최고가', '최저가', '평균가', '중앙값']
    st.dataframe(desc.style.format("{:,.2f}"))
    
    st.subheader("전체 주가 데이터 원본 (최신순)")
    st.dataframe(price_data[selected_tickers].sort_index(ascending=False))
