"""
AI 에이전트 채팅 UI — 채널톡 스타일 플로팅 위젯
position:fixed로 페이지 위에 떠다니는 독립 위젯
"""
import streamlit as st
import requests
import streamlit.components.v1 as components

AGENT_URL = "http://localhost:8000"


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
    """채널톡 스타일 플로팅 채팅 위젯 — 페이지 위에 떠다니는 독립 HTML 위젯"""

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

    status = "online" if agent_online else "offline"

    # 완전 독립 HTML/CSS/JS 채팅 위젯
    chat_widget_html = f"""
    <style>
        /* 플로팅 버튼 */
        #chat-fab {{
            position: fixed;
            bottom: 28px;
            right: 28px;
            z-index: 999999;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 16px rgba(99,102,241,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}
        #chat-fab:hover {{
            transform: scale(1.08);
            box-shadow: 0 6px 24px rgba(99,102,241,0.7);
        }}
        #chat-fab svg {{
            width: 26px;
            height: 26px;
            fill: white;
        }}
        #chat-fab .status-dot {{
            position: absolute;
            top: 2px;
            right: 2px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: {"#4CAF50" if agent_online else "#f44336"};
            border: 2px solid white;
        }}

        /* 채팅 팝업 */
        #chat-popup {{
            position: fixed;
            bottom: 96px;
            right: 28px;
            z-index: 999998;
            width: 380px;
            height: 520px;
            background: #1a1a2e;
            border-radius: 16px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.4);
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #2a2a4a;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}
        #chat-popup.open {{
            display: flex;
            animation: slideUp 0.25s ease-out;
        }}
        @keyframes slideUp {{
            from {{ opacity: 0; transform: translateY(16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* 헤더 */
        .chat-header {{
            background: linear-gradient(135deg, #6366F1, #8B5CF6);
            padding: 16px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-shrink: 0;
        }}
        .chat-header-title {{
            color: white;
            font-size: 15px;
            font-weight: 700;
        }}
        .chat-header-sub {{
            color: rgba(255,255,255,0.6);
            font-size: 11px;
            margin-top: 2px;
        }}
        .chat-close {{
            background: none;
            border: none;
            color: rgba(255,255,255,0.7);
            font-size: 20px;
            cursor: pointer;
            padding: 0 4px;
        }}
        .chat-close:hover {{ color: white; }}

        /* 메시지 영역 */
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .chat-messages::-webkit-scrollbar {{ width: 4px; }}
        .chat-messages::-webkit-scrollbar-thumb {{ background: #444; border-radius: 2px; }}

        .msg-user {{
            align-self: flex-end;
            background: #6366F1;
            color: white;
            padding: 8px 14px;
            border-radius: 16px 16px 4px 16px;
            max-width: 80%;
            font-size: 13px;
            line-height: 1.5;
            word-break: break-word;
        }}
        .msg-bot {{
            align-self: flex-start;
            background: #2a2a4a;
            color: #E0E0E0;
            padding: 10px 14px;
            border-radius: 16px 16px 16px 4px;
            max-width: 85%;
            font-size: 13px;
            line-height: 1.6;
            word-break: break-word;
        }}
        .msg-cost {{
            font-size: 10px;
            color: #888;
            margin-top: 4px;
        }}
        .msg-typing {{
            align-self: flex-start;
            color: #888;
            font-size: 12px;
            padding: 8px 14px;
        }}
        .msg-typing .dot {{
            animation: blink 1.4s infinite;
            display: inline-block;
        }}
        .msg-typing .dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .msg-typing .dot:nth-child(3) {{ animation-delay: 0.4s; }}
        @keyframes blink {{ 0%,80%,100% {{ opacity:0 }} 40% {{ opacity:1 }} }}

        /* 웰컴 */
        .welcome {{
            text-align: center;
            padding: 40px 20px;
            color: #888;
        }}
        .welcome-icon {{ font-size: 36px; margin-bottom: 8px; }}
        .welcome-title {{ font-size: 14px; font-weight: 600; color: #ccc; }}
        .welcome-desc {{ font-size: 11px; margin-top: 6px; line-height: 1.5; }}

        /* 추천 질문 */
        .suggestions {{
            padding: 8px 16px 4px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            flex-shrink: 0;
        }}
        .suggest-btn {{
            background: #2a2a4a;
            border: 1px solid #3a3a5a;
            color: #B0B0D0;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .suggest-btn:hover {{
            background: #6366F1;
            color: white;
            border-color: #6366F1;
        }}

        /* 입력 */
        .chat-input-area {{
            padding: 12px 14px;
            border-top: 1px solid #2a2a4a;
            display: flex;
            gap: 8px;
            flex-shrink: 0;
            background: #16162a;
        }}
        .chat-input {{
            flex: 1;
            background: #2a2a4a;
            border: 1px solid #3a3a5a;
            border-radius: 20px;
            padding: 8px 16px;
            color: #E0E0E0;
            font-size: 13px;
            outline: none;
        }}
        .chat-input:focus {{ border-color: #6366F1; }}
        .chat-input::placeholder {{ color: #666; }}
        .chat-send {{
            background: #6366F1;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }}
        .chat-send:hover {{ background: #5355D4; }}
        .chat-send svg {{ width: 16px; height: 16px; fill: white; }}
        .chat-send:disabled {{ opacity: 0.4; cursor: not-allowed; }}
    </style>

    <!-- 플로팅 버튼 -->
    <button id="chat-fab" onclick="toggleChat()">
        <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
        <div class="status-dot"></div>
    </button>

    <!-- 채팅 팝업 -->
    <div id="chat-popup">
        <div class="chat-header">
            <div>
                <div class="chat-header-title">🤖 동네 엑스레이 AI</div>
                <div class="chat-header-sub" id="header-status">{"🟢 온라인" if agent_online else "🔴 오프라인"}</div>
            </div>
            <button class="chat-close" onclick="toggleChat()">✕</button>
        </div>

        <div class="chat-messages" id="chat-messages">
            <div class="welcome">
                <div class="welcome-icon">🏙️</div>
                <div class="welcome-title">동네 데이터, 무엇이든 물어보세요</div>
                <div class="welcome-desc">
                    유동인구 · 카드매출 · 소득 · 부동산<br>
                    시뮬레이션 · 핫플 예측 · 동네 비교
                </div>
            </div>
        </div>

        <div class="suggestions" id="suggestions">
            <button class="suggest-btn" onclick="sendMessage('신당동 유동인구 알려줘')">신당동 유동인구</button>
            <button class="suggest-btn" onclick="sendMessage('서초동에 카페 차리면 매출이?')">카페 시뮬레이션</button>
            <button class="suggest-btn" onclick="sendMessage('다음 핫플은 어디야?')">넥스트 핫플</button>
            <button class="suggest-btn" onclick="sendMessage('중구 vs 영등포구 비교')">동네 비교</button>
        </div>

        <div class="chat-input-area">
            <input class="chat-input" id="chat-input" placeholder="메시지를 입력하세요..."
                   onkeydown="if(event.key==='Enter')sendFromInput()" />
            <button class="chat-send" id="send-btn" onclick="sendFromInput()">
                <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
        </div>
    </div>

    <script>
        const AGENT_URL = "{AGENT_URL}";
        const CONTEXT = {{
            selected_district: "{selected_district}",
            selected_month: "{selected_month}",
            current_tab: "{current_tab}"
        }};
        let chatHistory = [];
        let isOpen = false;

        function toggleChat() {{
            isOpen = !isOpen;
            document.getElementById('chat-popup').classList.toggle('open', isOpen);
        }}

        function addMessage(role, content, cost, tier) {{
            const container = document.getElementById('chat-messages');
            // 웰컴 메시지 제거
            const welcome = container.querySelector('.welcome');
            if (welcome) welcome.remove();

            const div = document.createElement('div');
            div.className = role === 'user' ? 'msg-user' : 'msg-bot';
            let html = content.replace(/\\n/g, '<br>');
            if (cost && cost > 0) {{
                const tierEmoji = {{"simple":"🟢","analysis":"🟡","complex":"🔴"}}[tier] || "⚪";
                html += '<div class="msg-cost">💰 $' + cost.toFixed(4) + ' ' + tierEmoji + '</div>';
            }}
            div.innerHTML = html;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;

            // 추천 질문 숨기기
            if (chatHistory.length > 0) {{
                document.getElementById('suggestions').style.display = 'none';
            }}
        }}

        function showTyping() {{
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'msg-typing';
            div.id = 'typing';
            div.innerHTML = '<span class="dot">●</span> <span class="dot">●</span> <span class="dot">●</span> 분석 중...';
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }}

        function removeTyping() {{
            const el = document.getElementById('typing');
            if (el) el.remove();
        }}

        function sendFromInput() {{
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            input.value = '';
            sendMessage(text);
        }}

        async function sendMessage(text) {{
            addMessage('user', text);
            chatHistory.push({{role: 'user', content: text}});

            const sendBtn = document.getElementById('send-btn');
            sendBtn.disabled = true;
            showTyping();

            try {{
                const resp = await fetch(AGENT_URL + '/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        query: text,
                        chat_history: chatHistory.slice(0, -1),
                        selected_district: CONTEXT.selected_district,
                        selected_month: CONTEXT.selected_month,
                        current_tab: CONTEXT.current_tab
                    }})
                }});

                removeTyping();

                if (resp.ok) {{
                    const data = await resp.json();
                    addMessage('bot', data.answer || '응답 없음', data.total_cost, data.query_type);
                    chatHistory.push({{role: 'assistant', content: data.answer}});

                    // 헤더 비용 업데이트
                    document.getElementById('header-status').innerHTML =
                        '🟢 온라인 · 💰 $' + (data.session_total_cost || 0).toFixed(4);
                }} else if (resp.status === 429) {{
                    addMessage('bot', '⚠️ 일일 비용 한도 초과');
                }} else {{
                    addMessage('bot', '❌ 서버 오류: ' + resp.status);
                }}
            }} catch (e) {{
                removeTyping();
                addMessage('bot', '❌ 연결 실패: ' + e.message);
            }}

            sendBtn.disabled = false;
            document.getElementById('chat-input').focus();
        }}
    </script>
    """

    # 높이 0으로 삽입 → 위젯은 position:fixed로 떠다님
    components.html(chat_widget_html, height=0)
