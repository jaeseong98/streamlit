"""
뉴스 엔진 — 데이터 변화에서 자동으로 인사이트 뉴스 생성
"""
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path


@st.cache_data
def generate_news_items():
    """전체 데이터에서 주요 변화/이벤트를 뉴스 아이템으로 생성"""
    from data_loader import (
        load_population_agg, load_card_sales_agg, load_income_agg,
        load_region_master, load_realestate, load_ajd_new_install
    )

    news = []
    region_master = load_region_master()
    pop_agg = load_population_agg()
    card_agg = load_card_sales_agg()

    # 데이터 있는 법정동만
    data_districts = set(pop_agg["DISTRICT_CODE"].unique())
    rm = region_master[region_master["district_code"].isin(data_districts)].copy()
    name_map = rm.set_index("district_code").apply(
        lambda r: f"{r['city_kor']} {r['district_kor']}", axis=1
    ).to_dict()

    months = sorted(pop_agg["STANDARD_YEAR_MONTH"].unique())

    def fmt_month(m):
        s = str(m)
        return f"{s[:4]}.{s[4:6]}"

    # ═══════════════════════════════════════
    # 1. 유동인구 급증/급감 감지
    # ═══════════════════════════════════════
    if len(months) >= 2:
        prev_m, curr_m = months[-2], months[-1]
        pop_curr = pop_agg[pop_agg["STANDARD_YEAR_MONTH"] == curr_m].copy()
        pop_prev = pop_agg[pop_agg["STANDARD_YEAR_MONTH"] == prev_m].copy()

        pop_curr["total"] = pop_curr["RESIDENTIAL_POPULATION"] + pop_curr["WORKING_POPULATION"] + pop_curr["VISITING_POPULATION"]
        pop_prev["total"] = pop_prev["RESIDENTIAL_POPULATION"] + pop_prev["WORKING_POPULATION"] + pop_prev["VISITING_POPULATION"]

        curr_dict = pop_curr.set_index("DISTRICT_CODE")["total"].to_dict()
        prev_dict = pop_prev.set_index("DISTRICT_CODE")["total"].to_dict()

        changes = []
        for dc in curr_dict:
            if dc in prev_dict and prev_dict[dc] > 0:
                rate = (curr_dict[dc] - prev_dict[dc]) / prev_dict[dc] * 100
                changes.append((dc, rate, curr_dict[dc]))

        changes.sort(key=lambda x: x[1], reverse=True)

        # 상위 급증
        for dc, rate, total in changes[:3]:
            if rate > 5:
                news.append({
                    "type": "pop_surge",
                    "icon": "📈",
                    "tag": "유동인구",
                    "tag_color": "#4CAF50",
                    "title": f"{name_map.get(dc, dc)} 유동인구 급증",
                    "summary": f"전월 대비 +{rate:.1f}% 증가 (총 {total:,.0f}명)",
                    "month": fmt_month(curr_m),
                    "district_code": dc,
                    "detail_type": "population",
                    "severity": "high" if rate > 15 else "medium",
                })

        # 하위 급감
        for dc, rate, total in changes[-3:]:
            if rate < -5:
                news.append({
                    "type": "pop_drop",
                    "icon": "📉",
                    "tag": "유동인구",
                    "tag_color": "#f44336",
                    "title": f"{name_map.get(dc, dc)} 유동인구 감소",
                    "summary": f"전월 대비 {rate:.1f}% 감소 (총 {total:,.0f}명)",
                    "month": fmt_month(curr_m),
                    "district_code": dc,
                    "detail_type": "population",
                    "severity": "high" if rate < -15 else "medium",
                })

    # ═══════════════════════════════════════
    # 2. 카드매출 변화 감지
    # ═══════════════════════════════════════
    card_months = sorted(card_agg["STANDARD_YEAR_MONTH"].unique())
    if len(card_months) >= 2:
        prev_m, curr_m = card_months[-2], card_months[-1]
        card_curr = card_agg[card_agg["STANDARD_YEAR_MONTH"] == curr_m].set_index("DISTRICT_CODE")
        card_prev = card_agg[card_agg["STANDARD_YEAR_MONTH"] == prev_m].set_index("DISTRICT_CODE")

        if "TOTAL_SALES" in card_curr.columns:
            changes = []
            for dc in card_curr.index:
                if dc in card_prev.index:
                    curr_val = card_curr.loc[dc, "TOTAL_SALES"]
                    prev_val = card_prev.loc[dc, "TOTAL_SALES"]
                    if prev_val > 0:
                        rate = (curr_val - prev_val) / prev_val * 100
                        changes.append((dc, rate, curr_val))

            changes.sort(key=lambda x: x[1], reverse=True)

            for dc, rate, total in changes[:3]:
                if rate > 5:
                    news.append({
                        "type": "sales_surge",
                        "icon": "💰",
                        "tag": "카드매출",
                        "tag_color": "#FF9800",
                        "title": f"{name_map.get(dc, dc)} 매출 급증",
                        "summary": f"전월 대비 +{rate:.1f}% ({total/1e8:,.1f}억원)",
                        "month": fmt_month(curr_m),
                        "district_code": dc,
                        "detail_type": "sales",
                        "severity": "high" if rate > 20 else "medium",
                    })

            for dc, rate, total in changes[-2:]:
                if rate < -10:
                    news.append({
                        "type": "sales_drop",
                        "icon": "💸",
                        "tag": "카드매출",
                        "tag_color": "#f44336",
                        "title": f"{name_map.get(dc, dc)} 매출 급감",
                        "summary": f"전월 대비 {rate:.1f}% ({total/1e8:,.1f}억원)",
                        "month": fmt_month(curr_m),
                        "district_code": dc,
                        "detail_type": "sales",
                        "severity": "high",
                    })

            # 커피 매출 트렌드
            if "COFFEE_SALES" in card_curr.columns:
                coffee_changes = []
                for dc in card_curr.index:
                    if dc in card_prev.index:
                        curr_c = card_curr.loc[dc, "COFFEE_SALES"]
                        prev_c = card_prev.loc[dc, "COFFEE_SALES"]
                        if prev_c > 0:
                            rate = (curr_c - prev_c) / prev_c * 100
                            coffee_changes.append((dc, rate, curr_c))

                coffee_changes.sort(key=lambda x: x[1], reverse=True)
                if coffee_changes and coffee_changes[0][1] > 10:
                    dc, rate, val = coffee_changes[0]
                    news.append({
                        "type": "coffee_trend",
                        "icon": "☕",
                        "tag": "트렌드",
                        "tag_color": "#795548",
                        "title": f"{name_map.get(dc, dc)} 카페 매출 상승",
                        "summary": f"커피 매출 +{rate:.1f}% — 상권 활성화 시그널",
                        "month": fmt_month(curr_m),
                        "district_code": dc,
                        "detail_type": "sales",
                        "severity": "low",
                    })

    # ═══════════════════════════════════════
    # 3. 방문인구 vs 거주인구 비율 변화 (상권 성장 시그널)
    # ═══════════════════════════════════════
    if len(months) >= 2:
        curr_m = months[-1]
        pop_curr = pop_agg[pop_agg["STANDARD_YEAR_MONTH"] == curr_m]

        for _, row in pop_curr.iterrows():
            dc = row["DISTRICT_CODE"]
            total = row["RESIDENTIAL_POPULATION"] + row["WORKING_POPULATION"] + row["VISITING_POPULATION"]
            if total > 0:
                visit_ratio = row["VISITING_POPULATION"] / total
                if visit_ratio > 0.4:
                    news.append({
                        "type": "visit_hotspot",
                        "icon": "🔥",
                        "tag": "핫플 시그널",
                        "tag_color": "#E91E63",
                        "title": f"{name_map.get(dc, dc)} 방문객 비중 {visit_ratio*100:.0f}%",
                        "summary": f"방문인구 비중이 높아 상권 활성화 지역",
                        "month": fmt_month(curr_m),
                        "district_code": dc,
                        "detail_type": "population",
                        "severity": "medium",
                    })

    # ═══════════════════════════════════════
    # 4. 부동산 시세 변화
    # ═══════════════════════════════════════
    try:
        realestate = load_realestate()
        re_emd = realestate[realestate["REGION_LEVEL"] == "emd"].copy()
        re_months = sorted(re_emd["YYYYMMDD"].unique())
        if len(re_months) >= 2:
            prev_m, curr_m = re_months[-2], re_months[-1]
            re_curr = re_emd[re_emd["YYYYMMDD"] == curr_m]
            re_prev = re_emd[re_emd["YYYYMMDD"] == prev_m]

            for _, row in re_curr.iterrows():
                bjd = str(row["BJD_CODE"])
                dc = bjd[:8]
                name = f"{row.get('SGG', '')} {row.get('EMD', '')}"
                prev_rows = re_prev[re_prev["BJD_CODE"].astype(str) == bjd]
                if not prev_rows.empty and row["MEME_PRICE_PER_SUPPLY_PYEONG"] > 0:
                    prev_price = prev_rows["MEME_PRICE_PER_SUPPLY_PYEONG"].values[0]
                    if prev_price > 0:
                        rate = (row["MEME_PRICE_PER_SUPPLY_PYEONG"] - prev_price) / prev_price * 100
                        if abs(rate) > 2:
                            news.append({
                                "type": "realestate",
                                "icon": "🏠" if rate > 0 else "🏚️",
                                "tag": "부동산",
                                "tag_color": "#9C27B0",
                                "title": f"{name.strip()} 매매가 {'상승' if rate > 0 else '하락'}",
                                "summary": f"평단가 {rate:+.1f}% ({row['MEME_PRICE_PER_SUPPLY_PYEONG']:,.0f}만원/평)",
                                "month": str(curr_m)[:7],
                                "district_code": dc,
                                "detail_type": "realestate",
                                "severity": "high" if abs(rate) > 5 else "medium",
                            })
    except Exception:
        pass

    # ═══════════════════════════════════════
    # 5. 아정당 신규 설치 변화
    # ═══════════════════════════════════════
    try:
        install = load_ajd_new_install()
        inst_months = sorted(install["YEAR_MONTH"].unique())
        if len(inst_months) >= 2:
            prev_m, curr_m = inst_months[-2], inst_months[-1]
            inst_curr = install[install["YEAR_MONTH"] == curr_m].groupby("INSTALL_CITY")["OPEN_COUNT"].sum()
            inst_prev = install[install["YEAR_MONTH"] == prev_m].groupby("INSTALL_CITY")["OPEN_COUNT"].sum()

            for city in inst_curr.index:
                if city in inst_prev.index and inst_prev[city] > 0:
                    rate = (inst_curr[city] - inst_prev[city]) / inst_prev[city] * 100
                    if rate > 20:
                        news.append({
                            "type": "install_surge",
                            "icon": "🌐",
                            "tag": "신규설치",
                            "tag_color": "#2196F3",
                            "title": f"{city} 인터넷 신규설치 급증",
                            "summary": f"+{rate:.0f}% ({inst_curr[city]:,.0f}건) — 전입 수요 증가",
                            "month": str(curr_m)[:7],
                            "district_code": None,
                            "detail_type": "install",
                            "severity": "medium",
                        })
    except Exception:
        pass

    # severity 순으로 정렬 (high > medium > low)
    severity_order = {"high": 0, "medium": 1, "low": 2}
    news.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 2))

    return news


def render_news_card(item, index):
    """사이드바용 뉴스 카드 HTML 렌더링"""
    severity_border = {
        "high": "#f44336",
        "medium": "#FF9800",
        "low": "#4CAF50",
    }
    border_color = severity_border.get(item.get("severity", "low"), "#9E9E9E")

    html = f"""
    <div style="
        border-left: 4px solid {border_color};
        background: #1E1E1E;
        padding: 10px 12px;
        margin-bottom: 8px;
        border-radius: 0 8px 8px 0;
        cursor: pointer;
        transition: background 0.2s;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="
                background: {item['tag_color']};
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: 600;
            ">{item['tag']}</span>
            <span style="color:#888; font-size:11px;">{item['month']}</span>
        </div>
        <div style="font-size:14px; font-weight:600; color:#E0E0E0; margin-bottom:4px;">
            {item['icon']} {item['title']}
        </div>
        <div style="font-size:12px; color:#9E9E9E;">
            {item['summary']}
        </div>
    </div>
    """
    return html


def render_detail_panel(item):
    """오른쪽 상세 패널 렌더링"""
    from data_loader import (
        load_population_agg, load_population_time, load_card_sales_agg,
        load_card_sales_time, load_income_agg, load_realestate, load_region_master
    )
    from charts import (
        population_flow_chart, spending_radar_chart,
        realestate_trend_chart, income_distribution_chart
    )

    dc = item.get("district_code")
    detail_type = item.get("detail_type", "population")

    st.markdown(f"### {item['icon']} {item['title']}")
    st.caption(f"기준: {item['month']}")
    st.info(item['summary'])

    if not dc:
        st.markdown("상세 데이터를 표시할 법정동 정보가 없습니다.")
        return

    region_master = load_region_master()
    rm_row = region_master[region_master["district_code"] == dc]
    if not rm_row.empty:
        city = rm_row.iloc[0]["city_kor"]
        district = rm_row.iloc[0]["district_kor"]
        st.markdown(f"**위치**: {city} {district}")

    st.divider()

    # 유동인구 상세
    if detail_type == "population":
        pop_agg = load_population_agg()
        pop_district = pop_agg[pop_agg["DISTRICT_CODE"] == dc].copy()

        if not pop_district.empty:
            pop_district["total"] = (pop_district["RESIDENTIAL_POPULATION"]
                                     + pop_district["WORKING_POPULATION"]
                                     + pop_district["VISITING_POPULATION"])

            col1, col2, col3 = st.columns(3)
            latest = pop_district[pop_district["STANDARD_YEAR_MONTH"] == pop_district["STANDARD_YEAR_MONTH"].max()]
            if not latest.empty:
                with col1:
                    st.metric("거주인구", f"{latest['RESIDENTIAL_POPULATION'].values[0]:,.0f}")
                with col2:
                    st.metric("직장인구", f"{latest['WORKING_POPULATION'].values[0]:,.0f}")
                with col3:
                    st.metric("방문인구", f"{latest['VISITING_POPULATION'].values[0]:,.0f}")

            # 추이 차트
            import plotly.graph_objects as go
            months_sorted = sorted(pop_district["STANDARD_YEAR_MONTH"].unique())
            month_labels = [f"{str(m)[:4]}.{str(m)[4:]}" for m in months_sorted]
            totals = [pop_district[pop_district["STANDARD_YEAR_MONTH"] == m]["total"].values[0]
                      for m in months_sorted if len(pop_district[pop_district["STANDARD_YEAR_MONTH"] == m]) > 0]

            fig = go.Figure(go.Scatter(
                x=month_labels[:len(totals)], y=totals,
                mode="lines+markers", line=dict(color="#636EFA", width=2),
                fill="tozeroy", fillcolor="rgba(99,110,250,0.1)"
            ))
            fig.update_layout(title="유동인구 월별 추이", height=300, xaxis_title="", yaxis_title="명")
            st.plotly_chart(fig, use_container_width=True, key=f"pop_trend_{dc}")

        # 시간대별
        try:
            pop_time = load_population_time()
            latest_month = pop_time["STANDARD_YEAR_MONTH"].max()
            pt_district = pop_time[
                (pop_time["DISTRICT_CODE"] == dc) &
                (pop_time["STANDARD_YEAR_MONTH"] == latest_month)
            ]
            if not pt_district.empty:
                st.plotly_chart(
                    population_flow_chart(pt_district, "시간대별 유동인구"),
                    use_container_width=True, key=f"pop_flow_{dc}"
                )
        except Exception:
            pass

    # 매출 상세
    elif detail_type == "sales":
        card_agg = load_card_sales_agg()
        card_district = card_agg[card_agg["DISTRICT_CODE"] == dc].copy()

        if not card_district.empty and "TOTAL_SALES" in card_district.columns:
            latest = card_district[card_district["STANDARD_YEAR_MONTH"] == card_district["STANDARD_YEAR_MONTH"].max()]

            col1, col2 = st.columns(2)
            with col1:
                if not latest.empty:
                    st.metric("월 총매출", f"{latest['TOTAL_SALES'].values[0]/1e8:,.1f}억원")
            with col2:
                if "COFFEE_SALES" in latest.columns and not latest.empty:
                    st.metric("커피 매출", f"{latest['COFFEE_SALES'].values[0]/1e4:,.0f}만원")

            # 레이더 차트
            if not latest.empty:
                st.plotly_chart(
                    spending_radar_chart(latest.iloc[0], "업종별 매출 비중"),
                    use_container_width=True, key=f"radar_{dc}"
                )

            # 추이
            import plotly.graph_objects as go
            months_sorted = sorted(card_district["STANDARD_YEAR_MONTH"].unique())
            month_labels = [f"{str(m)[:4]}.{str(m)[4:]}" for m in months_sorted]
            totals = [card_district[card_district["STANDARD_YEAR_MONTH"] == m]["TOTAL_SALES"].values[0]
                      for m in months_sorted
                      if len(card_district[card_district["STANDARD_YEAR_MONTH"] == m]) > 0]

            fig = go.Figure(go.Bar(
                x=month_labels[:len(totals)], y=[t/1e8 for t in totals],
                marker_color="#FF9800"
            ))
            fig.update_layout(title="월별 카드매출 추이", height=300, yaxis_title="억원")
            st.plotly_chart(fig, use_container_width=True, key=f"sales_trend_{dc}")

    # 부동산 상세
    elif detail_type == "realestate":
        try:
            realestate = load_realestate()
            re_district = realestate[
                (realestate["BJD_CODE"].astype(str).str[:8] == dc) &
                (realestate["REGION_LEVEL"] == "emd")
            ]
            if not re_district.empty:
                st.plotly_chart(
                    realestate_trend_chart(re_district, "매매/전세 평단가 추이"),
                    use_container_width=True, key=f"re_trend_{dc}"
                )
        except Exception:
            st.info("부동산 데이터 없음")

    # 설치 상세
    elif detail_type == "install":
        st.markdown("아정당 신규 설치 데이터는 시군구 단위입니다.")
        try:
            from data_loader import load_ajd_new_install
            install = load_ajd_new_install()
            import plotly.graph_objects as go

            # 전체 시도별 월별 추이
            monthly = install.groupby("YEAR_MONTH")["OPEN_COUNT"].sum().reset_index()
            monthly = monthly.sort_values("YEAR_MONTH")
            labels = [f"{str(m)[:7]}" for m in monthly["YEAR_MONTH"]]

            fig = go.Figure(go.Bar(
                x=labels, y=monthly["OPEN_COUNT"],
                marker_color="#2196F3"
            ))
            fig.update_layout(title="전국 월별 신규설치 건수", height=300, yaxis_title="건")
            st.plotly_chart(fig, use_container_width=True, key="install_trend")
        except Exception:
            pass
