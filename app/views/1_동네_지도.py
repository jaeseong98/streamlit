"""
탭 1: 동네 지도 — 서울 법정동 코로플레스 맵
데이터 범위: 중구, 영등포구, 서초구 (118개 법정동)
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_loader import (
    load_geojson, load_region_master, load_population_agg,
    load_card_sales_agg, load_income_agg
)
from scoring import calc_hotplace_score, normalize_series, calc_purchasing_power
from chat_ui import render_chat_panel


st.title("🗺️ 동네 지도")
st.caption("데이터 범위: 서울 중구 · 영등포구 · 서초구 (118개 법정동)")

# ── 데이터 로드 ──
try:
    geojson_full = load_geojson()
    region_master = load_region_master()
    pop_agg = load_population_agg()
    card_agg = load_card_sales_agg()
    income_agg = load_income_agg()
except Exception as e:
    st.error(f"데이터 로드 실패: {e}\n\n먼저 `python scripts/preprocess.py`를 실행해주세요.")
    st.stop()

# ── 데이터가 있는 법정동만 필터 ──
data_districts = set(pop_agg["DISTRICT_CODE"].unique())
region_with_data = region_master[region_master["district_code"].isin(data_districts)].copy()

# GeoJSON도 데이터 있는 법정동만 필터
geojson = {
    "type": "FeatureCollection",
    "features": [
        f for f in geojson_full["features"]
        if f["properties"]["district_code"] in data_districts
    ]
}

st.sidebar.header("지표 선택")
metric = st.sidebar.selectbox("색상 기준", [
    "종합 핫플 스코어",
    "유동인구 (총합)",
    "카드매출 (총합)",
    "구매력 스코어",
    "방문인구 증가율",
])

# ── 기준 년월 선택 ──
all_months = sorted(pop_agg["STANDARD_YEAR_MONTH"].unique(), reverse=True)
month_labels = [f"{str(m)[:4]}년 {str(m)[4:6]}월" for m in all_months]
selected_month_label = st.sidebar.selectbox("기준 년월", month_labels, index=0)
selected_month = all_months[month_labels.index(selected_month_label)]

st.caption(f"기준: {selected_month_label}")

# ── 지표 계산 ──
pop_latest = pop_agg[pop_agg["STANDARD_YEAR_MONTH"] == selected_month].copy()
card_latest = card_agg[card_agg["STANDARD_YEAR_MONTH"] == selected_month].copy()

# 지표 데이터 (데이터 있는 법정동만)
district_metrics = region_with_data[["district_code", "city_kor", "district_kor"]].copy()
district_metrics["name"] = district_metrics["city_kor"] + " " + district_metrics["district_kor"]

# 유동인구 총합
pop_total = pop_latest.copy()
pop_total["total_pop"] = (pop_total["RESIDENTIAL_POPULATION"]
                          + pop_total["WORKING_POPULATION"]
                          + pop_total["VISITING_POPULATION"])
pop_merged = pop_total.set_index("DISTRICT_CODE")["total_pop"]

# 카드매출 총합
if "TOTAL_SALES" in card_latest.columns:
    card_merged = card_latest.set_index("DISTRICT_CODE")["TOTAL_SALES"]
else:
    sales_cols = [c for c in card_latest.columns if c.endswith("_SALES")]
    card_latest["TOTAL_SALES"] = card_latest[sales_cols].sum(axis=1)
    card_merged = card_latest.set_index("DISTRICT_CODE")["TOTAL_SALES"]

# 구매력 스코어
purchasing = calc_purchasing_power(income_agg)

# 핫플 스코어
try:
    from data_loader import load_realestate, load_ajd_new_install
    realestate = load_realestate()
    install = load_ajd_new_install()
except Exception:
    realestate = pd.DataFrame()
    install = pd.DataFrame()

hotplace_df = calc_hotplace_score(pop_agg, card_agg, realestate, install, region_with_data)

# 머지
district_metrics = district_metrics.merge(
    hotplace_df[["DISTRICT_CODE", "hotplace_score", "visiting_growth"]],
    left_on="district_code", right_on="DISTRICT_CODE", how="left"
)
district_metrics["total_pop"] = district_metrics["district_code"].map(pop_merged)
district_metrics["total_sales"] = district_metrics["district_code"].map(card_merged)
district_metrics["purchasing_power"] = district_metrics["district_code"].map(purchasing)
district_metrics = district_metrics.fillna(0)

# 색상 기준
metric_col_map = {
    "종합 핫플 스코어": "hotplace_score",
    "유동인구 (총합)": "total_pop",
    "카드매출 (총합)": "total_sales",
    "구매력 스코어": "purchasing_power",
    "방문인구 증가율": "visiting_growth",
}
color_col = metric_col_map[metric]

# ── GeoJSON에 지표 주입 ──
district_dict = district_metrics.set_index("district_code")[color_col].to_dict()
name_dict = district_metrics.set_index("district_code")["name"].to_dict()
score_dict = district_metrics.set_index("district_code").get("hotplace_score", pd.Series(dtype=float)).to_dict()

for feature in geojson["features"]:
    dc = feature["properties"]["district_code"]
    feature["properties"]["metric_value"] = round(float(district_dict.get(dc, 0)), 1)
    feature["properties"]["display_name"] = name_dict.get(dc, dc)
    feature["properties"]["hotplace_score"] = round(float(score_dict.get(dc, 0)), 1)

# ── 지도 생성 ──
# 데이터 있는 3개 구 중심으로 줌
m = folium.Map(location=[37.5100, 126.9500], zoom_start=12, tiles="CartoDB positron")

choropleth = folium.Choropleth(
    geo_data=geojson,
    data=district_metrics,
    columns=["district_code", color_col],
    key_on="feature.properties.district_code",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name=metric,
    nan_fill_color="white"
).add_to(m)

# 툴팁
folium.GeoJsonTooltip(
    fields=["display_name", "metric_value", "hotplace_score"],
    aliases=["동네", f"{metric}", "핫플 스코어"],
    style="font-size: 14px;"
).add_to(choropleth.geojson)

# ── 렌더링 ──
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader(f"서울 법정동 — {metric}")
    map_data = st_folium(m, width=900, height=600, returned_objects=["last_object_clicked"])

with col2:
    st.subheader("📊 Top 10")
    top10 = district_metrics.nlargest(10, color_col)[["name", color_col]].reset_index(drop=True)
    top10.index = top10.index + 1
    top10.columns = ["동네", metric]
    st.dataframe(top10, use_container_width=True)

    st.subheader("📉 Bottom 10")
    has_value = district_metrics[district_metrics[color_col] > 0]
    if not has_value.empty:
        bottom10 = has_value.nsmallest(10, color_col)[["name", color_col]].reset_index(drop=True)
        bottom10.index = bottom10.index + 1
        bottom10.columns = ["동네", metric]
        st.dataframe(bottom10, use_container_width=True)

if map_data and map_data.get("last_object_clicked"):
    clicked = map_data["last_object_clicked"]
    st.info(f"클릭한 위치: {clicked.get('lat', ''):.4f}, {clicked.get('lng', ''):.4f} — '동네 프로파일' 탭에서 상세 분석을 확인하세요.")

# Build page context for chat panel
_top3 = district_metrics.nlargest(3, color_col)["name"].tolist()
_top3_names = ", ".join(_top3)
page_context = f"동네 지도 - 지표: {metric}, 기준: {selected_month_label}, 상위 동네: {_top3_names}"

render_chat_panel(current_tab="동네 지도", selected_district=None, selected_month=None, page_context=page_context)
