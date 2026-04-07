"""
AI 에이전트 채팅 UI — 채널톡 스타일 플로팅 위젯
Streamlit 페이지 위에 떠다니는 독립 HTML/JS 위젯
- localStorage로 대화 기록 유지
- 부모 페이지에 JS inject하여 진짜 fixed 위치 고정
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
    """채널톡 스타일 플로팅 채팅 위젯"""

    agent_online = _check_health()

    # 사이드바 비용
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

    # ── 방법: 부모 페이지에 직접 JS/CSS를 주입 ──
    # st.markdown으로 부모 DOM에 직접 채팅 위젯을 삽입
    # components.html iframe 대신 부모 페이지에 직접 렌더링

    chat_inject_js = f"""
    <script>
    (function() {{
        // 이미 삽입되었으면 스킵
        if (document.getElementById('xray-chat-fab')) return;

        const AGENT_URL = "{AGENT_URL}";
        const CONTEXT = {{
            selected_district: "{selected_district}",
            selected_month: "{selected_month}",
            current_tab: "{current_tab}"
        }};

        // localStorage에서 대화 복원
        let chatHistory = JSON.parse(localStorage.getItem('xray_chat_history') || '[]');
        let isOpen = localStorage.getItem('xray_chat_open') === 'true';

        // ── CSS ──
        const style = document.createElement('style');
        style.textContent = `
            #xray-chat-fab {{
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
            #xray-chat-fab:hover {{
                transform: scale(1.08);
                box-shadow: 0 6px 24px rgba(99,102,241,0.7);
            }}
            #xray-chat-fab svg {{ width: 26px; height: 26px; fill: white; }}
            #xray-chat-fab .xdot {{
                position: absolute; top: 2px; right: 2px;
                width: 12px; height: 12px; border-radius: 50%;
                background: {"#4CAF50" if agent_online else "#f44336"};
                border: 2px solid white;
            }}

            #xray-chat-popup {{
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
            #xray-chat-popup.xopen {{ display: flex; animation: xSlideUp 0.25s ease-out; }}
            @keyframes xSlideUp {{
                from {{ opacity:0; transform:translateY(16px); }}
                to {{ opacity:1; transform:translateY(0); }}
            }}

            .xhdr {{
                background: linear-gradient(135deg, #6366F1, #8B5CF6);
                padding: 14px 16px; display: flex;
                justify-content: space-between; align-items: center; flex-shrink: 0;
            }}
            .xhdr-t {{ color:white; font-size:15px; font-weight:700; }}
            .xhdr-s {{ color:rgba(255,255,255,0.6); font-size:11px; margin-top:2px; }}
            .xhdr-x {{ background:none; border:none; color:rgba(255,255,255,0.7);
                       font-size:20px; cursor:pointer; padding:0 4px; }}
            .xhdr-x:hover {{ color:white; }}

            .xmsgs {{
                flex:1; overflow-y:auto; padding:14px;
                display:flex; flex-direction:column; gap:8px;
            }}
            .xmsgs::-webkit-scrollbar {{ width:4px; }}
            .xmsgs::-webkit-scrollbar-thumb {{ background:#444; border-radius:2px; }}

            .xm-u {{
                align-self:flex-end; background:#6366F1; color:white;
                padding:8px 14px; border-radius:16px 16px 4px 16px;
                max-width:80%; font-size:13px; line-height:1.5; word-break:break-word;
            }}
            .xm-b {{
                align-self:flex-start; background:#2a2a4a; color:#E0E0E0;
                padding:10px 14px; border-radius:16px 16px 16px 4px;
                max-width:85%; font-size:13px; line-height:1.6; word-break:break-word;
            }}
            .xm-c {{ font-size:10px; color:#888; margin-top:4px; }}
            .xm-t {{ align-self:flex-start; color:#888; font-size:12px; padding:8px; }}
            .xm-t .xdot {{ animation: xblink 1.4s infinite; display:inline-block; }}
            .xm-t .xdot:nth-child(2) {{ animation-delay:0.2s; }}
            .xm-t .xdot:nth-child(3) {{ animation-delay:0.4s; }}
            @keyframes xblink {{ 0%,80%,100%{{opacity:0}} 40%{{opacity:1}} }}

            .xwel {{ text-align:center; padding:50px 20px; color:#888; }}
            .xwel-i {{ font-size:36px; margin-bottom:8px; }}
            .xwel-h {{ font-size:14px; font-weight:600; color:#ccc; }}
            .xwel-d {{ font-size:11px; margin-top:6px; line-height:1.5; }}

            .xsug {{ padding:8px 14px 4px; display:flex; flex-wrap:wrap; gap:6px; flex-shrink:0; }}
            .xsug-b {{
                background:#2a2a4a; border:1px solid #3a3a5a; color:#B0B0D0;
                padding:6px 12px; border-radius:20px; font-size:11px;
                cursor:pointer; transition:all 0.2s;
            }}
            .xsug-b:hover {{ background:#6366F1; color:white; border-color:#6366F1; }}

            .xinp {{
                padding:10px 12px; border-top:1px solid #2a2a4a;
                display:flex; gap:8px; flex-shrink:0; background:#16162a;
            }}
            .xinp input {{
                flex:1; background:#2a2a4a; border:1px solid #3a3a5a;
                border-radius:20px; padding:8px 16px; color:#E0E0E0;
                font-size:13px; outline:none;
            }}
            .xinp input:focus {{ border-color:#6366F1; }}
            .xinp input::placeholder {{ color:#555; }}
            .xinp button {{
                background:#6366F1; border:none; border-radius:50%;
                width:36px; height:36px; cursor:pointer;
                display:flex; align-items:center; justify-content:center;
            }}
            .xinp button:hover {{ background:#5355D4; }}
            .xinp button svg {{ width:16px; height:16px; fill:white; }}
            .xinp button:disabled {{ opacity:0.4; cursor:not-allowed; }}
        `;
        document.head.appendChild(style);

        // ── FAB 버튼 ──
        const fab = document.createElement('button');
        fab.id = 'xray-chat-fab';
        fab.innerHTML = '<svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg><div class="xdot"></div>';
        fab.onclick = toggleChat;
        document.body.appendChild(fab);

        // ── 채팅 팝업 ──
        const popup = document.createElement('div');
        popup.id = 'xray-chat-popup';
        popup.innerHTML = `
            <div class="xhdr">
                <div>
                    <div class="xhdr-t">🤖 동네 엑스레이 AI</div>
                    <div class="xhdr-s" id="xhdr-status">{"🟢 온라인" if agent_online else "🔴 오프라인"}</div>
                </div>
                <button class="xhdr-x" onclick="document.getElementById('xray-chat-popup').classList.remove('xopen'); localStorage.setItem('xray_chat_open','false');">✕</button>
            </div>
            <div class="xmsgs" id="xmsgs"></div>
            <div class="xsug" id="xsug">
                <button class="xsug-b" onclick="xSend('신당동 유동인구 알려줘')">신당동 유동인구</button>
                <button class="xsug-b" onclick="xSend('서초동에 카페 차리면 매출이?')">카페 시뮬레이션</button>
                <button class="xsug-b" onclick="xSend('다음 핫플은 어디야?')">넥스트 핫플</button>
                <button class="xsug-b" onclick="xSend('중구 vs 영등포구 비교')">동네 비교</button>
            </div>
            <div class="xinp">
                <input id="xinput" placeholder="메시지를 입력하세요..." onkeydown="if(event.key==='Enter')xSendInput()"/>
                <button id="xsendbtn" onclick="xSendInput()">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
        `;
        document.body.appendChild(popup);

        // 이전 대화 복원
        if (chatHistory.length > 0) {{
            document.getElementById('xsug').style.display = 'none';
            const msgs = document.getElementById('xmsgs');
            msgs.innerHTML = '';
            chatHistory.forEach(m => {{
                addMsg(m.role === 'user' ? 'u' : 'b', m.content, m.cost, m.tier, true);
            }});
        }}

        // 열려있었으면 다시 열기
        if (isOpen) popup.classList.add('xopen');

        function toggleChat() {{
            const p = document.getElementById('xray-chat-popup');
            const wasOpen = p.classList.contains('xopen');
            p.classList.toggle('xopen');
            localStorage.setItem('xray_chat_open', !wasOpen);
            if (!wasOpen) document.getElementById('xinput').focus();
        }}

        function addMsg(type, content, cost, tier, noSave) {{
            const msgs = document.getElementById('xmsgs');
            const wel = msgs.querySelector('.xwel');
            if (wel) wel.remove();

            const d = document.createElement('div');
            d.className = type === 'u' ? 'xm-u' : 'xm-b';
            let html = content.replace(/\\n/g, '<br>');
            if (cost && cost > 0) {{
                const e = {{"simple":"🟢","analysis":"🟡","complex":"🔴"}}[tier] || "⚪";
                html += '<div class="xm-c">💰 $' + cost.toFixed(4) + ' ' + e + '</div>';
            }}
            d.innerHTML = html;
            msgs.appendChild(d);
            msgs.scrollTop = msgs.scrollHeight;

            if (chatHistory.length > 0) {{
                document.getElementById('xsug').style.display = 'none';
            }}
        }}

        function saveHistory() {{
            localStorage.setItem('xray_chat_history', JSON.stringify(chatHistory));
        }}

        // 전역 함수로 등록
        window.xSendInput = function() {{
            const inp = document.getElementById('xinput');
            const t = inp.value.trim();
            if (!t) return;
            inp.value = '';
            xSend(t);
        }};

        window.xSend = async function(text) {{
            addMsg('u', text);
            chatHistory.push({{role:'user', content:text}});
            saveHistory();

            const btn = document.getElementById('xsendbtn');
            btn.disabled = true;

            // typing
            const msgs = document.getElementById('xmsgs');
            const td = document.createElement('div');
            td.className = 'xm-t'; td.id = 'xtyping';
            td.innerHTML = '<span class="xdot">●</span> <span class="xdot">●</span> <span class="xdot">●</span> 분석 중...';
            msgs.appendChild(td);
            msgs.scrollTop = msgs.scrollHeight;

            try {{
                const r = await fetch(AGENT_URL + '/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type':'application/json'}},
                    body: JSON.stringify({{
                        query: text,
                        chat_history: chatHistory.slice(0,-1),
                        selected_district: CONTEXT.selected_district,
                        selected_month: CONTEXT.selected_month,
                        current_tab: CONTEXT.current_tab
                    }})
                }});
                const ty = document.getElementById('xtyping');
                if (ty) ty.remove();

                if (r.ok) {{
                    const d = await r.json();
                    addMsg('b', d.answer || '응답 없음', d.total_cost, d.query_type);
                    chatHistory.push({{role:'assistant', content:d.answer, cost:d.total_cost, tier:d.query_type}});
                    saveHistory();
                    const st = document.getElementById('xhdr-status');
                    if (st) st.innerHTML = '🟢 온라인 · 💰 $' + (d.session_total_cost||0).toFixed(4);
                }} else {{
                    addMsg('b', '❌ 오류: ' + r.status);
                }}
            }} catch(e) {{
                const ty = document.getElementById('xtyping');
                if (ty) ty.remove();
                addMsg('b', '❌ 연결 실패: ' + e.message);
            }}
            btn.disabled = false;
            document.getElementById('xinput').focus();
        }};
    }})();
    </script>
    """

    st.markdown(chat_inject_js, unsafe_allow_html=True)
