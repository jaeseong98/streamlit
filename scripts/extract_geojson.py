"""
법정동 마스터에서 GeoJSON 추출 — 멀티라인 CSV 특수 파싱
SPH_카드매출.csv (실제 내용: 법정동 마스터 + GeoJSON 경계)
"""
import json
import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR.parent / "data"
OUT_DIR = BASE_DIR / "processed_data"

fpath = DATA_DIR / "SPH" / "SPH_카드매출.csv"

print(f"읽는 중: {fpath}")
raw = fpath.read_text(encoding="utf-8-sig")

# 전략: GeoJSON 블록은 "{ 로 시작하고 }" 로 끝남
# 각 레코드는 "PROVINCE_CODE," 패턴으로 시작

# 먼저 헤더 분리
lines = raw.split("\n")
header = lines[0].strip()
body = "\n".join(lines[1:])

# 레코드 분리: 숫자코드로 시작하는 줄을 레코드 시작으로 인식
# 패턴: ^11, (시도코드 11로 시작)
record_pattern = re.compile(r'^(\d{2}),(\d{5}),(\d{8}),(.+?),(.+?),(.+?),(.+?),(.+?),(.+?),(.*)', re.DOTALL)

# 레코드 분리 — 새 레코드는 "숫자숫자," 로 시작
records = []
current = ""
for line in lines[1:]:
    stripped = line.strip()
    if not stripped:
        continue

    # 새 레코드 시작: 2자리 숫자로 시작하고 바로 쉼표
    if re.match(r'^\d{2},\d{5},\d{8},', stripped) and current:
        records.append(current)
        current = stripped
    else:
        current += "\n" + stripped

if current:
    records.append(current)

print(f"파싱된 레코드 수: {len(records)}")

features = []
region_rows = []

for rec in records:
    # 첫 9개 필드 추출 (마지막이 GeoJSON)
    # CSV에서 쉼표로 분리하되, GeoJSON 시작 전까지만
    match = re.match(r'^(\d+),(\d+),(\d+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),(.*)', rec, re.DOTALL)
    if not match:
        continue

    province_code = match.group(1)
    city_code = match.group(2)
    district_code = match.group(3)
    province_kor = match.group(4)
    city_kor = match.group(5)
    district_kor = match.group(6)
    province_eng = match.group(7)
    city_eng = match.group(8)
    district_eng = match.group(9)
    geom_str = match.group(10).strip()

    # 지역 마스터 행
    province_short = province_kor.replace("특별시", "").replace("광역시", "").replace("특별자치시", "").replace("특별자치도", "")
    region_rows.append({
        "province_code": province_code,
        "city_code": city_code,
        "district_code": district_code,
        "province_kor": province_kor,
        "city_kor": city_kor,
        "district_kor": district_kor,
        "province_short": province_short,
    })

    # GeoJSON 파싱
    if geom_str and "{" in geom_str:
        # CSV 이중따옴표 제거: ""coordinates"" → "coordinates"
        geom_str = geom_str.strip('"')
        geom_str = geom_str.replace('""', '"')

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
        except json.JSONDecodeError as e:
            # 디버그: 처음 실패하는 것만 출력
            if len(features) == 0:
                print(f"  JSON 파싱 실패 ({district_kor}): {str(e)[:100]}")
                print(f"  GeoJSON 시작: {geom_str[:200]}")

# GeoJSON 저장
geojson = {"type": "FeatureCollection", "features": features}
geo_path = OUT_DIR / "geo_boundaries.json"
with open(geo_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False)
print(f"✅ GeoJSON 저장: {len(features)}개 법정동 경계 → {geo_path}")

# 지역 마스터 저장
region_df = pd.DataFrame(region_rows).drop_duplicates(subset=["district_code"])
region_df.to_parquet(OUT_DIR / "region_master.parquet", index=False)
print(f"✅ 지역 마스터 저장: {len(region_df)}개 법정동 → region_master.parquet")

# 통계
if features:
    sample = features[0]
    print(f"\n샘플 ({sample['properties']['name']}):")
    coords = sample["geometry"]["coordinates"]
    if sample["geometry"]["type"] == "MultiPolygon":
        n_polys = len(coords)
        n_points = sum(len(ring) for poly in coords for ring in poly)
    else:
        n_polys = 1
        n_points = sum(len(ring) for ring in coords)
    print(f"  폴리곤 수: {n_polys}, 꼭짓점 수: {n_points}")
