"""
AI 에이전트 채팅 UI — 채널톡 스타일 플로팅 버튼 + 팝업 채팅창
"""
import streamlit as st
import requests
import json
import streamlit.components.v1 as components

AGENT_URL = "http://localhost:8000"


def _call_agent(query: str, chat_history: list, district: str = "", month: str = "", tab: str = "") -> dict:
    """에이전트 API 호출 (대화 히스토리 포함)"""
    try:
        resp = requests.post(
            f"{AGENT_URL}/chat",
            json={
                "query": query,
                "chat_history": chat_history,
                "selected_district": district,
                "selected_month": month,
                "current_tab": tab,
            },
            timeout=60,
        )
        if resp.status_code == 429:
            return {"error": "일일 비용 한도 초과. 내일 다시 시도해주세요."}
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "AI 에이전트 서버에 연결할 수 없습니다. (localhost:8000)"}
    except requests.Timeout:
        return {"error": "응답 시간 초과 (60초)"}
    except Exception as e:
        return {"error": f"오류: {str(e)}"}


def _get_cost_summary() -> dict | None:
    try:
        resp = requests.get(f"{AGENT_URL}/costs", timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _check_agent_health() -> bool:
    try:
        resp = requests.get(f"{AGENT_URL}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def render_chat_panel(current_tab: str = "", selected_district: str = "", selected_month: str = ""):
    """
    채널톡 스타일 플로팅 채팅 패널
    - 오른쪽 하단 버튼 클릭 → 채팅창 토글
    - 대화 히스토리 유지
    - 비용 실시간 표시
    """
    # ── 세션 초기화 ──
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "session_cost" not in st.session_state:
        st.session_state.session_cost = 0.0

    agent_online = _check_agent_health()

    # ── 플로팅 버튼 + 채팅창 (CSS/HTML) ──
    chat_history_html = ""
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            chat_history_html += f"""
            <div style="display:flex; justify-content:flex-end; margin:8px 0;">
                <div style="background:#4A90D9; color:white; padding:8px 14px; border-radius:16px 16px 4px 16px; max-width:80%; font-size:13px; word-break:break-word;">
                    {msg["content"]}
                </div>
            </div>"""
        else:
            cost_badge = ""
            if msg.get("cost"):
                cost_badge = f'<span style="color:#888; font-size:10px; display:block; margin-top:4px;">💰 ${msg["cost"]:.4f} | {msg.get("tier","")}</span>'
            chat_history_html += f"""
            <div style="display:flex; justify-content:flex-start; margin:8px 0;">
                <div style="background:#2D2D2D; color:#E0E0E0; padding:8px 14px; border-radius:16px 16px 16px 4px; max-width:85%; font-size:13px; word-break:break-word; line-height:1.5;">
                    {msg["content"]}{cost_badge}
                </div>
            </div>"""

    status_dot = "🟢" if agent_online else "🔴"
    status_text = "온라인" if agent_online else "오프라인"
    cost_summary = _get_cost_summary()
    cost_display = f"${cost_summary['total_cost']:.4f}" if cost_summary else "$0"
    query_count = cost_summary.get("total_queries", 0) if cost_summary else 0

    # Streamlit native 방식으로 구현
    # 사이드바에 비용 표시
    if cost_summary and cost_summary.get("total_queries", 0) > 0:
        with st.sidebar:
            st.divider()
            st.markdown("### 💰 AI 비용")
            st.metric("세션 총 비용", f"${cost_summary['total_cost']:.4f}")
            st.caption(f"질의 {query_count}건 | 평균 ${cost_summary.get('avg_cost', 0):.4f}/건")

    # ── 채팅 토글 버튼 ──
    # 하단 고정 expander 방식
    with st.container():
        # 플로팅 효과를 CSS로 구현
        st.markdown("""
        <style>
        .chat-float-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        }
        </style>
        """, unsafe_allow_html=True)

        # 채팅 열기/닫기
        col_spacer, col_toggle = st.columns([5, 1])
        with col_toggle:
            if st.button("🤖 AI", key="chat_toggle_btn", use_container_width=True):
                st.session_state.chat_open = not st.session_state.chat_open
                st.rerun()

    # ── 채팅창 (열려있을 때) ──
    if st.session_state.chat_open:
        st.markdown("---")

        # 헤더
        col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
        with col_h1:
            st.markdown(f"### 🤖 AI 에이전트 {status_dot}")
        with col_h2:
            st.caption(f"💰 {cost_display}")
        with col_h3:
            if st.button("✕ 닫기", key="chat_close"):
                st.session_state.chat_open = False
                st.rerun()

        # 대화 히스토리 (스크롤 가능 컨테이너)
        chat_container = st.container(height=400)
        with chat_container:
            if not st.session_state.chat_messages:
                st.markdown("""
                <div style="text-align:center; color:#888; padding:40px 20px;">
                    <div style="font-size:40px; margin-bottom:10px;">🤖</div>
                    <div style="font-size:14px; font-weight:600;">동네 엑스레이 AI</div>
                    <div style="font-size:12px; margin-top:8px;">
                        데이터 기반으로 무엇이든 물어보세요.<br>
                        유동인구, 카드매출, 소득, 부동산, 시뮬레이션 등
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for i, msg in enumerate(st.session_state.chat_messages):
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        if msg.get("cost"):
                            st.caption(f"💰 ${msg['cost']:.4f} | Tier: {msg.get('tier', '')}")

        # 입력
        if not agent_online:
            st.warning("에이전트 서버가 꺼져있습니다. `uvicorn agent.server:app --port 8000`")
        else:
            if prompt := st.chat_input("무엇이든 물어보세요...", key="floating_chat_input"):
                # 사용자 메시지 저장
                st.session_state.chat_messages.append({"role": "user", "content": prompt})

                # 대화 히스토리 준비 (이전 대화 전달)
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_messages[:-1]  # 현재 질문 제외
                ]

                # API 호출
                result = _call_agent(
                    prompt, history,
                    selected_district, selected_month, current_tab
                )

                if "error" in result:
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"❌ {result['error']}"
                    })
                else:
                    answer = result.get("answer", "응답 없음")
                    cost = result.get("total_cost", 0)
                    tier = result.get("query_type", "")
                    st.session_state.session_cost = result.get("session_total_cost", 0)

                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": answer,
                        "cost": cost,
                        "tier": tier,
                    })

                st.rerun()
