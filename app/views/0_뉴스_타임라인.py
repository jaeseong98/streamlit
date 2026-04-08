"""
인사이트 피드 — 토스증권 스타일 3컬럼 시그널 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_loader import (
    load_region_master, load_population_agg, load_card_sales_agg,
    load_card_sales_time, load_population_time, load_population_demo,
    load_income_agg, load_realestate,
)
from scoring import calc_monthly_signals
from charts import (
    spending_radar_chart, realestate_trend_chart,
    population_flow_chart, population_pyramid,
    income_distribution_chart, job_donut_chart,
    TIME_SLOT_KOR,
)
from chat_ui import render_chat_panel

# ── CSS ──
st.markdown("""<style>
/* 컬럼 내 간격 제거 */
[data-testid="stColumn"]:first-child [data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stColumn"]:nth-child(2) [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
/* 투명 버튼 — 카드 크기에 맞춰 겹치기 */
[data-testid="stBaseButton-tertiary"] {
    margin: 0 !important; position: relative; z-index: 1;
    margin-top: -38px !important; height: 38px !important;
}
[data-testid="stBaseButton-tertiary"] button {
    min-height: 38px !important; height: 38px !important;
    padding: 0 !important; opacity: 0 !important; cursor: pointer !important;
}
/* 시그널 카드 hover */
.sig-card { transition: background 0.15s; border-radius: 0 6px 6px 0; }
.sig-card:hover { background: rgba(128,128,128,0.06) !important; }
.signal-header {
    font-size: 13px; font-weight: 700; padding: 12px 0 8px;
    border-bottom: 1px solid rgba(128,128,128,0.15); margin-bottom: 18px;
}
.kw-tag {
    display: inline-block; padding: 5px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 500; margin: 3px 4px 3px 0;
    border: 1px solid rgba(128,128,128,0.25); background: rgba(128,128,128,0.08);
}
.detail-title-sub { font-size: 13px; opacity: 0.55; margin-bottom: 2px; }
.detail-title { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.detail-title .name { font-size: 22px; font-weight: 800; }
.detail-title .change { font-size: 22px; font-weight: 800; }
.detail-title .change.up { color: #f04452; }
.detail-title .change.down { color: #3182f6; }
.detail-title .date { font-size: 13px; opacity: 0.45; }
/* 오른쪽 내 동네 글씨 축소 */
[data-testid="stColumn"]:last-child [data-testid="stMetricValue"] { font-size: 20px !important; }
[data-testid="stColumn"]:last-child [data-testid="stMetricLabel"] { font-size: 11px !important; }
[data-testid="stColumn"]:last-child [data-testid="stMetricDelta"] { font-size: 11px !important; }
[data-testid="stColumn"]:last-child h3 { font-size: 14px !important; }
</style>""", unsafe_allow_html=True)

# ── 데이터 로드 ──
region_master = load_region_master()
pop_agg = load_population_agg()
card_agg = load_card_sales_agg()

data_districts = set(pop_agg["DISTRICT_CODE"].unique())
rm = region_master[region_master["district_code"].isin(data_districts)].copy()
rm["label"] = rm["city_kor"] + " " + rm["district_kor"]
district_options = rm.sort_values("label")["label"].tolist()

if not district_options:
    st.error("데이터가 있는 법정동이 없습니다.")
    st.stop()

@st.cache_data
def _cached_signals(_pop, _card, _rm):
    return calc_monthly_signals(_pop, _card, _rm)

signals = _cached_signals(pop_agg, card_agg, region_master)

if "selected_signal_idx" not in st.session_state:
    st.session_state.selected_signal_idx = 0
if "my_neighborhood" not in st.session_state:
    st.session_state.my_neighborhood = district_options[0]

# ── 헤더 ──
total_records = len(pop_agg) + len(card_agg)
st.markdown(
    f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;">'
    f'<span style="color:#6366F1; font-weight:700; font-size:16px;">✦</span>'
    f'<span style="font-size:13px; font-weight:600; opacity:0.5;">'
    f'데이터 {total_records:,}건을 분석한 시그널</span></div>',
    unsafe_allow_html=True,
)

if not signals:
    st.info("감지된 시그널이 없습니다.")
    st.stop()

# ═══════════════════════════════════════
col_left, col_mid, col_right = st.columns([3, 5, 4])

# ─────────────────────────────────────
# LEFT: 시그널 리스트
# ─────────────────────────────────────
with col_left:
    filter_val = st.radio("필터", ["전체", "상승", "하락"], horizontal=True, label_visibility="collapsed")
    if filter_val == "상승":
        filtered = [s for s in signals if s["direction"] == "up"]
    elif filter_val == "하락":
        filtered = [s for s in signals if s["direction"] == "down"]
    else:
        filtered = list(signals)

    month_groups: dict[str, list] = {}
    for s in filtered:
        month_groups.setdefault(s["month_label"], []).append(s)

    signal_scroll = st.container(height=480)
    with signal_scroll:
      for month_label, month_sigs in month_groups.items():
        year = month_label[:4]
        mon = month_label[5:]
        st.markdown(f'<div class="signal-header">{year}년 {int(mon)}월</div>', unsafe_allow_html=True)

        for sig_item in month_sigs:
            global_idx = signals.index(sig_item) if sig_item in signals else 0
            is_selected = global_idx == st.session_state.selected_signal_idx
            chg_prefix = "+" if sig_item["direction"] == "up" else ""
            color = "#f04452" if sig_item["direction"] == "up" else "#3182f6"
            dir_label = "상승" if sig_item["direction"] == "up" else "하락"
            kw = sig_item["keywords"][0] if sig_item["keywords"] else ""

            bg = "rgba(99,102,241,0.10)" if is_selected else "transparent"
            bl = "3px solid #6366F1" if is_selected else "3px solid transparent"

            st.markdown(
                f'<div class="sig-card" style="padding:8px 8px; background:{bg}; border-left:{bl};">'
                f'  <div style="font-size:14px; font-weight:700;">{sig_item["name"]}</div>'
                f'  <div style="font-size:12px; margin-top:2px;">'
                f'    <span style="color:{color};">{chg_prefix}{sig_item["composite"]}점 {dir_label}</span>'
                f'    <span style="opacity:0.35;"> · {kw}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("ㅤ", key=f"sig_{global_idx}", use_container_width=True, type="tertiary"):
                st.session_state.selected_signal_idx = global_idx
                st.rerun()

    # ── 근처 시그널 (클릭 가능) ──
    st.divider()
    my_nb = st.session_state.my_neighborhood
    my_city = my_nb.split(" ")[0] if my_nb else ""
    my_short = my_nb.split(" ")[-1] if my_nb else ""
    nearby = [s for s in signals if s["city"] == my_city and s["name"] != my_nb][:3]
    if nearby:
        st.markdown(f'<div style="font-size:13px; font-weight:700; margin-bottom:4px;">{my_short} 근처 시그널</div>', unsafe_allow_html=True)
        for ni, r in enumerate(nearby):
            rcolor = "#f04452" if r["direction"] == "up" else "#3182f6"
            rp = "+" if r["direction"] == "up" else ""
            rk = r["keywords"][0] if r["keywords"] else ""
            st.markdown(
                f'<div class="sig-card" style="padding:10px 0; cursor:pointer;">'
                f'  <div style="font-size:13px; font-weight:600;">{r["name"]}</div>'
                f'  <div style="font-size:12px; margin-top:3px;">'
                f'    <span style="color:{rcolor};">{rp}{r["composite"]}점</span>'
                f'    <span style="opacity:0.35;"> · {rk}</span></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("ㅤ", key=f"nearby_{ni}", use_container_width=True, type="tertiary"):
                idx = signals.index(r) if r in signals else None
                if idx is not None:
                    st.session_state.selected_signal_idx = idx
                    st.rerun()

# ─────────────────────────────────────
# MIDDLE: 상세 패널
# ─────────────────────────────────────
with col_mid:
    sel_idx = min(st.session_state.selected_signal_idx, len(signals) - 1)
    sig = signals[sel_idx]
    chg_prefix = "+" if sig["direction"] == "up" else ""
    dir_text = "상승" if sig["direction"] == "up" else "하락"
    dir_cls = "up" if sig["direction"] == "up" else "down"
    short_name = sig["name"]
    main_kw = sig["keywords"][0] if sig["keywords"] else "지표 변동"
    m_year, m_mon = sig["month_label"][:4], sig["month_label"][5:]

    # 조사 처리
    last_char = main_kw[-1] if main_kw else ""
    has_batchim = last_char and (ord(last_char) - 0xAC00) % 28 > 0 if '\uAC00' <= last_char <= '\uD7A3' else False
    josa = "으로" if has_batchim else "로"
    st.markdown(f'<div class="detail-title-sub">{main_kw}{josa}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="detail-title">'
        f'  <span class="name">{short_name}</span>'
        f'  <span class="change {dir_cls}">{chg_prefix}{abs(sig["composite"])}점 {dir_text}</span>'
        f'  <span class="date">{m_year}년 {int(m_mon)}월</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 왜 올랐을까?
    why_title = "왜 올랐을까?" if sig["direction"] == "up" else "왜 떨어졌을까?"
    with st.container(border=True):
        st.markdown(f"**{why_title}**")
        reasons_html = "".join(
            f'<li style="font-size:13px; line-height:1.7; opacity:0.75; margin-bottom:4px;">{r}</li>'
            for r in sig["reasons"]
        )
        st.markdown(f'<ul style="padding-left:18px; margin:6px 0 0;">{reasons_html}</ul>', unsafe_allow_html=True)

    kw_html = "".join(f'<span class="kw-tag">{kw}</span>' for kw in sig["keywords"])
    st.markdown(kw_html, unsafe_allow_html=True)

    # 출처 (접힌 상태)
    with st.expander(f"{len(sig['sources'])}개 출처", expanded=False):
        for src in sig["sources"]:
            st.markdown(f'<div style="font-size:12px; padding:2px 0;">{src} · {m_year}년 {int(m_mon)}월</div>', unsafe_allow_html=True)

    # 점수 breakdown (접힌 상태)
    with st.expander("점수 구성 보기", expanded=False):
        pop_score = sig["pop_chg"] * 0.35
        sales_score = sig["sales_chg"] * 0.35
        visit_score = sig["visit_chg"] * 0.30
        for label, chg, weight, score in [
            ("유동인구", sig["pop_chg"], 35, pop_score),
            ("카드매출", sig["sales_chg"], 35, sales_score),
            ("방문인구", sig["visit_chg"], 30, visit_score),
        ]:
            bar_color = "#f04452" if score > 0 else "#3182f6"
            bar_width = min(abs(score) / max(abs(sig["composite"]), 1) * 100, 100)
            sp = "+" if score > 0 else ""
            cp = "+" if chg > 0 else ""
            st.markdown(
                f'<div style="padding:5px 0;">'
                f'  <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:2px;">'
                f'    <span>{label} <span style="opacity:0.35;">({weight}%)</span></span>'
                f'    <span style="font-weight:700; color:{bar_color};">{sp}{score:.1f}점</span>'
                f'  </div>'
                f'  <div style="display:flex; align-items:center; gap:6px;">'
                f'    <div style="flex:1; height:5px; border-radius:3px; background:rgba(128,128,128,0.1);">'
                f'      <div style="width:{bar_width}%; height:100%; border-radius:3px; background:{bar_color};"></div></div>'
                f'    <span style="font-size:10px; opacity:0.35;">{cp}{chg}%</span>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        mid_current = round(100 + sig["composite"], 1)
        total_color = "#f04452" if sig["composite"] > 0 else "#3182f6"
        total_prefix = "+" if sig["composite"] > 0 else ""
        st.markdown(
            f'<div style="padding:6px 0 2px; border-top:1px solid rgba(128,128,128,0.12); margin-top:4px;">'
            f'  <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:800;">'
            f'    <span>종합</span>'
            f'    <span style="color:{total_color};">{mid_current}점</span>'
            f'  </div>'
            f'  <div style="text-align:right; font-size:10px; opacity:0.35;">100점 → {mid_current}점 ({total_prefix}{sig["composite"]}점)</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # 연관 동네 (클릭 가능)
    st.markdown('<div style="font-size:14px; font-weight:700; margin-bottom:6px;">연관 동네</div>', unsafe_allow_html=True)
    same_city = [s for s in signals if s["city"] == sig["city"] and s["dc"] != sig["dc"]]
    if same_city:
        for ri, rel in enumerate(same_city[:5]):
            rc = "#f04452" if rel["direction"] == "up" else "#3182f6"
            rp = "+" if rel["direction"] == "up" else ""
            rk = rel["keywords"][0] if rel["keywords"] else ""
            rel_curr = round(100 + rel["composite"], 1)
            st.markdown(
                f'<div class="sig-card" style="display:flex; justify-content:space-between; align-items:center;'
                f'  padding:8px 0; border-bottom:1px solid rgba(128,128,128,0.08); cursor:pointer;">'
                f'  <div style="display:flex; align-items:center; gap:8px;">'
                f'    <span style="font-size:13px; font-weight:600;">{rel["name"]}</span>'
                f'    <span style="font-size:13px; font-weight:700;">{rel_curr}점</span>'
                f'    <span style="font-size:12px; color:{rc}; font-weight:600;">{rp}{rel["composite"]}점</span>'
                f'  </div>'
                f'  <span style="font-size:11px; opacity:0.35;">{rk}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("ㅤ", key=f"rel_{ri}", use_container_width=True, type="tertiary"):
                idx = signals.index(rel) if rel in signals else None
                if idx is not None:
                    st.session_state.selected_signal_idx = idx
                    st.rerun()
    else:
        st.caption("같은 구의 다른 시그널이 없습니다.")

# ─────────────────────────────────────
# RIGHT: 내 동네 프로파일
# ─────────────────────────────────────
with col_right:
    st.markdown('<div style="font-size:14px; font-weight:700;">내 동네</div>', unsafe_allow_html=True)
    current_idx = district_options.index(st.session_state.my_neighborhood) if st.session_state.my_neighborhood in district_options else 0
    new_nb = st.selectbox("동네 변경", district_options, index=current_idx, label_visibility="collapsed", key="my_nb_select")
    if new_nb != st.session_state.my_neighborhood:
        st.session_state.my_neighborhood = new_nb
        st.rerun()

    sel_row = rm[rm["label"] == new_nb].iloc[0]
    dc = sel_row["district_code"]
    city = sel_row["city_kor"]
    district = sel_row["district_kor"]

    all_months = sorted(pop_agg["STANDARD_YEAR_MONTH"].unique(), reverse=True)
    latest_month = all_months[0] if all_months else None
    prev_month = all_months[1] if len(all_months) >= 2 else None
    ml_str = f"{str(latest_month)[:4]}년 {int(str(latest_month)[4:6])}월" if latest_month else ""
    st.caption(f"{city} {district} · {ml_str}")

    if not latest_month:
        st.stop()

    pop_d = pop_agg[(pop_agg["DISTRICT_CODE"] == dc) & (pop_agg["STANDARD_YEAR_MONTH"] == latest_month)]
    card_d = card_agg[(card_agg["DISTRICT_CODE"] == dc) & (card_agg["STANDARD_YEAR_MONTH"] == latest_month)]
    pop_prev_d = pop_agg[(pop_agg["DISTRICT_CODE"] == dc) & (pop_agg["STANDARD_YEAR_MONTH"] == prev_month)] if prev_month else pd.DataFrame()
    card_prev_d = card_agg[(card_agg["DISTRICT_CODE"] == dc) & (card_agg["STANDARD_YEAR_MONTH"] == prev_month)] if prev_month else pd.DataFrame()

    try:
        income_agg_data = load_income_agg()
        income_d = income_agg_data[(income_agg_data["DISTRICT_CODE"] == dc) & (income_agg_data["STANDARD_YEAR_MONTH"] == latest_month)]
    except Exception:
        income_d = pd.DataFrame()

    # ── 탭 ──
    tab_summary, tab_spend, tab_people, tab_estate, tab_finance = st.tabs(
        ["요약", "소비", "인구", "부동산", "금융"]
    )

    with tab_summary:
        # 프로파일 점수
        my_sig = [s for s in signals if s["dc"] == dc]
        if my_sig:
            ls = my_sig[0]
            current_score = round(100 + ls["composite"], 1)
            score_color = "#f04452" if ls["direction"] == "up" else "#3182f6"
            score_prefix = "+" if ls["direction"] == "up" else ""
            st.markdown(
                f'<div style="padding:4px 0;">'
                f'  <div style="font-size:11px; opacity:0.5;">프로파일 점수</div>'
                f'  <div style="font-size:26px; font-weight:800;">{current_score}점</div>'
                f'  <div style="font-size:11px; color:{score_color};">'
                f'    전월대비 {score_prefix}{ls["composite"]}점 (100점 → {current_score}점)</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            with st.expander("점수 구성 보기"):
                for label, chg, weight, score in [
                    ("유동인구", ls["pop_chg"], 35, round(ls["pop_chg"] * 0.35, 1)),
                    ("카드매출", ls["sales_chg"], 35, round(ls["sales_chg"] * 0.35, 1)),
                    ("방문인구", ls["visit_chg"], 30, round(ls["visit_chg"] * 0.30, 1)),
                ]:
                    bc = "#f04452" if score > 0 else "#3182f6"
                    bw = min(abs(score) / max(abs(ls["composite"]), 1) * 100, 100)
                    sp = "+" if score > 0 else ""
                    cp = "+" if chg > 0 else ""
                    st.markdown(
                        f'<div style="padding:3px 0;">'
                        f'  <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:2px;">'
                        f'    <span>{label} <span style="opacity:0.35;">({weight}%)</span></span>'
                        f'    <span style="font-weight:700; color:{bc};">{sp}{score}점</span></div>'
                        f'  <div style="display:flex; align-items:center; gap:4px;">'
                        f'    <div style="flex:1; height:3px; border-radius:2px; background:rgba(128,128,128,0.1);">'
                        f'      <div style="width:{bw}%; height:100%; border-radius:2px; background:{bc};"></div></div>'
                        f'    <span style="font-size:9px; opacity:0.35;">{cp}{chg}%</span></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

        if not pop_d.empty:
            total_curr = pop_d["RESIDENTIAL_POPULATION"].values[0] + pop_d["WORKING_POPULATION"].values[0] + pop_d["VISITING_POPULATION"].values[0]
            delta_str = None
            if not pop_prev_d.empty:
                total_prev = pop_prev_d["RESIDENTIAL_POPULATION"].values[0] + pop_prev_d["WORKING_POPULATION"].values[0] + pop_prev_d["VISITING_POPULATION"].values[0]
                if total_prev > 0:
                    delta_pct = (total_curr - total_prev) / total_prev * 100
                    delta_str = f"{total_curr - total_prev:+,.0f}명 ({delta_pct:+.1f}%)"
            st.metric("총 유동인구", f"{total_curr:,.0f}명", delta_str)

            st.caption("전월대비 변동률")
            r_cols = st.columns(3)
            for j, (lb, cn) in enumerate(zip(["거주", "직장", "방문"], ["RESIDENTIAL_POPULATION", "WORKING_POPULATION", "VISITING_POPULATION"])):
                with r_cols[j]:
                    v = pop_d[cn].values[0]
                    d = None
                    if not pop_prev_d.empty:
                        pv = pop_prev_d[cn].values[0]
                        if pv > 0:
                            d = f"전월대비 {(v - pv) / pv * 100:+.1f}%"
                    st.metric(lb, f"{v:,.0f}", d)

        m_cols = st.columns(3)
        with m_cols[0]:
            if not card_d.empty and "TOTAL_SALES" in card_d.columns:
                val = card_d["TOTAL_SALES"].values[0]
                disp = f"{val/1e8:,.1f}억" if val > 1e8 else f"{val/1e4:,.0f}만"
                d_s = None
                if not card_prev_d.empty and "TOTAL_SALES" in card_prev_d.columns:
                    pv = card_prev_d["TOTAL_SALES"].values[0]
                    if pv > 0:
                        d_s = f"{(val - pv) / pv * 100:+.1f}%"
                st.metric("카드매출", disp, d_s)
        with m_cols[1]:
            if not income_d.empty and "AVERAGE_INCOME" in income_d.columns:
                avg = income_d["AVERAGE_INCOME"].values[0]
                if pd.notna(avg) and avg > 0:
                    st.metric("평균소득", f"{avg/1e4:,.0f}만")
        with m_cols[2]:
            if not income_d.empty and "total_customers" in income_d.columns:
                cust = income_d["total_customers"].values[0]
                st.metric("고객수", f"{cust:,.0f}")

    with tab_spend:
        if not card_d.empty:
            fig = spending_radar_chart(card_d.iloc[0], f"{district} 소비 DNA")
            fig.update_layout(height=250, margin=dict(l=25, r=25, t=35, b=25))
            st.plotly_chart(fig, use_container_width=True, key="my_radar")
        try:
            card_time = load_card_sales_time()
            ct_d = card_time[(card_time["DISTRICT_CODE"] == dc) & (card_time["STANDARD_YEAR_MONTH"] == latest_month)]
            if not ct_d.empty and "TIME_SLOT" in ct_d.columns:
                time_order = ["T06", "T09", "T12", "T15", "T18", "T21", "T24"]
                ct_agg = ct_d.groupby("TIME_SLOT")[["FOOD_SALES", "COFFEE_SALES", "TOTAL_SALES"]].sum()
                ct_agg = ct_agg.reindex([t for t in time_order if t in ct_agg.index]).fillna(0)
                labels = [TIME_SLOT_KOR.get(t, t) for t in ct_agg.index]
                fig_ct = go.Figure()
                if "TOTAL_SALES" in ct_agg.columns:
                    fig_ct.add_trace(go.Bar(x=labels, y=ct_agg["TOTAL_SALES"], name="전체", marker_color="#636EFA"))
                if "FOOD_SALES" in ct_agg.columns:
                    fig_ct.add_trace(go.Bar(x=labels, y=ct_agg["FOOD_SALES"], name="식음료", marker_color="#EF553B"))
                if "COFFEE_SALES" in ct_agg.columns:
                    fig_ct.add_trace(go.Bar(x=labels, y=ct_agg["COFFEE_SALES"], name="커피", marker_color="#00CC96"))
                fig_ct.update_layout(title="시간대별 매출", barmode="group", height=230, margin=dict(l=25, r=10, t=30, b=25))
                st.plotly_chart(fig_ct, use_container_width=True, key="my_sales_time")
        except Exception:
            pass

    with tab_people:
        try:
            pop_time = load_population_time()
            pt_d = pop_time[(pop_time["DISTRICT_CODE"] == dc) & (pop_time["STANDARD_YEAR_MONTH"] == latest_month)]
            if not pt_d.empty:
                fig = population_flow_chart(pt_d, f"{district} 시간대별 유동인구")
                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True, key="my_pop_flow")
        except Exception:
            st.info("데이터 없음")
        try:
            pop_demo = load_population_demo()
            pd_d = pop_demo[(pop_demo["DISTRICT_CODE"] == dc) & (pop_demo["STANDARD_YEAR_MONTH"] == latest_month)]
            if not pd_d.empty:
                fig = population_pyramid(pd_d, f"{district} 인구 피라미드")
                fig.update_layout(height=270)
                st.plotly_chart(fig, use_container_width=True, key="my_pop_pyramid")
        except Exception:
            pass

    with tab_estate:
        try:
            re = load_realestate()
            re_d = re[(re["BJD_CODE"].astype(str).str[:8] == dc) & (re["REGION_LEVEL"] == "emd")]
            if not re_d.empty:
                fig = realestate_trend_chart(re_d, f"{district} 매매/전세 추이")
                fig.update_layout(height=270)
                st.plotly_chart(fig, use_container_width=True, key="my_re")
            else:
                re_sgg = re[(re["SGG"] == city) & (re["REGION_LEVEL"] == "sgg")]
                if not re_sgg.empty:
                    fig = realestate_trend_chart(re_sgg, f"{city}(시군구) 추이")
                    fig.update_layout(height=270)
                    st.plotly_chart(fig, use_container_width=True, key="my_re_sgg")
                else:
                    st.info("부동산 데이터 없음")
        except Exception:
            st.info("부동산 데이터 로드 실패")

    with tab_finance:
        if not income_d.empty:
            fig = income_distribution_chart(income_d.iloc[0], f"{district} 소득 분포")
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True, key="my_income")
            fig = job_donut_chart(income_d.iloc[0], f"{district} 직업군 분포")
            fig.update_layout(height=250)
            st.plotly_chart(fig, use_container_width=True, key="my_job")
        else:
            st.info("소득 데이터 없음")

# ── 채팅 ──
page_context = f"인사이트 피드 - {sig['name']} {chg_prefix}{sig['composite']}점" if signals else "인사이트 피드"
render_chat_panel(current_tab="메인", selected_district=None, selected_month=None, page_context=page_context)
