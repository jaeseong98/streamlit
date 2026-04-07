"""나머지 전처리 — 카드매출 시간대별, 유동인구, 리치고, 아정당, 코드마스터"""
import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
OUT_DIR = BASE_DIR / "processed_data"
SPH_DIR = DATA_DIR / "SPH"
RICHGO_DIR = DATA_DIR / "리치고"
AJD_DIR = DATA_DIR / "아정당"

# 이미 있는 파일은 스킵
existing = {f.name for f in OUT_DIR.iterdir()}

# ── 카드매출 시간대별 ──
if "card_sales_time_agg.parquet" not in existing:
    print("[1] 카드매출 시간대별 집계 중...")
    fpath = SPH_DIR / "SPH_코드_마스터.csv"  # 실제: 카드매출
    time_group_cols = ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE",
                       "STANDARD_YEAR_MONTH", "WEEKDAY_WEEKEND", "TIME_SLOT"]
    agg_dict = {}
    total = 0
    for chunk in pd.read_csv(fpath, encoding="utf-8-sig", chunksize=200000, low_memory=False):
        chunk = chunk[chunk["CARD_TYPE"].astype(str) == "1"]
        sales_cols = [c for c in chunk.columns if c.endswith("_SALES") or c.endswith("_COUNT")]
        grouped = chunk.groupby(time_group_cols)[sales_cols].sum()
        for idx, row in grouped.iterrows():
            if idx not in agg_dict:
                agg_dict[idx] = row.to_dict()
            else:
                for c in sales_cols:
                    agg_dict[idx][c] = agg_dict[idx].get(c, 0) + row[c]
        total += len(chunk)
    print(f"  {total:,}행 처리")
    rows = [dict(zip(time_group_cols, k), **v) for k, v in agg_dict.items()]
    df = pd.DataFrame(rows)
    for c in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        df[c] = df[c].astype(str)
    df.to_parquet(OUT_DIR / "card_sales_time_agg.parquet", index=False)
    print(f"  ✅ {len(df):,}행 저장")
else:
    print("[1] card_sales_time_agg.parquet 이미 존재 — 스킵")

# ── 유동인구 ──
if "population_agg.parquet" not in existing:
    print("\n[2] 유동인구 집계 중...")
    fpath = SPH_DIR / "SPH_유동인구.csv"
    df = pd.read_csv(fpath, encoding="utf-8-sig", low_memory=False)
    pop_cols = ["RESIDENTIAL_POPULATION", "WORKING_POPULATION", "VISITING_POPULATION"]
    group_cols = ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE", "STANDARD_YEAR_MONTH"]

    pop_agg = df.groupby(group_cols)[pop_cols].sum().reset_index()
    for c in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        pop_agg[c] = pop_agg[c].astype(str)
    pop_agg.to_parquet(OUT_DIR / "population_agg.parquet", index=False)
    print(f"  ✅ {len(pop_agg):,}행 → population_agg.parquet")

    time_group = group_cols + ["WEEKDAY_WEEKEND", "TIME_SLOT"]
    pop_time = df.groupby(time_group)[pop_cols].sum().reset_index()
    for c in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        pop_time[c] = pop_time[c].astype(str)
    pop_time.to_parquet(OUT_DIR / "population_time_agg.parquet", index=False)
    print(f"  ✅ {len(pop_time):,}행 → population_time_agg.parquet")

    demo_group = group_cols + ["GENDER", "AGE_GROUP"]
    pop_demo = df.groupby(demo_group)[pop_cols].sum().reset_index()
    for c in ["PROVINCE_CODE", "CITY_CODE", "DISTRICT_CODE"]:
        pop_demo[c] = pop_demo[c].astype(str)
    pop_demo.to_parquet(OUT_DIR / "population_demo_agg.parquet", index=False)
    print(f"  ✅ {len(pop_demo):,}행 → population_demo_agg.parquet")
else:
    print("[2] population_agg.parquet 이미 존재 — 스킵")

# ── 리치고 ──
for name, fname in [("realestate", "리치고_아파트_매매전세_시세.csv"),
                     ("richgo_population", "리치고_성별_연령별_인구수.csv"),
                     ("richgo_fertility", "리치고_5세미만_대비_2040여성_인구.csv")]:
    out_name = f"{name}.parquet"
    if out_name not in existing:
        print(f"\n[리치고] {fname} → {out_name}")
        df = pd.read_csv(RICHGO_DIR / fname, encoding="utf-8-sig")
        if "BJD_CODE" in df.columns:
            df["BJD_CODE"] = df["BJD_CODE"].astype(str)
        df.to_parquet(OUT_DIR / out_name, index=False)
        print(f"  ✅ {len(df):,}행")

# ── 아정당 ──
ajd_files = {
    "ajd_contract_regional": "V01_MONTHLY_REGIONAL_CONTRACT_STATS.csv",
    "ajd_bundle_patterns": "V02_SERVICE_BUNDLE_PATTERNS.csv",
    "ajd_funnel": "V03_CONTRACT_FUNNEL_CONVERSION.csv",
    "ajd_channel": "V04_CHANNEL_CONTRACT_PERFORMANCE.csv",
    "ajd_new_install": "V05_REGIONAL_NEW_INSTALL.csv",
    "ajd_rental_trends": "V06_RENTAL_CATEGORY_TRENDS.csv",
    "ajd_ga4_marketing": "V07_GA4_MARKETING_ATTRIBUTION.csv",
    "ajd_ga4_device": "V08_GA4_DEVICE_STATS.csv",
    "ajd_call_stats": "V09_MONTHLY_CALL_STATS.csv",
    "ajd_call_hourly": "V10_HOURLY_CALL_DISTRIBUTION.csv",
    "ajd_call_conversion": "V11_CALL_TO_CONTRACT_CONVERSION.csv",
}
for name, fname in ajd_files.items():
    out_name = f"{name}.parquet"
    if out_name not in existing:
        print(f"\n[아정당] {fname} → {out_name}")
        df = pd.read_csv(AJD_DIR / fname, encoding="utf-8-sig", low_memory=False)
        df.to_parquet(OUT_DIR / out_name, index=False)
        print(f"  ✅ {len(df):,}행")

# ── 코드마스터 ──
if "code_master.parquet" not in existing:
    print("\n[코드마스터]")
    df = pd.read_csv(SPH_DIR / "SPH_자산소득.csv", encoding="utf-8-sig")
    df.to_parquet(OUT_DIR / "code_master.parquet", index=False)
    print(f"  ✅ {len(df):,}행")

print("\n" + "=" * 50)
print("전처리 완료! 파일 목록:")
for f in sorted(OUT_DIR.iterdir()):
    print(f"  {f.name:40s} {f.stat().st_size / 1024 / 1024:.2f} MB")
