"""
동네 엑스레이 + 디지털 트윈 — 앱 진입점
st.navigation API로 페이지 네비게이션 관리
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(
    page_title="동네 엑스레이",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 사이드바 브랜딩 ──
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 8px 0 4px;">
            <div style="font-size:28px;">🏙️</div>
            <div style="
                font-size:18px;
                font-weight:800;
                background: linear-gradient(135deg, #6366F1, #8B5CF6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -0.5px;
            ">동네 엑스레이</div>
            <div style="font-size:11px; color:#888; margin-top:2px;">서울 상권 데이터 인텔리전스</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

# ── 페이지 정의 ──
pages = {
    "홈": [
        st.Page("views/0_뉴스_타임라인.py", title="인사이트 피드", icon="📡", default=True),
    ],
    "분석 도구": [
        st.Page("views/1_동네_지도.py", title="동네 지도", icon="🗺️"),
        st.Page("views/2_동네_프로파일.py", title="동네 프로파일", icon="🔍"),
        st.Page("views/3_넥스트_핫플.py", title="넥스트 핫플", icon="🔥"),
    ],
    "시뮬레이션": [
        st.Page("views/4_디지털_트윈.py", title="디지털 트윈", icon="🌆"),
        st.Page("views/5_동네_비교.py", title="동네 비교", icon="⚖️"),
    ],
}

nav = st.navigation(pages)
nav.run()
