# Snowflake 네이티브 전환 기획안

## 1. 현재 → 전환 후 비교

```
현재 (3곳 분리, 3개 비용):
┌────────────────┐   ┌──────────────┐   ┌────────────┐
│ Streamlit Cloud│──→│ Render       │──→│ OpenAI API │
│ (대시보드)      │   │ (FastAPI)    │   │ (GPT-4.1)  │
│ Free           │   │ Free         │   │ ~$4/월     │
└───────┬────────┘   └──────┬───────┘   └────────────┘
        │                    │
        └── DuckDB ──────────┘
            (parquet 파일, 양쪽 복사)

전환 후 (Snowflake 1곳):
┌──────────────────────────────────────────────────┐
│                  Snowflake                        │
│                                                  │
│  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ Streamlit in     │  │ Cortex Agent         │  │
│  │ Snowflake        │──│ ┌ Cortex Analyst     │  │
│  │ (대시보드)        │  │ │ (자연어 → SQL)     │  │
│  │                  │  │ ├ Cortex COMPLETE    │  │
│  │                  │  │ │ (LLM 추론)         │  │
│  │                  │  │ └ Cortex Search      │  │
│  └──────────────────┘  └──────────┬───────────┘  │
│           │                       │              │
│           └───── Snowflake Tables ┘              │
│                 (이미 있음!)                       │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ Git Integration                          │    │
│  │ GitHub prod 브랜치 → 자동 동기화          │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### 없어지는 것
- ❌ Render 서버 (FastAPI)
- ❌ Streamlit Cloud
- ❌ OpenAI API 키 & 별도 과금
- ❌ DuckDB + parquet 파일 관리
- ❌ 두 레포 간 데이터 복사

### 남는 것
- ✅ GitHub 레포 (코드 관리 + CI/CD)
- ✅ Snowflake 계정 (데이터 + AI + UI 통합)

---

## 2. Snowflake 핵심 기능 매핑

### 2-1. Cortex Analyst (우리의 Text-to-SQL 대체)

현재 LangGraph Agent가 하는 일:
```
사용자: "신당동 유동인구 알려줘"
→ Router(GPT nano) → SQL 생성(GPT) → DuckDB 실행 → 응답 생성(GPT)
  (3번의 LLM 호출, OpenAI 비용)
```

Cortex Analyst:
```
사용자: "신당동 유동인구 알려줘"
→ Cortex Analyst(내장 LLM) → SQL 자동 생성 → Snowflake 실행 → 응답
  (1번의 호출, Snowflake 크레딧)
```

**Semantic Model (YAML)** 이 핵심 — 테이블 구조를 사람 언어로 설명해주면 Cortex가 자동으로 SQL 생성:

```yaml
# semantic_model.yaml
name: neighborhood_xray
tables:
  - name: SPH_POPULATION
    description: "서울 법정동별 월별 유동인구 (거주/직장/방문)"
    columns:
      - name: DISTRICT_CODE
        description: "법정동 코드 (8자리)"
      - name: STANDARD_YEAR_MONTH
        description: "기준년월 (YYYYMM)"
      - name: RESIDENTIAL_POPULATION
        description: "거주인구 수"
        synonyms: ["거주인구", "사는 사람", "주민"]
      - name: WORKING_POPULATION
        description: "직장인구 수"
        synonyms: ["직장인구", "출근", "근무"]
      - name: VISITING_POPULATION
        description: "방문인구 수"
        synonyms: ["방문인구", "방문객", "놀러오는"]

  - name: SPH_CARD_SALES
    description: "서울 법정동별 월별 카드매출 (20개 업종)"
    columns:
      - name: TOTAL_SALES
        description: "총 카드매출 금액 (원)"
        synonyms: ["매출", "총매출", "카드매출"]
      - name: COFFEE_SALES
        description: "커피 업종 매출"
        synonyms: ["커피", "카페", "커피매출"]
      - name: FOOD_SALES
        description: "식음료 업종 매출"
        synonyms: ["음식", "식당", "식음료"]
      # ... 20개 업종

  - name: SPH_INCOME
    description: "서울 법정동별 월별 소득/자산/신용 데이터"
    columns:
      - name: AVERAGE_INCOME
        description: "평균 소득 (원)"
        synonyms: ["소득", "수입", "연봉"]
      - name: AVERAGE_SCORE
        description: "평균 신용점수"
        synonyms: ["신용점수", "신용등급"]

  - name: REGION_MASTER
    description: "법정동 마스터 (코드-이름 매핑)"
    columns:
      - name: DISTRICT_CODE
        description: "법정동 코드"
      - name: CITY_KOR
        description: "시군구 한글명"
        synonyms: ["구", "시군구"]
      - name: DISTRICT_KOR
        description: "법정동 한글명"
        synonyms: ["동", "동네", "법정동"]

  - name: RICHGO_REALESTATE
    description: "아파트 매매/전세 시세 (서울 3개구, 13년치)"
    columns:
      - name: MEME_PRICE_PER_SUPPLY_PYEONG
        description: "매매 공급평당 가격 (만원)"
        synonyms: ["매매가", "집값", "아파트값"]
      - name: JEONSE_PRICE_PER_SUPPLY_PYEONG
        description: "전세 공급평당 가격 (만원)"
        synonyms: ["전세가", "전세"]
```

### 2-2. Cortex COMPLETE (LLM 추론)

시뮬레이션, 인사이트 해석 등 복합 추론에 사용:

```python
# Snowflake Python에서 Cortex LLM 호출
from snowflake.cortex import Complete

response = Complete(
    model="claude-3.5-sonnet",  # 또는 "llama3.1-70b" (무료급)
    prompt=f"""
    서초구 잠원동 데이터:
    - 유동인구: 68만명 (방문 22만)
    - 카드매출: 커피 3.2억, 음식 8.1억
    - 평균소득: 7,200만원
    
    이 동네에서 카페를 차리면 예상 매출은?
    """
)
```

### 2-3. Cortex Agent (우리 LangGraph 대체)

Cortex Analyst(구조화 데이터) + Cortex Search(비구조화) + LLM을 자동 오케스트레이션:

```python
from snowflake.core import Root
from snowflake.cortex import agent

# Agent 생성 — Cortex Analyst를 도구로 사용
response = agent.run(
    model="claude-3.5-sonnet",
    tools=[
        {"tool_spec": {"type": "cortex_analyst_text_to_sql",
                       "semantic_model_file": "@stage/semantic_model.yaml"}}
    ],
    messages=[{"role": "user", "content": "신당동에 카페 차리면 매출이 어떨까?"}]
)
```

---

## 3. 전환 작업 목록

### Phase 1: Snowflake 데이터 확인 & Semantic Model (Day 1)
- [ ] 기존 Snowflake 테이블 목록 확인
- [ ] 테이블명 ↔ 우리 parquet 파일 매핑
- [ ] semantic_model.yaml 작성 (위 예시 기반)
- [ ] Cortex Analyst 테스트 ("신당동 유동인구" 질의)

### Phase 2: Streamlit in Snowflake 전환 (Day 2~3)
- [ ] 새 GitHub 레포 또는 브랜치 (`snowflake-native`)
- [ ] DuckDB/parquet 쿼리 → Snowflake SQL로 변환
  - `read_parquet('xxx.parquet')` → `SELECT * FROM DB.SCHEMA.TABLE`
  - data_loader.py → snowflake_connector로 교체
- [ ] Streamlit in Snowflake 앱 생성
- [ ] Git Integration 연결 (prod 브랜치)
- [ ] 기존 5개 탭 동작 확인

### Phase 3: Cortex Agent 전환 (Day 3~4)
- [ ] Cortex Analyst 설정 (semantic_model.yaml 스테이지 업로드)
- [ ] Cortex Agent 설정 (Analyst를 도구로 연결)
- [ ] chat_ui.py → Cortex Agent API 호출로 변경
- [ ] 시뮬레이션 로직 → Cortex COMPLETE로 이관
- [ ] 비용 추적 → Snowflake 크레딧 모니터링으로 변경

### Phase 4: CI/CD 연결 (Day 4)
- [ ] Snowflake Git Repository 객체 생성
- [ ] GitHub snowF3 레포 연결
- [ ] prod 브랜치 push → 자동 동기화 확인
- [ ] 테스트 배포

### Phase 5: 정리 (Day 5)
- [ ] Render 서비스 삭제
- [ ] Streamlit Cloud 앱 삭제
- [ ] OpenAI API 키 비활성화
- [ ] README 업데이트 (Snowflake 접속 방법)

---

## 4. 코드 변경 상세

### 4-1. data_loader.py 변경

```python
# 현재 (DuckDB + parquet)
import pandas as pd
from pathlib import Path
PROCESSED_DIR = Path("processed_data")

def load_population_agg():
    return pd.read_parquet(PROCESSED_DIR / "population_agg.parquet")

# 전환 후 (Snowflake 직접 쿼리)
import streamlit as st
from snowflake.snowpark.context import get_active_session

def get_session():
    return get_active_session()  # Streamlit in Snowflake에서 자동 제공

def load_population_agg():
    session = get_session()
    return session.table("SPH_POPULATION").to_pandas()
```

### 4-2. chat_ui.py 변경

```python
# 현재 (FastAPI HTTP 호출)
response = requests.post(f"{AGENT_URL}/chat", json={...})

# 전환 후 (Cortex Agent 직접 호출)
from snowflake.cortex import agent

response = agent.run(
    model="claude-3.5-sonnet",
    tools=[cortex_analyst_tool],
    messages=messages
)
```

### 4-3. 불필요해지는 파일들

```
삭제 가능:
  agent/agent/server.py      ← FastAPI 서버 (불필요)
  agent/agent/graph.py       ← LangGraph (Cortex Agent로 대체)
  agent/agent/tools/         ← DuckDB 도구 (Cortex Analyst로 대체)
  scripts/preprocess.py      ← parquet 변환 (불필요)
  processed_data/            ← parquet 파일 (불필요)
  render.yaml                ← Render 배포 (불필요)
```

---

## 5. Snowflake 비용 추정

### Cortex LLM 비용 (크레딧 기반)

| 모델 | 크레딧/1M tokens | 우리 예상 (월 1,500건) |
|------|-----------------|---------------------|
| llama3.1-8b | 0.12 | ~$0.5/월 |
| llama3.1-70b | 0.90 | ~$4/월 |
| claude-3.5-sonnet | 1.80 | ~$8/월 |
| gpt-4o | 3.00 | ~$13/월 |

### 전체 비용 비교

| 항목 | 현재 | Snowflake 전환 후 |
|------|------|-----------------|
| 호스팅 (Render) | $0 (Free) | $0 (Snowflake에 포함) |
| 호스팅 (Streamlit Cloud) | $0 (Free) | $0 (Snowflake에 포함) |
| LLM (OpenAI) | ~$4/월 | ~$4/월 (Cortex 크레딧) |
| 데이터 저장/쿼리 | $0 (로컬) | ~$2/월 (Snowflake 웨어하우스) |
| **합계** | **~$4/월** | **~$6/월** |

비용은 비슷하지만, **운영 복잡도가 극적으로 줄어듦** (3곳 → 1곳).

---

## 6. Git CI/CD 설정

### Snowflake에서 GitHub 연결

```sql
-- 1. GitHub PAT Secret 생성
CREATE OR REPLACE SECRET github_secret
  TYPE = password
  USERNAME = 'snowF3'
  PASSWORD = 'ghp_xxxxx';  -- GitHub Personal Access Token

-- 2. API Integration 생성
CREATE OR REPLACE API INTEGRATION github_api
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/snowF3/')
  ALLOWED_AUTHENTICATION_SECRETS = (github_secret)
  ENABLED = true;

-- 3. Git Repository 연결
CREATE OR REPLACE GIT REPOSITORY snowf3_streamlit
  API_INTEGRATION = github_api
  GIT_CREDENTIALS = github_secret
  ORIGIN = 'https://github.com/snowF3/streamlit.git';

-- 4. prod 브랜치 fetch
ALTER GIT REPOSITORY snowf3_streamlit FETCH;

-- 5. Streamlit 앱 생성 (Git에서 직접)
CREATE OR REPLACE STREAMLIT neighborhood_xray
  ROOT_LOCATION = '@snowf3_streamlit/branches/prod/app'
  MAIN_FILE = 'main.py'
  QUERY_WAREHOUSE = 'COMPUTE_WH';
```

### 배포 워크플로우

```bash
# 개발자가 할 일 (변경 없음!)
git checkout prod
git merge dev
git push origin prod

# Snowflake에서 동기화 (자동 또는 수동)
ALTER GIT REPOSITORY snowf3_streamlit FETCH;
-- → Streamlit 앱 자동 업데이트
```

---

## 7. 최종 아키텍처

```
개발자
  │
  └── git push origin prod
        │
        ▼
GitHub (snowF3/streamlit)
  │ prod 브랜치
  ▼
Snowflake Git Repository (자동 동기화)
  │
  ├── Streamlit in Snowflake ──→ 대시보드 UI
  │     └── Cortex Agent 호출
  │           ├── Cortex Analyst ──→ 자연어 → SQL → 결과
  │           ├── Cortex COMPLETE ──→ 인사이트/시뮬레이션
  │           └── Cortex Search ──→ (향후 비정형 데이터)
  │
  └── Snowflake Tables ──→ SPH / 리치고 / 아정당 (이미 있음)
```
