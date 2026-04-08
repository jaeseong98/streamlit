"""
인사이트 피드 — 인스타 스타일 3x3 그리드 + 카테고리 캐러셀
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from news_engine import generate_news_items, render_detail_panel
from chat_ui import render_chat_panel

# ── 인사이트 생성 ──
news_items = generate_news_items()

if not news_items:
    st.title("📡 인사이트 피드")
    st.info("감지된 인사이트가 없습니다.")
    st.stop()

# ── 시간 표시 ──
def _fake_time_ago(index, severity):
    if severity == "high":
        minutes = [2, 5, 8, 11, 15, 19, 23, 28, 33, 40]
    elif severity == "medium":
        minutes = [7, 14, 22, 31, 38, 47, 55, 68, 79, 90]
    else:
        minutes = [18, 35, 52, 74, 95, 120, 145, 180, 210, 260]
    m = minutes[index % len(minutes)]
    if m < 60:
        return f"{m}분 전"
    return f"{m // 60}시간 전"

# ── 카테고리 목록 ──
all_categories = []
seen = set()
for item in news_items:
    tag = item["tag"]
    if tag not in seen:
        all_categories.append(tag)
        seen.add(tag)

# ── 세션 상태 ──
if "selected_news" not in st.session_state:
    st.session_state.selected_news = None
if "category_idx" not in st.session_state:
    st.session_state.category_idx = 0
if "show_more" not in st.session_state:
    st.session_state.show_more = False

# ═══════════════════════════════════════
# 상세 보기 모드
# ═══════════════════════════════════════
if st.session_state.selected_news is not None:
    current_cat = all_categories[st.session_state.category_idx % len(all_categories)]
    cat_items = [item for item in news_items if item["tag"] == current_cat]
    detail_idx = st.session_state.selected_news

    if detail_idx >= len(cat_items):
        detail_idx = 0
        st.session_state.selected_news = 0

    selected_item = cat_items[detail_idx]

    # ── 헤더: 뒤로가기 + 카테고리 ──
    col_back, col_cat_title, col_count = st.columns([1, 4, 1])
    with col_back:
        if st.button("← 피드", type="secondary", key="back_to_feed"):
            st.session_state.selected_news = None
            st.rerun()
    with col_cat_title:
        st.markdown(f"### {selected_item['icon']} {current_cat}")
    with col_count:
        st.caption(f"{detail_idx + 1} / {len(cat_items)}")

    # ── 좌우 네비게이션 (같은 카테고리 내) ──
    col_prev, col_content, col_next = st.columns([1, 10, 1])
    with col_prev:
        st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
        if detail_idx > 0:
            if st.button("◀", key="detail_prev", use_container_width=True):
                st.session_state.selected_news = detail_idx - 1
                st.rerun()
    with col_next:
        st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
        if detail_idx < len(cat_items) - 1:
            if st.button("▶", key="detail_next", use_container_width=True):
                st.session_state.selected_news = detail_idx + 1
                st.rerun()

    with col_content:
        # ── 게시글 스타일 헤더 ──
        severity = selected_item.get("severity", "low")
        sev_badge = {"high": "🔴 긴급", "medium": "🟡 주의", "low": "🟢 참고"}
        border_color = {"high": "#f44336", "medium": "#FF9800", "low": "#4CAF50"}
        time_ago = _fake_time_ago(detail_idx, severity)

        st.markdown(
            f"""
            <div style="
                border: 1px solid #2a2a4a;
                border-radius: 16px;
                overflow: hidden;
                background: #16162a;
                margin-bottom: 16px;
            ">
                <div style="
                    background: linear-gradient(135deg, {border_color[severity]}22, transparent);
                    padding: 20px 24px;
                    border-bottom: 1px solid #2a2a4a;
                ">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:28px;">{selected_item['icon']}</span>
                            <div>
                                <div style="font-size:11px; color:#888;">
                                    <span style="
                                        background:{selected_item['tag_color']};
                                        color:white;
                                        padding:2px 8px;
                                        border-radius:10px;
                                        font-size:10px;
                                        font-weight:600;
                                    ">{selected_item['tag']}</span>
                                    &nbsp;·&nbsp; {sev_badge[severity]} &nbsp;·&nbsp; 🕐 {time_ago}
                                </div>
                                <div style="font-size:20px; font-weight:800; color:#E0E0E0; margin-top:4px;">
                                    {selected_item['title']}
                                </div>
                            </div>
                        </div>
                        <div style="text-align:right; color:#888; font-size:12px;">
                            📅 {selected_item['month']}
                        </div>
                    </div>
                    <div style="font-size:14px; color:#B0B0B0; line-height:1.6;">
                        {selected_item['summary']}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 상세 분석 (게시글 본문) ──
        st.markdown("#### 📊 상세 분석")
        render_detail_panel(selected_item)

        # ── 관련 인사이트 ──
        st.divider()
        st.markdown("#### 📌 관련 인사이트")
        related = [item for item in cat_items if item != selected_item][:3]
        if related:
            rel_cols = st.columns(len(related))
            for j, rel in enumerate(related):
                with rel_cols[j]:
                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #333;
                            padding:12px;
                            border-radius:10px;
                            background:#1a1a2e;
                        ">
                            <div style="font-size:11px; color:{rel['tag_color']}; font-weight:600;">{rel['tag']}</div>
                            <div style="font-size:13px; font-weight:600; margin:4px 0; color:#E0E0E0;">{rel['icon']} {rel['title']}</div>
                            <div style="font-size:11px; color:#888;">{rel['summary'][:50]}...</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("같은 카테고리의 다른 인사이트가 없습니다.")

    page_context = f"인사이트 피드 - 선택됨: {selected_item['title']}"

# ═══════════════════════════════════════
# 피드 그리드 모드
# ═══════════════════════════════════════
else:
    # ── 타이틀 + 요약 ──
    st.title("📡 인사이트 피드")

    high_count = sum(1 for i in news_items if i.get("severity") == "high")
    med_count = sum(1 for i in news_items if i.get("severity") == "medium")
    low_count = sum(1 for i in news_items if i.get("severity") == "low")
    st.caption(
        f"총 {len(news_items)}건 · "
        f"🔴 {high_count} · 🟡 {med_count} · 🟢 {low_count}"
    )

    # ── 카테고리 캐러셀 (좌우 화살표) ──
    cat_idx = st.session_state.category_idx % len(all_categories)
    current_cat = all_categories[cat_idx]

    col_left, col_tabs, col_right = st.columns([1, 10, 1])
    with col_left:
        if st.button("◀", key="cat_prev", use_container_width=True):
            st.session_state.category_idx = (cat_idx - 1) % len(all_categories)
            st.session_state.show_more = False
            st.rerun()
    with col_right:
        if st.button("▶", key="cat_next", use_container_width=True):
            st.session_state.category_idx = (cat_idx + 1) % len(all_categories)
            st.session_state.show_more = False
            st.rerun()

    with col_tabs:
        # 카테고리 인디케이터
        indicators = []
        for ci, cat in enumerate(all_categories):
            cat_color = "#6366F1" if ci == cat_idx else "#444"
            cat_count = sum(1 for item in news_items if item["tag"] == cat)
            # 태그 색상 가져오기
            tag_color = next((item["tag_color"] for item in news_items if item["tag"] == cat), "#888")
            if ci == cat_idx:
                indicators.append(
                    f'<span style="background:{tag_color}; color:white; padding:4px 14px; '
                    f'border-radius:16px; font-size:13px; font-weight:700;">'
                    f'{cat} ({cat_count})</span>'
                )
            else:
                indicators.append(
                    f'<span style="background:#2a2a4a; color:#888; padding:4px 12px; '
                    f'border-radius:16px; font-size:12px; cursor:pointer;">'
                    f'{cat}</span>'
                )

        st.markdown(
            f'<div style="display:flex; gap:8px; align-items:center; justify-content:center; '
            f'flex-wrap:wrap; padding:4px 0;">'
            + " ".join(indicators)
            + "</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── 현재 카테고리 인사이트 필터 ──
    cat_items = [item for item in news_items if item["tag"] == current_cat]

    if not cat_items:
        st.info(f"'{current_cat}' 카테고리에 인사이트가 없습니다.")
    else:
        # 표시할 개수 (기본 9, 더보기 시 전체)
        show_count = len(cat_items) if st.session_state.show_more else min(9, len(cat_items))
        display_items = cat_items[:show_count]

        # ── 3x3 그리드 렌더링 ──
        for row_start in range(0, len(display_items), 3):
            row_items = display_items[row_start:row_start + 3]
            cols = st.columns(3)

            for col_idx, item in enumerate(row_items):
                global_idx = row_start + col_idx
                severity = item.get("severity", "low")
                border_color = {"high": "#f44336", "medium": "#FF9800", "low": "#4CAF50"}
                sev_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                time_ago = _fake_time_ago(global_idx, severity)

                with cols[col_idx]:
                    st.markdown(
                        f"""
                        <div style="
                            border: 1px solid #2a2a4a;
                            border-top: 3px solid {border_color[severity]};
                            border-radius: 12px;
                            padding: 16px;
                            background: #16162a;
                            min-height: 160px;
                            display: flex;
                            flex-direction: column;
                            justify-content: space-between;
                        ">
                            <div>
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                    <span style="font-size:11px; color:#888;">{sev_badge[severity]} {time_ago}</span>
                                    <span style="font-size:10px; color:#666;">📅 {item['month']}</span>
                                </div>
                                <div style="font-size:22px; margin-bottom:8px;">{item['icon']}</div>
                                <div style="font-size:14px; font-weight:700; color:#E0E0E0; margin-bottom:6px; line-height:1.4;">
                                    {item['title']}
                                </div>
                                <div style="font-size:12px; color:#9E9E9E; line-height:1.4;">
                                    {item['summary'][:60]}{'...' if len(item['summary']) > 60 else ''}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "상세 보기",
                        key=f"grid_{cat_idx}_{global_idx}",
                        use_container_width=True,
                        type="tertiary",
                        icon="🔎",
                    ):
                        st.session_state.selected_news = global_idx
                        st.rerun()

        # ── 더 보기 / 접기 ──
        if len(cat_items) > 9:
            st.divider()
            if st.session_state.show_more:
                if st.button("접기 ▲", use_container_width=True, type="secondary"):
                    st.session_state.show_more = False
                    st.rerun()
            else:
                remaining = len(cat_items) - 9
                if st.button(
                    f"더 보기 ({remaining}건 더) ▼",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state.show_more = True
                    st.rerun()

    page_context = f"인사이트 피드 - {current_cat} 카테고리, {len(cat_items)}건"

render_chat_panel(current_tab="메인", selected_district=None, selected_month=None, page_context=page_context)
