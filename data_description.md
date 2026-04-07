# data 설명
 - SPH
 - 리치고
 - 아정당

## SPH

### SPH_법정동_마스터.csv
- **실제 내용: 자산소득 데이터**
- **설명**: 법정동 단위 고객의 소득, 카드 사용, 대출, 연체, 신용점수, 자산 등 종합 금융 프로파일
- **키 컬럼**:
    - `PROVINCE_CODE` : 시도 코드
    - `CITY_CODE` : 시군구 코드
    - `DISTRICT_CODE` : 법정동 코드
    - `STANDARD_YEAR_MONTH` : 기준년월 (예: 202207)
    - `INCOME_TYPE` : 소득유형 (0=법인, 1=개인) → 코드 마스터 M08 참조
    - `GENDER` : 성별 (M/F) → 코드 마스터 M01 참조
    - `AGE_GROUP` : 연령대 (10~85) → 코드 마스터 M02 참조
- **측정값 컬럼** (주요 그룹):
    - 고객수: `CUSTOMER_COUNT`
    - 직업군 비율: `RATE_MODEL_GROUP_LARGE_COMPANY_EMPLOYEE`, `RATE_MODEL_GROUP_GENERAL_EMPLOYEE`, `RATE_MODEL_GROUP_PROFESSIONAL_EMPLOYEE`, `RATE_MODEL_GROUP_EXECUTIVES`, `RATE_MODEL_GROUP_GENERAL_SELF_EMPLOYED`, `RATE_MODEL_GROUP_PROFESSIONAL_SELF_EMPLOYED`, `RATE_MODEL_GROUP_OTHERS`
    - 주거 평형: `PYEONG_UNDER_20_COUNT`, `PYEONG_OVER_20_COUNT`, `PYEONG_OVER_30_COUNT`, `PYEONG_OVER_40_COUNT`
    - 소득 통계: `AVERAGE_INCOME`, `MEDIAN_INCOME`, `AVERAGE_HOUSEHOLD_INCOME`, `AVERAGE_INCOME_OVER_70`, 소득구간별 비율 (`RATE_INCOME_UNDER_20M` ~ `RATE_INCOME_OVER_70M`)
    - 매매/전세 갭: `AVERAGE_PRICE_GAP`, `AVERAGE_LEASE_GAP`
    - 카드 사용: 카드수(신용/체크), 총사용액(일시불/할부/현금서비스/해외), 평균사용액, 한도
    - 대출 잔액: 은행/비은행/신용/주택/담보별 건수 및 금액 (기존+신규)
    - 연체: `DELINQUENT0_COUNT`, `DELINQUENT30_COUNT`, `DELINQUENT90_COUNT`, 평균연체일수/금액
    - 신용점수: `AVERAGE_SCORE`, 등급별 비율 (`RATE_SCORE1`~`RATE_SCORE3`), 대출여력
    - 자산: `OWN_HOUSING_COUNT`, `MULTIPLE_HOUSING_COUNT`, `AVERAGE_ASSET_AMOUNT`, `RATE_HIGHEND`

### SPH_유동인구.csv
- **실제 내용: 유동인구 데이터** (파일명 일치)
- **설명**: 법정동 단위 시간대별/성별/연령별 유동인구 (거주/근무/방문)
- **키 컬럼**:
    - `PROVINCE_CODE` : 시도 코드
    - `CITY_CODE` : 시군구 코드
    - `DISTRICT_CODE` : 법정동 코드
    - `STANDARD_YEAR_MONTH` : 기준년월 (예: 202303)
    - `WEEKDAY_WEEKEND` : 주중/주말 (W/H) → 코드 마스터 M04 참조
    - `GENDER` : 성별 (M/F) → 코드 마스터 M01 참조
    - `AGE_GROUP` : 연령대 → 코드 마스터 M02 참조
    - `TIME_SLOT` : 시간대 (T06~T24) → 코드 마스터 M03 참조
- **측정값 컬럼**:
    - `RESIDENTIAL_POPULATION` : 거주인구
    - `WORKING_POPULATION` : 근무인구
    - `VISITING_POPULATION` : 방문인구

### SPH_자산소득.csv
- **실제 내용: 코드 마스터** (파일명 불일치)
- **설명**: 다른 SPH 테이블에서 사용하는 코드값의 정의 (룩업 테이블)
- **컬럼**: `CODE_ID`, `CODE_NAME`, `SUB_CODE`, `SUB_CODE_NAME`, `SORT_ORDER`, `USE_YN`, `REMARKS`
- **코드 체계**:
    | CODE_ID | CODE_NAME | 코드값 |
    |---------|-----------|--------|
    | M01 | 성별 | M(남), F(여) |
    | M02 | 연령대 | 10(00-14), 15(15-19), 20(20-24), 25(25-29), 30(30-34), 35(35-39), 40(40-44), 45(45-49), 50(50-54), 55(55-59), 60(60-64), 65(65-69), 70(70-74), 75(75-79), 80(80-84), 85(85-89) |
    | M03 | 시간대 | T06(아침), T09(오전), T12(점심), T15(오후), T18(저녁), T21(심야), T24(기타) |
    | M04 | 주중/주말 | H(주말), W(주중) |
    | M06 | 라이프스타일 | L01(싱글), L02(신혼부부), L03(영유아가족), L04(청소년가족), L05(성인자녀가족), L06(실버) |
    | M07 | 신용관리사_파일구분 | 0(기업), 1(주거) |
    | M08 | 카드사_파일구분 | 0(법인), 1(개인) |

### SPH_카드매출.csv
- **실제 내용: 법정동 마스터** (파일명 불일치)
- **설명**: 법정동 행정구역 정보 및 GeoJSON 경계 좌표
- **컬럼**:
    - `PROVINCE_CODE` : 시도 코드
    - `CITY_CODE` : 시군구 코드
    - `DISTRICT_CODE` : 법정동 코드
    - `PROVINCE_KOR_NAME` : 시도 한글명 (예: 서울특별시)
    - `CITY_KOR_NAME` : 시군구 한글명 (예: 중랑구)
    - `DISTRICT_KOR_NAME` : 법정동 한글명 (예: 중화동)
    - `PROVINCE_ENG_NAME` : 시도 영문명
    - `CITY_ENG_NAME` : 시군구 영문명
    - `DISTRICT_ENG_NAME` : 법정동 영문명
    - `DISTRICT_GEOM` : 법정동 경계 GeoJSON 좌표 (MultiPolygon)

### SPH_코드_마스터.csv
- **실제 내용: 카드매출 데이터** (파일명 불일치)
- **설명**: 법정동 단위 업종별 카드 매출액 및 건수 (시간대/성별/연령/라이프스타일별)
- **키 컬럼**:
    - `PROVINCE_CODE` : 시도 코드
    - `CITY_CODE` : 시군구 코드
    - `DISTRICT_CODE` : 법정동 코드
    - `STANDARD_YEAR_MONTH` : 기준년월 (예: 202209)
    - `CARD_TYPE` : 카드 유형 (0=법인, 1=개인) → 코드 마스터 M08 참조
    - `WEEKDAY_WEEKEND` : 주중/주말 (W/H) → 코드 마스터 M04 참조
    - `GENDER` : 성별 (M/F/*) → 코드 마스터 M01 참조
    - `AGE_GROUP` : 연령대 → 코드 마스터 M02 참조
    - `TIME_SLOT` : 시간대 (T06~T24) → 코드 마스터 M03 참조
    - `LIFESTYLE` : 라이프스타일 (L01~L06/*) → 코드 마스터 M06 참조
- **측정값 컬럼** (20개 업종 x 매출액 + 건수):
    | 업종 | 매출액 컬럼 | 건수 컬럼 |
    |------|------------|----------|
    | 식음료 | FOOD_SALES | FOOD_COUNT |
    | 커피 | COFFEE_SALES | COFFEE_COUNT |
    | 오락 | ENTERTAINMENT_SALES | ENTERTAINMENT_COUNT |
    | 백화점 | DEPARTMENT_STORE_SALES | DEPARTMENT_STORE_COUNT |
    | 대형마트 | LARGE_DISCOUNT_STORE_SALES | LARGE_DISCOUNT_STORE_COUNT |
    | 소매점 | SMALL_RETAIL_STORE_SALES | SMALL_RETAIL_STORE_COUNT |
    | 의류/잡화 | CLOTHING_ACCESSORIES_SALES | CLOTHING_ACCESSORIES_COUNT |
    | 스포츠/문화/레저 | SPORTS_CULTURE_LEISURE_SALES | SPORTS_CULTURE_LEISURE_COUNT |
    | 숙박 | ACCOMMODATION_SALES | ACCOMMODATION_COUNT |
    | 여행 | TRAVEL_SALES | TRAVEL_COUNT |
    | 미용 | BEAUTY_SALES | BEAUTY_COUNT |
    | 생활서비스 | HOME_LIFE_SERVICE_SALES | HOME_LIFE_SERVICE_COUNT |
    | 교육/학원 | EDUCATION_ACADEMY_SALES | EDUCATION_ACADEMY_COUNT |
    | 의료 | MEDICAL_SALES | MEDICAL_COUNT |
    | 전자/가구 | ELECTRONICS_FURNITURE_SALES | ELECTRONICS_FURNITURE_COUNT |
    | 자동차 판매 | CAR_SALES | CAR_SALES_COUNT |
    | 자동차 서비스 | CAR_SERVICE_SUPPLIES_SALES | CAR_SERVICE_SUPPLIES_COUNT |
    | 주유 | GAS_STATION_SALES | GAS_STATION_COUNT |
    | 이커머스 | E_COMMERCE_SALES | E_COMMERCE_COUNT |
    | **합계** | **TOTAL_SALES** | **TOTAL_COUNT** |

## 리치고

### REGION_APT_RICHGO_MARKET_PRICE_M_H.csv
- **설명**: 읍면동(emd)/시군구(sgg) 단위 아파트 AI 매매·전세 시세 (공급평당 가격, 만원 단위)
- **기간**: 2012-01 ~ 2024-12 (월별, 156개월)
- **행 수**: 4,356건 (emd 3,888건 + sgg 468건)
- **지역 범위**: 서울특별시 영등포구(2,313건), 서초구(1,331건), 중구(712건) — 읍면동 26개, 시군구 3개
- **키 컬럼**:
    - `REGION_LEVEL` : 지역 단위 (emd=읍면동, sgg=시군구)
    - `BJD_CODE` : 법정동 코드 (10자리)
    - `SD` : 시도명 (서울)
    - `SGG` : 시군구명 (중구, 영등포구, 서초구)
    - `EMD` : 읍면동명 (sgg 레벨일 경우 빈 값)
    - `YYYYMMDD` : 기준년월 (예: 2024-12-01)
- **측정값 컬럼**:
    - `TOTAL_HOUSEHOLDS` : 총 세대수 (547 ~ 45,145)
    - `MEME_PRICE_PER_SUPPLY_PYEONG` : 매매 공급평당 가격 (만원, 약 1,082 ~ 11,651)
    - `JEONSE_PRICE_PER_SUPPLY_PYEONG` : 전세 공급평당 가격 (만원)

### REGION_MOIS_POPULATION_AGE_UNDER5_PER_FEMALE_20TO40_M_H.csv
- **설명**: 읍면동 단위 5세 미만 영유아 인구 대비 20~40세 여성 인구 비율 (행정안전부 주민등록 기반)
- **기간**: 2025-01 (단일 시점 스냅샷)
- **행 수**: 118건
- **지역 범위**: 서울특별시 중구(74건), 영등포구(34건), 서초구(10건) — 읍면동 118개
- **키 컬럼**:
    - `REGION_LEVEL` : 지역 단위 (emd 고정)
    - `BJD_CODE` : 법정동 코드 (10자리)
    - `SD` : 시도명 (서울)
    - `SGG` : 시군구명 (중구, 영등포구, 서초구)
    - `EMD` : 읍면동명
    - `YYYYMMDD` : 기준년월 (2025-01-01)
- **측정값 컬럼**:
    - `AGE_UNDER5` : 5세 미만 영유아 인구수 (0 ~ 2,505)
    - `FEMALE_20TO40` : 20~40세 여성 인구수
    - `AGE_UNDER5_PER_FEMALE_20TO40` : 영유아/가임여성 비율 (0 ~ 1, 빈 값 존재 — 여성 인구 0인 경우)

### REGION_MOIS_POPULATION_GENDER_AGE_M_H.csv
- **설명**: 읍면동 단위 성별·연령대별 주민등록 인구수 (행정안전부 기반)
- **기간**: 2025-01 (단일 시점 스냅샷)
- **행 수**: 118건
- **지역 범위**: 서울특별시 중구(74건), 영등포구(34건), 서초구(10건) — 읍면동 118개
- **키 컬럼**:
    - `REGION_LEVEL` : 지역 단위 (emd 고정)
    - `BJD_CODE` : 법정동 코드 (10자리)
    - `SD` : 시도명 (서울)
    - `SGG` : 시군구명 (중구, 영등포구, 서초구)
    - `EMD` : 읍면동명
    - `YYYYMMDD` : 기준년월 (2025-01-01)
- **측정값 컬럼**:
    - `TOTAL` : 총 인구수 (0 ~ 106,138)
    - `MALE` : 남성 인구수
    - `FEMALE` : 여성 인구수
    - `AGE_UNDER20` : 20세 미만 인구수
    - `AGE_20S` : 20대 인구수
    - `AGE_30S` : 30대 인구수
    - `AGE_40S` : 40대 인구수
    - `AGE_50S` : 50대 인구수
    - `AGE_60S` : 60대 인구수
    - `AGE_OVER70` : 70세 이상 인구수


## 아정당

### V01_MONTHLY_REGIONAL_CONTRACT_STATS.csv
- **설명**: 월별 지역(시도/시군구)별 상품 유형별 계약 통계 - 계약 수, 퍼널 전환수, 전환율, 매출 포함
- **기간**: 2023-02 ~ 2027-06 (월별, 46개월)
- **행 수**: 23,614건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월 (예: 2026-01-01)
    - `INSTALL_STATE` : 설치 시도 (서울, 경기, 부산 등 19개 시도)
    - `INSTALL_CITY` : 설치 시군구
    - `MAIN_CATEGORY_NAME` : 상품 유형 (인터넷 8,379 / 렌탈 6,598 / 유심만 4,017 / 모바일 2,810 / 알뜰요금제 1,694 / 다이렉트자보 68 / 기업용인터넷 48)
- **측정값 컬럼**:
    - `CONTRACT_COUNT` : 계약 건수
    - `CONSULT_REQUEST_COUNT` : 상담요청 건수
    - `REGISTEND_COUNT` : 접수 완료 건수
    - `OPEN_COUNT` : 개통 건수
    - `PAYEND_COUNT` : 지급 완료 건수
    - `REGISTEND_CVR` : 접수 전환율 (%)
    - `OPEN_CVR` : 개통 전환율 (%)
    - `PAYEND_CVR` : 지급 전환율 (%)
    - `AVG_NET_SALES` : 평균 순매출 (원)
    - `TOTAL_NET_SALES` : 총 순매출 (원)

### V02_SERVICE_BUNDLE_PATTERNS.csv
- **설명**: 인터넷 서비스 결합 상품 패턴별 계약 현황 및 정책금 분석
- **기간**: 2021-08 ~ 2027-03 (월별, 61개월)
- **행 수**: 2,164건
- **대상 상품**: 인터넷 전용
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `MAIN_CATEGORY_NAME` : 상품 유형 (인터넷 단일)
    - `BUNDLE_COMBINATION` : 결합 유형 (23종) — 단독가입(322) / 요즘가족결합(256) / 총액결합할인(211) / 온할인(199) / 패밀리(212) / 참쉬운가족결합(175) / 프리미엄싱글결합(146) / 투게더결합(95) 등
    - `HAS_TV` : TV 결합 여부 (Y/N)
    - `HAS_PHONE` : 전화 결합 여부 (Y/N)
    - `HAS_WIFI` : WiFi 결합 여부 (Y/N)
- **측정값 컬럼**:
    - `CONTRACT_COUNT` : 계약 건수
    - `PAYEND_COUNT` : 지급 완료 건수
    - `AVG_NET_SALES` : 평균 순매출 (원)
    - `AVG_POLICY_AMOUNT` : 평균 정책금 (원)

### V03_CONTRACT_FUNNEL_CONVERSION.csv
- **설명**: 월별 상품 유형별 계약 퍼널 단계별 전환율 (상담요청→청약→접수→개통→지급)
- **기간**: 2021-07 ~ 2027-07 (월별, 69개월)
- **행 수**: 274건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `MAIN_CATEGORY_NAME` : 상품 유형 (인터넷 69 / 렌탈 50 / 유심만 38 / 모바일 34 / 알뜰요금제 34 / 기업용인터넷 26 / 다이렉트자보 13 / 상조 6 / 부동산 3 / 이사 1)
- **측정값 컬럼**:
    - `TOTAL_COUNT` : 총 건수
    - `CONSULT_REQUEST_COUNT` : 상담요청 건수
    - `SUBSCRIPTION_COUNT` : 청약 건수
    - `REGISTEND_COUNT` : 접수 완료 건수
    - `OPEN_COUNT` : 개통 건수
    - `PAYEND_COUNT` : 지급 완료 건수
    - `CVR_CONSULT_REQUEST` : 상담요청 전환율 (%)
    - `CVR_SUBSCRIPTION` : 청약 전환율 (%)
    - `CVR_REGISTEND` : 접수 전환율 (%)
    - `CVR_OPEN` : 개통 전환율 (%)
    - `CVR_PAYEND` : 지급 전환율 (%)
    - `OVERALL_CVR` : 전체 전환율 (%)

### V04_CHANNEL_CONTRACT_PERFORMANCE.csv
- **설명**: 유입 채널(접수 경로/마케팅 경로)별 계약 성과 - 개통률, 지급률, 매출 포함
- **기간**: 2021-08 ~ 2026-12 (월별, 62개월)
- **행 수**: 8,002건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `MAIN_CATEGORY_NAME` : 상품 유형 (인터넷 2,939 / 렌탈 1,917 / 유심만 1,090 / 모바일 980 / 알뜰요금제 712 / 기업용인터넷 304 등 10종)
    - `RECEIVE_PATH_NAME` : 접수 경로 (인바운드 3,132 / 플랫폼 1,991 / 카톡 882 / 아정당랜딩 470 / 기타 564 / ARS전화번호남기기 222 / 아정당매장 188 / 다이렉트 123 등 37종)
    - `INFLOW_PATH_NAME` : 유입 경로 (미분류 695 / 재인입 565 / 인터넷(네이버/구글등) 453 / 유튜브(자사) 409 / 카카오 365 / 블로그 364 / 네이버브랜드검색광고 361 / 전화예약상담 342 / 유튜브(PPL) 325 / 랜딩페이지 316 등 54종)
- **측정값 컬럼**:
    - `CONTRACT_COUNT` : 계약 건수
    - `REGISTEND_COUNT` : 접수 완료 건수
    - `OPEN_COUNT` : 개통 건수
    - `PAYEND_COUNT` : 지급 완료 건수
    - `OPEN_CVR` : 개통 전환율 (%)
    - `PAYEND_CVR` : 지급 전환율 (%)
    - `AVG_NET_SALES` : 평균 순매출 (원)
    - `TOTAL_NET_SALES` : 총 순매출 (원)

### V05_REGIONAL_NEW_INSTALL.csv
- **설명**: 지역별 인터넷 신규 설치 현황 - 단독/결합 비율, 개통/지급 건수, 평균 매출
- **기간**: 2023-02 ~ 2027-06 (월별, 46개월)
- **행 수**: 8,379건
- **지역 범위**: 전국 18개 시도, 시군구 단위
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `INSTALL_STATE` : 설치 시도 (서울, 경기, 경남, 경북, 부산, 대구, 인천, 광주, 대전, 울산, 세종, 강원, 충북, 충남, 전북, 전남, 제주 등 18개)
    - `INSTALL_CITY` : 설치 시군구
- **측정값 컬럼**:
    - `CONTRACT_COUNT` : 계약 건수
    - `OPEN_COUNT` : 개통 건수
    - `PAYEND_COUNT` : 지급 완료 건수
    - `BUNDLE_COUNT` : 결합 건수
    - `STANDALONE_COUNT` : 단독 가입 건수
    - `AVG_NET_SALES` : 평균 순매출 (원)

### V06_RENTAL_CATEGORY_TRENDS.csv
- **설명**: 렌탈 상품 카테고리(대분류/소분류)별 월별 트렌드 - 지역, 개통/지급 전환율, 정책금 포함
- **기간**: 2023-03 ~ 2026-06 (월별, 40개월)
- **행 수**: 6,013건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `INSTALL_STATE` : 설치 시도
    - `RENTAL_MAIN_CATEGORY` : 렌탈 대분류 (41종) — 주방가전(정수기 591 / 식기세척기 88 / 전기레인지 43 등), 생활가전(공기청정기 490 / 세탁기 401 / 건조기 242 / 에어컨 303 등), IT(노트북 219 / TV 388 등), 가구(침대/매트리스 274 / 안마의자 198) 등
    - `RENTAL_SUB_CATEGORY` : 렌탈 소분류 (대분류와 동일 수준으로 세분화)
- **측정값 컬럼**:
    - `CONTRACT_COUNT` : 계약 건수
    - `OPEN_COUNT` : 개통 건수
    - `PAYEND_COUNT` : 지급 완료 건수
    - `OPEN_CVR` : 개통 전환율 (%)
    - `PAYEND_CVR` : 지급 전환율 (%)
    - `AVG_NET_SALES` : 평균 순매출 (원)
    - `AVG_POLICY_AMOUNT` : 평균 정책금 (원, 빈 값 존재)

### V07_GA4_MARKETING_ATTRIBUTION.csv
- **설명**: GA4 기반 UTM 소스/매체별 마케팅 전환 분석 - 세션, 상담요청, 계약 CVR, 매출 포함
- **기간**: 2025-02 ~ 2026-04 (월별, 15개월)
- **행 수**: 8,869건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `UTM_SOURCE` : UTM 소스 (네이버, 구글, 유튜브 인플루언서, 제휴 사이트 등 다수)
    - `UTM_MEDIUM` : UTM 매체 (referral, cpc, ppl, 캠페인명 등 다수)
- **측정값 컬럼**:
    - `TOTAL_SESSIONS` : 총 세션 수
    - `TOTAL_USERS` : 총 사용자 수
    - `TOTAL_CONSULT_REQUESTS` : 총 상담요청 건수
    - `TOTAL_CONSULT_PHONE` : 전화 상담요청
    - `TOTAL_CONSULT_KAKAO` : 카카오 상담요청
    - `TOTAL_CONSULT_CHANNELTALK` : 채널톡 상담요청
    - `TOTAL_CONTRACTS` : 총 계약 건수
    - `CONSULT_CVR` : 상담 전환율 (%)
    - `CONTRACT_CVR` : 계약 전환율 (%)
    - `TOTAL_REVENUE` : 총 매출 (원)

### V08_GA4_DEVICE_STATS.csv
- **설명**: GA4 디바이스 유형별 세션 수, 사용자 수, 전환 이벤트 집계
- **기간**: 2025-02 ~ 2026-04 (월별, 15개월)
- **행 수**: 57건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `DEVICE_CATEGORY` : 디바이스 유형 (mobile 15건 / desktop 15건 / tablet 15건 / smart tv 12건)
- **측정값 컬럼**:
    - `SESSION_COUNT` : 세션 수
    - `USER_COUNT` : 사용자 수
    - `CONVERSION_EVENT_COUNT` : 전환 이벤트 수
    - `CONVERSION_RATE` : 전환율 (%)

### V09_MONTHLY_CALL_STATS.csv
- **설명**: 월별 콜센터 통화 통계 - 수신/발신 구분, 상품 유형별 통화량, 평균 통화 시간, 연결률
- **기간**: 2022-12 ~ 2026-04 (월별, 37개월)
- **행 수**: 418건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `DIVISION_NAME` : 통화 구분 (수신 210건 / 발신 208건)
    - `MAIN_CATEGORY_NAME` : 상품 유형 (인터넷 71 / 렌탈 65 / 유심만 63 / 알뜰요금제 61 / 모바일 58 / 기업용인터넷 52 / 다이렉트자보 26 / 상조 9 / 이사 7 / 부동산 6)
- **측정값 컬럼**:
    - `CALL_COUNT` : 통화 건수
    - `AVG_BILL_SECOND` : 평균 통화시간 (초)
    - `AVG_BILL_MINUTE` : 평균 통화시간 (분)
    - `MAX_BILL_SECOND` : 최대 통화시간 (초)
    - `TOTAL_BILL_SECOND` : 총 통화시간 (초)
    - `CONNECTED_COUNT` : 연결 건수
    - `UNCONNECTED_COUNT` : 미연결 건수
    - `CONNECTION_RATE` : 연결률 (%)

### V10_HOURLY_CALL_DISTRIBUTION.csv
- **설명**: 콜센터 시간대(0~23시) × 요일별 통화 분포 - 피크타임 및 연결률 분석용
- **행 수**: 336건
- **참고**: YEAR_MONTH 컬럼 없음 — 전체 기간 집계 데이터
- **키 컬럼**:
    - `HOUR_OF_DAY` : 시간대 (0~23시, 24개 구간)
    - `DAY_OF_WEEK` : 요일 코드 (0~6)
    - `DAY_OF_WEEK_NAME` : 요일명 (월/화/수/목/금/토/일, 빈 값 존재)
    - `DIVISION_NAME` : 통화 구분 (수신 168건 / 발신 168건)
- **측정값 컬럼**:
    - `CALL_COUNT` : 통화 건수
    - `CONNECTED_COUNT` : 연결 건수
    - `UNCONNECTED_COUNT` : 미연결 건수
    - `CONNECTION_RATE` : 연결률 (%)
    - `AVG_BILL_SECOND` : 평균 통화시간 (초)
    - `AVG_BILL_MINUTE` : 평균 통화시간 (분)

### V11_CALL_TO_CONTRACT_CONVERSION.csv
- **설명**: 콜센터 통화에서 계약서 생성까지의 전환율 및 리드타임 분석
- **기간**: 2023-07 ~ 2026-04 (월별, 31개월)
- **행 수**: 100건
- **키 컬럼**:
    - `YEAR_MONTH` : 기준년월
    - `MAIN_CATEGORY_NAME` : 상품 유형 (알뜰요금제 19 / 렌탈 17 / 인터넷 13 / 유심만 13 / 모바일 12 / 기업용인터넷 11 / 상조 5 / 다이렉트자보 5 / 이사 4 / 부동산 1)
    - `DIVISION_NAME` : 통화 구분 (발신 57건 / 수신 43건)
- **측정값 컬럼**:
    - `TOTAL_CALLS` : 총 통화 건수
    - `LINKED_CONTRACTS` : 연계 계약 건수
    - `CALLS_PER_CONTRACT` : 계약당 통화 건수
    - `CALL_TO_CONTRACT_CVR` : 통화→계약 전환율 (%)
    - `AVG_LEADTIME_DAYS` : 평균 리드타임 (일, 음수값 존재 — 통화 전 계약 발생 케이스)
    - `MEDIAN_LEADTIME_DAYS` : 중앙값 리드타임 (일)