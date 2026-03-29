# ✈️ FlightIQ — Airline Operations Intelligence Platform

> Flight delays cost U.S. airlines **$28.2 billion annually**. This platform identifies operational inefficiencies across airports, carriers, and weather conditions to recommend data-driven strategies that reduce delays and improve airline performance.

![Landing Page](docs/screenshots/landing.png)

---

## 🎯 Problem Statement

Despite advances in aviation technology, **1 in 5 U.S. domestic flights arrives late**. The industry lacks unified analytics that decompose delay causes, identify systemic patterns, and translate data into actionable operational improvements.

This platform analyzes **2.76 million flights** across **15 carriers** and **350+ airports** (Mar–Jul 2023) to answer critical operational questions and provide executive-ready insights.

---

## 🔑 Key Questions Answered

| # | Question | Finding |
|---|----------|---------|
| 1 | Which airline has the best on-time performance? | **Republic Airways** leads at 85.6% on-time; **Delta** best among majors at 81.2% |
| 2 | What are the main delay causes? | **Late Aircraft cascading (39%)** and **Carrier issues (36%)** dominate — not weather |
| 3 | What are peak delay hours? | **3 AM–4 AM** red-eye flights show 36%+ delay rates; **evening flights (6–9 PM)** accumulate 28%+ |
| 4 | How does weather compare to carrier delays? | Weather causes only **5.3%** of delay minutes — carrier-controllable factors are 7× larger |
| 5 | Which airports are most delayed? | Smaller regional airports have highest rates; hub airports manage volume efficiently |
| 6 | What seasonal patterns exist? | **Summer months** (Jun–Jul) show 22%+ delay rates vs 18% in spring |

---

## 🏗️ Architecture

```
                            DATA PIPELINE
  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │  BTS Flight Data ──┐                                │
  │  (2.76M rows)      │    ETL Pipeline                │
  │                     ├──► (Python/Pandas) ──► DuckDB  │
  │  Airport Reference ─┘    Cleaning, Joins     104 MB  │
  │  (OurAirports)           Feature Eng.        OLAP   │
  │                                                     │
  └────────────────────────────┬────────────────────────┘
                               │
              ┌────────────────┼────────────────────┐
              │                │                    │
              ▼                ▼                    ▼
        ┌──────────┐   ┌────────────┐    ┌──────────────┐
        │   SQL    │   │   Python   │    │   Excel &    │
        │ Analysis │   │  EDA + ML  │    │   Power BI   │
        │ 4 files  │   │ 6 scripts  │    │  Dashboards  │
        │ CTEs,    │   │ 28 charts  │    │  KPIs, Drill │
        │ Windows  │   │ SHAP model │    │  Heatmaps    │
        └──────────┘   └────────────┘    └──────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
            ┌──────────────┐    ┌─────────────────┐
            │   FastAPI    │    │  React Frontend  │
            │   Backend    │    │  + Three.js 3D   │
            │  15 endpoints│    │  + Recharts      │
            │  AI Chatbot  │◄──│  + Framer Motion  │
            └──────────────┘    └─────────────────┘
```

---

## 🔥 Key Insights

### 1. Late Aircraft Cascading Is the #1 Delay Driver (39%)
Not weather, not air traffic control — **late-arriving aircraft from prior flights** cause the largest share of delay minutes. This operational inefficiency ripples through airline schedules, creating cascade effects.

**→ Recommendation:** Implement buffer scheduling between aircraft rotations, especially at hub airports.

### 2. Carrier-Controllable Factors Dwarf Weather Impact
Carrier issues (maintenance, crew, operations) account for **36% of delay minutes** while weather accounts for only **5.3%**. Combined, carrier + late aircraft = **75% of all delays**.

**→ Recommendation:** Shift investment from weather prediction systems to ground operations and crew management.

### 3. Early Morning Flights Have the Best On-Time Rates
Flights between 6–9 AM have **<15% delay rates**, while evening flights (6–9 PM) exceed **28%**. Delays compound throughout the day.

**→ Recommendation:** Prioritize morning departures for time-sensitive travelers; redistribute capacity from evening peaks.

### 4. Regional Carriers Outperform Major Airlines
Republic Airways (85.6%), PSA Airlines (85.3%), and Endeavor Air (84.5%) all outperform every major carrier. Simpler hub-and-spoke operations = fewer cascade failure points.

**→ Recommendation:** Major airlines should study regional carrier scheduling practices for operational improvement.

### 5. Summer Months Show 25% Higher Delay Rates
June and July consistently show the highest delay rates, driven by thunderstorm season and peak travel demand.

**→ Recommendation:** Pre-position extra crew and aircraft during summer months; build weather contingency buffers.

### 6. Hub Airports Manage Scale Efficiently
Despite handling 100K+ flights, Atlanta (ATL), Dallas (DFW), and Denver (DEN) maintain competitive delay rates — demonstrating that volume alone doesn't cause delays.

**→ Recommendation:** Smaller airports with disproportionate delays should adopt hub airport slot management practices.

---

## 📊 Dashboard Preview

### Interactive Web Dashboard (React + Recharts)
![Insights Page](docs/screenshots/insights.png)

### AI Chatbot with Real-Time Query Execution
![Chatbot](docs/screenshots/chatbot.png)

### Power BI Executive Dashboard
![Power BI](docs/screenshots/powerbi.png)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Database** | DuckDB | OLAP analytics on 2.76M rows |
| **SQL** | DuckDB SQL | CTEs, window functions, materialized views |
| **Python** | Pandas, Matplotlib, Seaborn | EDA, data cleaning, visualization |
| **ML** | Scikit-learn, SHAP | Delay prediction model (Random Forest) |
| **Excel** | XlsxWriter + Excel | Pivot tables, basic dashboard |
| **Power BI** | Power BI Desktop | Executive dashboard with DAX measures |
| **Backend** | FastAPI + Uvicorn | REST API (15 endpoints + chatbot) |
| **Frontend** | React + TypeScript | SPA with routing and state management |
| **3D** | Three.js / React Three Fiber | Animated globe on landing page |
| **Charts** | Recharts | Interactive data visualizations |
| **Animation** | Framer Motion | Page transitions, scroll animations |
| **Styling** | Tailwind CSS v4 | Utility-first responsive design |

---

## 📂 Project Structure

```
flight-delay-analytics/
├── data/
│   ├── raw/flights/          # BTS On-Time Performance CSVs
│   ├── raw/weather/          # Weather data (optional)
│   ├── reference/            # Airport reference data
│   └── processed/            # DuckDB database (flights.duckdb)
├── sql/
│   ├── 00_schema.sql         # Table definitions, views
│   ├── 01_data_quality.sql   # Data quality checks
│   ├── 02_exploratory.sql    # Exploratory queries
│   └── 03_advanced_analytics.sql  # Window functions, CTEs, rankings
├── python-analysis/
│   ├── 01_eda.py             # Exploratory data analysis (6 charts)
│   ├── 02_delay_analysis.py  # Delay deep-dive (7 charts)
│   ├── 03_airport_analysis.py # Airport comparison (5 charts)
│   ├── 04_seasonal_trends.py # Seasonal patterns (5 charts)
│   ├── 05_ml_model.py        # Delay prediction + SHAP (4 charts)
│   └── 06_export_excel.py    # Excel workbook generation
├── dashboard/
│   ├── excel/                # Excel dashboard
│   └── powerbi/              # Power BI files + theme JSON
├── backend/
│   ├── main.py               # FastAPI application
│   ├── config.py             # Environment configuration
│   ├── routers/
│   │   ├── analytics.py      # 11 analytics endpoints
│   │   ├── chatbot.py        # AI chatbot endpoints
│   │   └── export.py         # Data export endpoints
│   ├── services/
│   │   ├── query_engine.py   # Thread-safe DuckDB query engine
│   │   └── chatbot_engine.py # NL → SQL intent classification
│   └── models/
│       └── schemas.py        # Pydantic response models
├── frontend/
│   ├── src/
│   │   ├── pages/            # Landing, Insights, Dashboard, Chatbot
│   │   ├── components/       # Globe, KPICard, Charts, Navbar, Footer
│   │   ├── api/              # Backend API client
│   │   ├── hooks/            # React data hooks
│   │   └── theme/            # Color system
│   └── package.json
├── docs/
│   └── charts/               # 28 generated analysis charts
├── scripts/
│   └── process_data.py       # ETL pipeline
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.11+
- Node.js 18+
- Power BI Desktop (optional, for PBI dashboard)

### 1. Clone & Setup
```bash
git clone https://github.com/YOUR_USERNAME/flight-delay-analytics.git
cd flight-delay-analytics

# Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Data Setup
Download BTS On-Time Performance data from [transtats.bts.gov](https://www.transtats.bts.gov/DL_SelectFields.asp) and place CSVs in `data/raw/flights/`.

```bash
# Run ETL pipeline
python scripts/process_data.py
```

### 3. Run Analysis
```bash
python python-analysis/01_eda.py
python python-analysis/02_delay_analysis.py
python python-analysis/03_airport_analysis.py
python python-analysis/04_seasonal_trends.py
python python-analysis/05_ml_model.py
python python-analysis/06_export_excel.py
```

### 4. Start Backend API
```bash
uvicorn backend.main:app --port 8000 --reload
# API docs: http://localhost:8000/docs
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Open: http://localhost:5173
```

### 6. Power BI (Optional)
1. Open Power BI Desktop
2. Import `data/processed/*.parquet` or exported CSVs
3. Apply theme from `dashboard/powerbi/theme.json`
4. Use DAX measures from `MASTER_PLAN.md`

---

## 📈 ML Model Performance

| Metric | Value |
|--------|-------|
| Accuracy | 65.6% |
| ROC-AUC | 0.69 |
| Precision | 33.2% |
| Recall | 61.3% |

The model intentionally favors **recall** (catching actual delays) over precision, as missing a delay prediction is more costly than a false alarm. Top features: departure delay, hour of day, carrier code, and distance.

---

## 💼 Business Impact

| Recommendation | Estimated Impact |
|---------------|-----------------|
| Buffer scheduling between rotations | Reduce cascade delays by ~15% |
| Morning slot optimization | Lower avg delay by 8-12 min |
| Carrier operations investment | Address 75% of controllable delays |
| Summer crew pre-positioning | Reduce seasonal peak delays by ~10% |
| Hub best-practice adoption | Improve regional airport efficiency |

---

## 👤 Author

**Mudit** — Data Engineer & Analyst

---

*Built with data from the U.S. Bureau of Transportation Statistics (BTS)*
