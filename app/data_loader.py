"""
데이터 로딩 & 캐싱 모듈
전처리된 parquet 파일을 로드하고 Streamlit 캐시로 유지
"""
import json
import pandas as pd
import streamlit as st
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "processed_data"


@st.cache_data
def load_geojson():
    """법정동 GeoJSON 경계 로드"""
    with open(PROCESSED_DIR / "geo_boundaries.json", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_region_master():
    """지역 매핑 마스터 테이블"""
    return pd.read_parquet(PROCESSED_DIR / "region_master.parquet")


@st.cache_data
def load_income_agg():
    """자산소득 집계 (법정동 × 년월)"""
    return pd.read_parquet(PROCESSED_DIR / "income_agg.parquet")


@st.cache_data
def load_income_detail():
    """자산소득 상세 (법정동 × 년월 × 성별 × 연령대)"""
    return pd.read_parquet(PROCESSED_DIR / "income_detail.parquet")


@st.cache_data
def load_card_sales_agg():
    """카드매출 집계 (법정동 × 년월)"""
    return pd.read_parquet(PROCESSED_DIR / "card_sales_agg.parquet")


@st.cache_data
def load_card_sales_time():
    """카드매출 시간대별 (법정동 × 년월 × 주중주말 × 시간대)"""
    return pd.read_parquet(PROCESSED_DIR / "card_sales_time_agg.parquet")


@st.cache_data
def load_population_agg():
    """유동인구 집계 (법정동 × 년월)"""
    return pd.read_parquet(PROCESSED_DIR / "population_agg.parquet")


@st.cache_data
def load_population_time():
    """유동인구 시간대별 (법정동 × 년월 × 주중주말 × 시간대)"""
    return pd.read_parquet(PROCESSED_DIR / "population_time_agg.parquet")


@st.cache_data
def load_population_demo():
    """유동인구 인구통계별 (법정동 × 년월 × 성별 × 연령대)"""
    return pd.read_parquet(PROCESSED_DIR / "population_demo_agg.parquet")


@st.cache_data
def load_realestate():
    """리치고 부동산 시세"""
    return pd.read_parquet(PROCESSED_DIR / "realestate.parquet")


@st.cache_data
def load_richgo_population():
    """리치고 인구 구조"""
    return pd.read_parquet(PROCESSED_DIR / "richgo_population.parquet")


@st.cache_data
def load_richgo_fertility():
    """리치고 영유아/여성 비율"""
    return pd.read_parquet(PROCESSED_DIR / "richgo_fertility.parquet")


@st.cache_data
def load_ajd_new_install():
    """아정당 지역별 신규설치"""
    return pd.read_parquet(PROCESSED_DIR / "ajd_new_install.parquet")


@st.cache_data
def load_ajd_funnel():
    """아정당 퍼널 전환율"""
    return pd.read_parquet(PROCESSED_DIR / "ajd_funnel.parquet")


@st.cache_data
def load_ajd_channel():
    """아정당 채널 성과"""
    return pd.read_parquet(PROCESSED_DIR / "ajd_channel.parquet")


@st.cache_data
def load_ajd_rental():
    """아정당 렌탈 트렌드"""
    return pd.read_parquet(PROCESSED_DIR / "ajd_rental_trends.parquet")


@st.cache_data
def load_ajd_ga4():
    """아정당 GA4 마케팅"""
    return pd.read_parquet(PROCESSED_DIR / "ajd_ga4_marketing.parquet")


@st.cache_data
def load_code_master():
    """SPH 코드 마스터"""
    return pd.read_parquet(PROCESSED_DIR / "code_master.parquet")


def get_district_list():
    """법정동 목록 (시군구 > 법정동 형태)"""
    rm = load_region_master()
    rm["label"] = rm["city_kor"] + " " + rm["district_kor"]
    return rm.sort_values(["city_kor", "district_kor"])


def get_latest_year_month(df, col="STANDARD_YEAR_MONTH"):
    """가장 최근 년월 반환"""
    return df[col].max()


def filter_by_district(df, district_code, col="DISTRICT_CODE"):
    """법정동 코드로 필터"""
    return df[df[col] == str(district_code)]


def filter_by_year_month(df, year_month, col="STANDARD_YEAR_MONTH"):
    """년월로 필터"""
    return df[df[col] == year_month]
