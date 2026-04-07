"""
AI 에이전트 채팅 UI — 채널톡 스타일 플로팅 위젯
우측 하단 동그란 버튼 → 클릭 시 팝업 채팅창
"""
import streamlit as st
import requests
import json
import streamlit.components.v1 as components

AGENT_URL = "http://localhost:8000"


def _call_agent(query: str, chat_history: list, district: str = "", month: str = "", tab: str = "") -> dict:
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
            return {"error": "일일 비용 한도 초과"}
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "AI 서버 연결 불가 (localhost:8000)"}
    except requests.Timeout:
        return {"error": "응답 시간 초과"}
    except Exception as e:
        return {"error": str(e)}


def _check_health() -> bool:
    try:
        return requests.get(f"{AGENT_URL}/health", timeout=2).status_code == 200
    except Exception:
        return False


def _get_cost_summary() -> dict | None:
    try:
        resp = requests.get(f"{AGENT_URL}/costs", timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def render_chat_panel(current_tab: str = "", selected_district: str = "", selected_month: str = ""):
    """채널톡 스타일 플로팅 채팅 위젯"""

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    agent_online = _check_health()

    # 사이드바 비용 표시
    cost_summary = _get_cost_summary()
    if cost_summary and cost_summary.get("total_queries", 0) > 0:
        with st.sidebar:
            st.divider()
            st.markdown("### 💰 AI 비용")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 비용", f"${cost_summary['total_cost']:.4f}")
            with col2:
                st.metric("질의 수", f"{cost_summary['total_queries']}건")

    # ── 채널톡 스타일 플로팅 버튼 (항상 표시) ──
    status_color = "#4CAF50" if agent_online else "#f44336"
    badge_count = len(st.session_state.chat_messages) // 2  # 대화 쌍 수

    float_button_html = f"""
    <style>
        .chat-fab {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 99999;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .chat-fab:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 28px rgba(99, 102, 241, 0.6);
        }}
        .chat-fab svg {{
            width: 28px;
            height: 28px;
            fill: white;
        }}
        .chat-fab-badge {{
            position: absolute;
            top: -2px;
            right: -2px;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: {status_color};
            border: 2px solid white;
        }}
    </style>
    <div class="chat-fab" onclick="window.parent.postMessage({{type:'toggle_chat'}},'*')" title="AI 에이전트">
        <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
        <div class="chat-fab-badge"></div>
    </div>
    """
    components.html(float_button_html, height=0)

    # ── 채팅창 토글 버튼 (Streamlit native) ──
    # 하단 우측에 작은 토글
    cols = st.columns([8, 1])
    with cols[1]:
        btn_label = "💬" if not st.session_state.chat_open else "✕"
        if st.button(btn_label, key="chat_toggle", help="AI 에이전트 열기/닫기"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

    # ── 채팅창 (열려있을 때) ──
    if not st.session_state.chat_open:
        return

    # 채팅 컨테이너를 CSS로 우측 하단 팝업처럼 스타일링
    st.markdown("""
    <style>
    /* 채팅 영역 스타일링 */
    [data-testid="stExpander"] {
        border: 1px solid #333 !important;
        border-radius: 16px !important;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        padding: 16px 20px;
        border-radius: 12px 12px 0 0;
        margin-bottom: 0;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:white; font-size:16px; font-weight:700;">🤖 동네 엑스레이 AI</div>
                <div style="color:rgba(255,255,255,0.7); font-size:12px; margin-top:2px;">
                    {'🟢 온라인' if agent_online else '🔴 오프라인'} · 비용: ${cost_summary['total_cost']:.4f if cost_summary else 0}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 대화 영역
    chat_container = st.container(height=380)
    with chat_container:
        if not st.session_state.chat_messages:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#888;">
                <div style="font-size:48px; margin-bottom:12px;">🏙️</div>
                <div style="font-size:15px; font-weight:600; color:#E0E0E0;">동네 데이터, 무엇이든 물어보세요</div>
                <div style="font-size:12px; margin-top:8px; line-height:1.6;">
                    유동인구 · 카드매출 · 소득 · 부동산<br>
                    시뮬레이션 · 핫플 예측 · 동네 비교
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 추천 질문 버튼
            st.markdown("**💡 이런 질문을 해보세요:**")
            suggestions = [
                "신당동 유동인구 알려줘",
                "서초동에 카페 차리면 매출이?",
                "다음 핫플은 어디야?",
                "중구 vs 영등포구 비교해줘",
            ]
            cols_s = st.columns(2)
            for i, s in enumerate(suggestions):
                with cols_s[i % 2]:
                    if st.button(s, key=f"suggest_{i}", use_container_width=True):
                        st.session_state.chat_messages.append({"role": "user", "content": s})
                        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages[:-1]]
                        result = _call_agent(s, history, selected_district, selected_month, current_tab)
                        if "error" not in result:
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": result.get("answer", ""),
                                "cost": result.get("total_cost", 0),
                                "tier": result.get("query_type", ""),
                            })
                        else:
                            st.session_state.chat_messages.append({"role": "assistant", "content": f"❌ {result['error']}"})
                        st.rerun()
        else:
            for i, msg in enumerate(st.session_state.chat_messages):
                with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
                    st.markdown(msg["content"])
                    if msg.get("cost"):
                        tier_emoji = {"simple": "🟢", "analysis": "🟡", "complex": "🔴"}.get(msg.get("tier", ""), "⚪")
                        st.caption(f"💰 ${msg['cost']:.4f} {tier_emoji}")

    # 입력 영역
    if not agent_online:
        st.error("에이전트 서버 꺼져있음 — `uvicorn agent.server:app --port 8000`")
    else:
        col_input, col_clear = st.columns([6, 1])
        with col_clear:
            if st.button("🗑️", key="clear_chat", help="대화 초기화"):
                st.session_state.chat_messages = []
                st.rerun()

        if prompt := st.chat_input("메시지를 입력하세요...", key="float_chat_input"):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})

            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages[:-1]]

            with st.spinner("분석 중..."):
                result = _call_agent(prompt, history, selected_district, selected_month, current_tab)

            if "error" in result:
                st.session_state.chat_messages.append({"role": "assistant", "content": f"❌ {result['error']}"})
            else:
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": result.get("answer", "응답 없음"),
                    "cost": result.get("total_cost", 0),
                    "tier": result.get("query_type", ""),
                })

            st.rerun()
