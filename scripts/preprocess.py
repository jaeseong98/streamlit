"""
데이터 전처리 스크립트 — CSV 원본 → 경량 parquet 변환
1회 실행 후 processed_data/ 디렉토리에 결과 저장
"""
import os
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path

# ── 경로 설정 ──
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
OUT_DIR = BASE_DIR / "processed_data"
OUT_DIR.mkdir(exist_ok=True)

SPH_DIR = DATA_DIR / "SPH"
RICHGO_DIR = DATA_DIR / "리치고"
AJD_DIR = DATA_DIR / "아정당"

# ── 파일명 ↔ 실제 내용 매핑 (SPH 파일명이 뒤바뀌어 있음) ──
FILE_MAP = {
    "법정동마스터": SPH_DIR / "SPH_카드매출.csv",       # 실제: 법정동 마스터 + GeoJSON
    "자산소득":     SPH_DIR / "SPH_법정동_마스터.csv",   # 실제: 자산소득
    "코드마스터":   SPH_DIR / "SPH_자산소득.csv",       # 실제: 코드 마스터
    "카드매출":     SPH_DIR / "SPH_코드_마스터.csv",    # 실제: 카드매출
    "유동인구":     SPH_DIR / "SPH_유동인구.csv",       # 실제: 유동인구 (정상)
}


def step1_geojson():
    """법정동 마스터에서 GeoJSON 경계 추출 + 지역 매핑 테이블 생성"""
    print("=" * 60)
    print("[Step 1] GeoJSON 경계 + 지역 매핑 테이블 추출")
    print("=" * 60)

    fpath = FILE_MAP["법정동마스터"]
    print(f"  읽는 중: {fpath.name}")

    # 이 파일은 GeoJSON이 멀티라인이라 일반 CSV 파싱이 어려움
    # 전체 텍스트를 읽어서 직접 파싱
    raw = fpath.read_text(encoding="utf-8-sig")
    lines = raw.split("\n")

    header = lines[0].strip().split(",")
    print(f"  헤더: {header}")

    # 레코드 단위로 파싱 — DISTRICT_GEOM에 멀티라인 JSON이 들어있음
    records = []
    current_record = ""
    for line in lines[1:]:
        current_record += line
        # 레코드가 완성되었는지 확인: province_code로 시작하는 새 줄이면 이전 레코드 완료
        # GeoJSON은 { } 쌍이 맞으면 완료
        brace_open = current_record.count("{")
        brace_close = current_record.count("}")
        if brace_open > 0 and brace_open == brace_close:
            records.append(current_record)
            current_record = ""
        elif brace_open == 0 and "," in current_record and len(current_record.strip()) > 5:
            # GeoJSON 없는 레코드
            records.append(current_record)
            current_record = ""

    print(f"  파싱된 레코드 수: {len(records)}")

    features = []
    region_rows = []

    for rec in records:
        # 처음 9개 컬럼은 일반 데이터, 마지막이 DISTRICT_GEOM
        # CSV에서 첫 9개 필드를 추출
        parts = rec.split(",", 9)
        if len(parts) < 10:
            continue

        try:
            province_code = parts[0].strip().strip('"')
            city_code = parts[1].strip().strip('"')
            district_code = parts[2].strip().strip('"')
            province_kor = parts[3].strip().strip('"')
            city_kor = parts[4].strip().strip('"')
            district_kor = parts[5].strip().strip('"')
            province_eng = parts[6].strip().strip('"')
            city_eng = parts[7].strip().strip('"')
            district_eng = parts[8].strip().strip('"')
            geom_str = parts[9].strip().strip('"')
        except (IndexError, ValueError):
            continue

        if not district_code or not province_code:
            continue

        # 지역 매핑 테이블 행
        region_rows.append({
            "province_code": province_code,
            "city_code": city_code,
            "district_code": district_code,
            "province_kor": province_kor,
            "city_kor": city_kor,
            "district_kor": district_kor,
            "province_short": province_kor.replace("특별시", "").replace("광역시", "").replace("특별자치시", "").replace("특별자치도", ""),
        })

        # GeoJSON Feature 생성
        if geom_str and "{" in geom_str:
            try:
                geom = json.loads(geom_str)
                feature = {
                    "type": "Feature",
                    "properties": {
                        "district_code": district_code,
                        "city_code": city_code,
                        "province_code": province_code,
                        "name": f"{city_kor} {district_kor}",
                        "city_kor": city_kor,
                        "district_kor": district_kor,
                    },
                    "geometry": geom
                }
                features.append(feature)
            except json.JSONDecodeError:
                pass  # GeoJSON 파싱 실패 시 스킵

    # GeoJSON FeatureCollection 저장
    geojson = {"type": "FeatureCollection", "features": features}
    geo_path = OUT_DIR / "geo_boundaries.json"
    with open(geo_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    print(f"  ✅ GeoJSON 저장: {len(features)}개 법정동 경계 → {geo_path.name}")

    # 지역 매핑 테이블 저장
    region_df = pd.DataFrame(region_rows).drop_duplicates(subset=["district_code"])
    region_df.to_parquet(OUT_DIR / "region_master.parquet", index=False)
    print(f"  ✅ 지역 마스터 저장: {len(region_df)}개 법정동 → region_master.parquet")

    return region_df


def step2_income(region_df):
    """자산소득 데이터 집계"""
    print("\n" + "=" * 60)
    print("[Step 2] 자산소득 데이터 집계")
    print("=" * 60)

    fpath = FILE_MAP["자산소득"]
    print(f"  읽는 중: {fpath.name}")

    df = pd.read_csv(fpath, encoding="utf-8-sig", low_memory=False)
    print(f"  원본 행 수: {len(df):,}")

    # 개인 데이터만 (INCOME_TYPE=1)
    df = df[df["INCOME_TYPE"] == 1].copy()

    # 법정동 × 년월 × 성별 × 연령대별 가중평균 계산
    weight_col = "CUSTOMER_COUNT"
    value_cols = [
        "AVERAGE_INCOME", "MEDIAN_INCOME", "AVERAGE_HOUSEHOLD_INCOME",
        "AVERAGE_SCORE",
        "RATE_MODEL_GROUP_LARGE_COMPANY_EMPLOYEE",
        "RATE_MODEL_GROUP_GENERAL_EMPLOYEE",
        "RATE_MODEL_GROUP_PROFESSIONAL_EMPLOYEE",
        "RATE_MODEL_GROUP_EXECUTIVES",
        "RATE_MODEL_GROUP_GENERAL_SELF_EMPLOYED",
        "RATE_MODEL_GROUP_PROFESSIONAL_SELF_EMPLOYED",
        "RATE_MODEL_GROUP_OTHERS",
        "RATE_INCOME_UNDER_20M", "RATE_INCOME_20M_30M", "RATE_INCOME_30M_40M",
        "RATE_INCOME_40M_50M", "RATE_INCOME_50M_60M", "RATE_INCOME_60M_70M",
        "RATE_INCOME_OVER_70M",
        "RATE_SCORE1", "RATE_SCORE2", "RATE_SCORE3",
        "RATE_HIGHEND",
        "AVERAGE_ASSET_AMOUNT",
    ]

    # 존재하는 컬럼만 필터
    value_cols = [c for c in value_cols if c in df.columns]

    # 법정동 × 년월 단위로 가중평균 집계
    group_cols = ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE", "STANDARD_YEAR_MONTH"]

    agg_rows = []
    for keys, grp in df.groupby(group_cols):
        row = dict(zip(group_cols, keys))
        total_customers = grp[weight_col].sum()
        row["total_customers"] = total_customers

        if total_customers > 0:
            for vc in value_cols:
                if vc in grp.columns:
                    valid = grp[[vc, weight_col]].dropna(subset=[vc])
                    if len(valid) > 0:
                        row[vc] = np.average(valid[vc], weights=valid[weight_col])
                    else:
                        row[vc] = np.nan
        agg_rows.append(row)

    income_agg = pd.DataFrame(agg_rows)

    # DISTRICT_CODE를 문자열로
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        income_agg[col] = income_agg[col].astype(str)

    income_agg.to_parquet(OUT_DIR / "income_agg.parquet", index=False)
    print(f"  ✅ 자산소득 집계 저장: {len(income_agg):,}행 → income_agg.parquet")

    # 성별×연령대별 상세도 저장 (합성 인구 생성용)
    detail_cols = group_cols + ["GENDER", "AGE_GROUP", weight_col] + value_cols
    detail_cols = [c for c in detail_cols if c in df.columns]
    income_detail = df[detail_cols].copy()
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        income_detail[col] = income_detail[col].astype(str)
    income_detail.to_parquet(OUT_DIR / "income_detail.parquet", index=False)
    print(f"  ✅ 자산소득 상세 저장: {len(income_detail):,}행 → income_detail.parquet")


def step3_card_sales():
    """카드매출 데이터 집계 (chunked read — 파일이 1GB)"""
    print("\n" + "=" * 60)
    print("[Step 3] 카드매출 데이터 집계")
    print("=" * 60)

    fpath = FILE_MAP["카드매출"]
    print(f"  읽는 중 (chunked): {fpath.name}")

    sales_categories = [
        "FOOD", "COFFEE", "ENTERTAINMENT", "DEPARTMENT_STORE",
        "LARGE_DISCOUNT_STORE", "SMALL_RETAIL_STORE", "CLOTHING_ACCESSORIES",
        "SPORTS_CULTURE_LEISURE", "ACCOMMODATION", "TRAVEL", "BEAUTY",
        "HOME_LIFE_SERVICE", "EDUCATION_ACADEMY", "MEDICAL",
        "ELECTRONICS_FURNITURE", "CAR", "CAR_SERVICE_SUPPLIES",
        "GAS_STATION", "E_COMMERCE", "TOTAL"
    ]

    sales_cols = [f"{cat}_SALES" for cat in sales_categories]
    count_cols = [f"{cat}_COUNT" for cat in sales_categories]
    # CAR는 CAR_SALES / CAR_SALES_COUNT 형태 — 확인 필요

    group_cols = ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE", "STANDARD_YEAR_MONTH"]

    agg_dict = {}
    chunk_num = 0
    total_rows = 0

    for chunk in pd.read_csv(fpath, encoding="utf-8-sig", chunksize=200000, low_memory=False):
        chunk_num += 1
        total_rows += len(chunk)

        # 개인 카드만 (CARD_TYPE=1 또는 '1')
        chunk = chunk[chunk["CARD_TYPE"].astype(str) == "1"]

        # 존재하는 매출/건수 컬럼만 사용
        available_sales = [c for c in chunk.columns if c.endswith("_SALES")]
        available_counts = [c for c in chunk.columns if c.endswith("_COUNT")]
        agg_cols = available_sales + available_counts

        # 법정동 × 년월 집계
        grouped = chunk.groupby(group_cols)[agg_cols].sum()

        for idx, row in grouped.iterrows():
            key = idx
            if key not in agg_dict:
                agg_dict[key] = row.to_dict()
            else:
                for col in agg_cols:
                    agg_dict[key][col] = agg_dict[key].get(col, 0) + row[col]

        if chunk_num % 5 == 0:
            print(f"    chunk {chunk_num} 처리 완료 ({total_rows:,}행)")

    print(f"  총 {total_rows:,}행 처리 완료")

    # DataFrame으로 변환
    rows = []
    for key, vals in agg_dict.items():
        row = dict(zip(group_cols, key))
        row.update(vals)
        rows.append(row)

    card_agg = pd.DataFrame(rows)
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        card_agg[col] = card_agg[col].astype(str)

    card_agg.to_parquet(OUT_DIR / "card_sales_agg.parquet", index=False)
    print(f"  ✅ 카드매출 집계 저장: {len(card_agg):,}행 → card_sales_agg.parquet")

    # 시간대별 상세 집계도 (디지털 트윈용)
    print("  시간대별 상세 집계 중...")
    time_group_cols = ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE",
                       "STANDARD_YEAR_MONTH", "WEEKDAY_WEEKEND", "TIME_SLOT"]

    time_agg_dict = {}
    for chunk in pd.read_csv(fpath, encoding="utf-8-sig", chunksize=200000, low_memory=False):
        chunk = chunk[chunk["CARD_TYPE"].astype(str) == "1"]
        available_sales = [c for c in chunk.columns if c.endswith("_SALES")]
        available_counts = [c for c in chunk.columns if c.endswith("_COUNT")]
        agg_cols = available_sales + available_counts

        grouped = chunk.groupby(time_group_cols)[agg_cols].sum()
        for idx, row in grouped.iterrows():
            key = idx
            if key not in time_agg_dict:
                time_agg_dict[key] = row.to_dict()
            else:
                for col in agg_cols:
                    time_agg_dict[key][col] = time_agg_dict[key].get(col, 0) + row[col]

    time_rows = []
    for key, vals in time_agg_dict.items():
        row = dict(zip(time_group_cols, key))
        row.update(vals)
        time_rows.append(row)

    card_time_agg = pd.DataFrame(time_rows)
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        card_time_agg[col] = card_time_agg[col].astype(str)

    card_time_agg.to_parquet(OUT_DIR / "card_sales_time_agg.parquet", index=False)
    print(f"  ✅ 카드매출 시간대별 저장: {len(card_time_agg):,}행 → card_sales_time_agg.parquet")


def step4_population():
    """유동인구 데이터 집계"""
    print("\n" + "=" * 60)
    print("[Step 4] 유동인구 데이터 집계")
    print("=" * 60)

    fpath = FILE_MAP["유동인구"]
    print(f"  읽는 중: {fpath.name}")

    df = pd.read_csv(fpath, encoding="utf-8-sig", low_memory=False)
    print(f"  원본 행 수: {len(df):,}")

    pop_cols = ["RESIDENTIAL_POPULATION", "WORKING_POPULATION", "VISITING_POPULATION"]
    group_cols = ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE", "STANDARD_YEAR_MONTH"]

    # A: 법정동 × 년월 총합
    pop_agg = df.groupby(group_cols)[pop_cols].sum().reset_index()
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        pop_agg[col] = pop_agg[col].astype(str)
    pop_agg.to_parquet(OUT_DIR / "population_agg.parquet", index=False)
    print(f"  ✅ 유동인구 집계 저장: {len(pop_agg):,}행 → population_agg.parquet")

    # B: 법정동 × 년월 × 시간대 × 주중주말 (디지털 트윈용)
    time_group = group_cols + ["WEEKDAY_WEEKEND", "TIME_SLOT"]
    pop_time = df.groupby(time_group)[pop_cols].sum().reset_index()
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        pop_time[col] = pop_time[col].astype(str)
    pop_time.to_parquet(OUT_DIR / "population_time_agg.parquet", index=False)
    print(f"  ✅ 유동인구 시간대별 저장: {len(pop_time):,}행 → population_time_agg.parquet")

    # C: 법정동 × 년월 × 성별 × 연령대 (인구 피라미드용)
    demo_group = group_cols + ["GENDER", "AGE_GROUP"]
    pop_demo = df.groupby(demo_group)[pop_cols].sum().reset_index()
    for col in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        pop_demo[col] = pop_demo[col].astype(str)
    pop_demo.to_parquet(OUT_DIR / "population_demo_agg.parquet", index=False)
    print(f"  ✅ 유동인구 인구통계별 저장: {len(pop_demo):,}행 → population_demo_agg.parquet")


def step5_richgo():
    """리치고 데이터 변환"""
    print("\n" + "=" * 60)
    print("[Step 5] 리치고 데이터 변환")
    print("=" * 60)

    # 부동산 시세
    realestate = pd.read_csv(RICHGO_DIR / "리치고_아파트_매매전세_시세.csv", encoding="utf-8-sig")
    realestate["BJD_CODE"] = realestate["BJD_CODE"].astype(str)
    realestate.to_parquet(OUT_DIR / "realestate.parquet", index=False)
    print(f"  ✅ 부동산 시세: {len(realestate):,}행 → realestate.parquet")

    # 인구 구조
    pop_age = pd.read_csv(RICHGO_DIR / "리치고_성별_연령별_인구수.csv", encoding="utf-8-sig")
    pop_age["BJD_CODE"] = pop_age["BJD_CODE"].astype(str)
    pop_age.to_parquet(OUT_DIR / "richgo_population.parquet", index=False)
    print(f"  ✅ 인구 구조: {len(pop_age):,}행 → richgo_population.parquet")

    # 영유아/여성 비율
    fertility = pd.read_csv(RICHGO_DIR / "리치고_5세미만_대비_2040여성_인구.csv", encoding="utf-8-sig")
    fertility["BJD_CODE"] = fertility["BJD_CODE"].astype(str)
    fertility.to_parquet(OUT_DIR / "richgo_fertility.parquet", index=False)
    print(f"  ✅ 영유아/여성: {len(fertility):,}행 → richgo_fertility.parquet")


def step6_ajungdang():
    """아정당 데이터 변환"""
    print("\n" + "=" * 60)
    print("[Step 6] 아정당 데이터 변환")
    print("=" * 60)

    ajd_files = {
        "contract_regional": "V01_MONTHLY_REGIONAL_CONTRACT_STATS.csv",
        "bundle_patterns": "V02_SERVICE_BUNDLE_PATTERNS.csv",
        "funnel": "V03_CONTRACT_FUNNEL_CONVERSION.csv",
        "channel": "V04_CHANNEL_CONTRACT_PERFORMANCE.csv",
        "new_install": "V05_REGIONAL_NEW_INSTALL.csv",
        "rental_trends": "V06_RENTAL_CATEGORY_TRENDS.csv",
        "ga4_marketing": "V07_GA4_MARKETING_ATTRIBUTION.csv",
        "ga4_device": "V08_GA4_DEVICE_STATS.csv",
        "call_stats": "V09_MONTHLY_CALL_STATS.csv",
        "call_hourly": "V10_HOURLY_CALL_DISTRIBUTION.csv",
        "call_conversion": "V11_CALL_TO_CONTRACT_CONVERSION.csv",
    }

    for name, fname in ajd_files.items():
        fpath = AJD_DIR / fname
        df = pd.read_csv(fpath, encoding="utf-8-sig", low_memory=False)
        out_name = f"ajd_{name}.parquet"
        df.to_parquet(OUT_DIR / out_name, index=False)
        print(f"  ✅ {fname}: {len(df):,}행 → {out_name}")


def step7_code_master():
    """코드 마스터 저장"""
    print("\n" + "=" * 60)
    print("[Step 7] 코드 마스터 저장")
    print("=" * 60)

    fpath = FILE_MAP["코드마스터"]
    df = pd.read_csv(fpath, encoding="utf-8-sig")
    df.to_parquet(OUT_DIR / "code_master.parquet", index=False)
    print(f"  ✅ 코드 마스터: {len(df):,}행 → code_master.parquet")


if __name__ == "__main__":
    print("🚀 데이터 전처리 시작")
    print(f"   데이터 소스: {DATA_DIR}")
    print(f"   출력 디렉토리: {OUT_DIR}")
    print()

    region_df = step1_geojson()
    step2_income(region_df)
    step3_card_sales()
    step4_population()
    step5_richgo()
    step6_ajungdang()
    step7_code_master()

    print("\n" + "=" * 60)
    print("✅ 전처리 완료!")
    print("=" * 60)
    # 결과 파일 목록
    for f in sorted(OUT_DIR.iterdir()):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:40s} {size_mb:8.2f} MB")
