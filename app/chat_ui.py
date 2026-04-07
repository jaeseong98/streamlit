"""
AI 에이전트 채팅 UI — FastAPI 서버와 통신
모든 페이지 하단에 import하여 사용
"""
import streamlit as st
import requests
import json

AGENT_URL = "http://localhost:8000"


def _call_agent(query: str, district: str = "", month: str = "", tab: str = "") -> dict:
    """에이전트 API 호출"""
    try:
        resp = requests.post(
            f"{AGENT_URL}/chat",
            json={
                "query": query,
                "selected_district": district,
                "selected_month": month,
                "current_tab": tab,
            },
            timeout=30,
        )
        if resp.status_code == 429:
            return {"error": "일일 비용 한도 초과. 내일 다시 시도해주세요."}
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "AI 에이전트 서버에 연결할 수 없습니다. (http://localhost:8000)"}
    except requests.Timeout:
        return {"error": "응답 시간 초과 (30초)"}
    except Exception as e:
        return {"error": f"오류: {str(e)}"}


def _get_cost_summary() -> dict | None:
    """비용 요약 조회"""
    try:
        resp = requests.get(f"{AGENT_URL}/costs", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def render_chat_panel(current_tab: str = "", selected_district: str = "", selected_month: str = ""):
    """
    AI 에이전트 채팅 패널 렌더링
    각 페이지 하단에서 호출:
        from chat_ui import render_chat_panel
        render_chat_panel(current_tab="동네 지도", selected_district="신당동", selected_month="202506")
    """
    st.divider()
    st.subheader("🤖 AI 에이전트")

    # 서버 상태 체크
    try:
        health = requests.get(f"{AGENT_URL}/health", timeout=2)
        if health.status_code == 200:
            st.caption("🟢 에이전트 연결됨")
        else:
            st.caption("🔴 에이전트 응답 이상")
    except Exception:
        st.caption("🔴 에이전트 서버 꺼져있음 — `uvicorn agent.server:app` 으로 시작하세요")
        return

    # 세션 히스토리
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # 대화 표시
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("cost"):
                st.caption(f"💰 ${msg['cost']:.4f} | {msg.get('tier', '')}")

    # 입력
    if prompt := st.chat_input("데이터에 대해 무엇이든 물어보세요...", key="agent_chat_input"):
        # 사용자 메시지
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # API 호출
        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                result = _call_agent(prompt, selected_district, selected_month, current_tab)

            if "error" in result:
                st.error(result["error"])
                st.session_state.chat_messages.append({
                    "role": "assistant", "content": f"❌ {result['error']}"
                })
            else:
                answer = result.get("answer", "응답 없음")
                st.markdown(answer)

                # 차트 렌더링
                chart = result.get("chart_data")
                if chart and isinstance(chart, dict) and chart.get("type"):
                    _render_chart(chart)

                # 비용 표시
                cost = result.get("total_cost", 0)
                tier = result.get("query_type", "")
                session_cost = result.get("session_total_cost", 0)
                st.caption(f"💰 이 질문: ${cost:.4f} | Tier: {tier} | 세션 누적: ${session_cost:.4f}")

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "cost": cost,
                    "tier": tier,
                })

    # 사이드바에 비용 표시
    with st.sidebar:
        cost_summary = _get_cost_summary()
        if cost_summary and cost_summary.get("total_queries", 0) > 0:
            st.divider()
            st.markdown("### 💰 AI 비용")
            st.metric("세션 총 비용", f"${cost_summary['total_cost']:.4f}")
            st.caption(f"질의 {cost_summary['total_queries']}건 | 평균 ${cost_summary['avg_cost']:.4f}/건")

            tier = cost_summary.get("tier_distribution", {})
            if any(tier.values()):
                cols = st.columns(3)
                with cols[0]:
                    st.metric("🟢 Tier1", tier.get("nano", 0))
                with cols[1]:
                    st.metric("🟡 Tier2", tier.get("mini", 0))
                with cols[2]:
                    st.metric("🔴 Tier3", tier.get("full", 0))


def _render_chart(chart_data: dict):
    """차트 데이터 → Plotly 차트 렌더링"""
    import plotly.graph_objects as go

    chart_type = chart_data.get("type", "bar")
    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    title = chart_data.get("title", "")

    if not labels or not values:
        return

    if chart_type == "bar":
        fig = go.Figure(go.Bar(x=labels, y=values, marker_color="#636EFA"))
    elif chart_type == "line":
        fig = go.Figure(go.Scatter(x=labels, y=values, mode="lines+markers", line=dict(color="#636EFA")))
    elif chart_type == "radar":
        fig = go.Figure(go.Scatterpolar(r=values + [values[0]], theta=labels + [labels[0]], fill="toself"))
    else:
        fig = go.Figure(go.Bar(x=labels, y=values))

    fig.update_layout(title=title, height=350)
    st.plotly_chart(fig, use_container_width=True, key=f"agent_chart_{hash(title)}")
