# ✈️ AIRLINE ANALYTICS PLATFORM — MASTER EXECUTION PLAN
## McKinsey-Level Portfolio Project

---

# 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ BTS DOT  │    │ Weather  │    │ Airport  │    │  Indian  │          │
│  │ 6M+ rows │    │  NOAA    │    │ OurAirp  │    │  DGCA    │          │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘          │
│       └───────────────┴──────────────┴──────────────┘                  │
│                        ▼                                                │
│  ┌─────────────────────────────────────────────┐                       │
│  │     ETL Pipeline (Python/Pandas/Parquet)    │                       │
│  └─────────────────┬───────────────────────────┘                       │
│                    ▼                                                    │
│  ┌─────────────────────────────────────────────┐                       │
│  │          DuckDB Analytics Database           │                       │
│  │  • Fact: flights (6M+ rows)                 │                       │
│  │  • Dim: airports, carriers, calendar         │                       │
│  │  • Views: daily, monthly, route metrics     │                       │
│  └─────────────────┬───────────────────────────┘                       │
└────────────────────┼────────────────────────────────────────────────────┘
                     │
┌────────────────────┼────────────────────────────────────────────────────┐
│                    ▼       ANALYTICS LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  SQL     │  │  Python  │  │  Excel   │  │ Power BI │               │
│  │ Analysis │  │  EDA+ML  │  │ Pivots   │  │Dashboard │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
└───────┼─────────────┼─────────────┼──────────────┼──────────────────────┘
        └─────────────┴─────────────┴──────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────────────────┐
│                     ▼      APPLICATION LAYER                            │
│  ┌──────────────────────────────────────┐                               │
│  │   FastAPI Backend (Python)           │                               │
│  │   • /api/analytics/* endpoints       │                               │
│  │   • /api/chatbot/* endpoint          │                               │
│  │   • DuckDB query engine              │                               │
│  └──────────────────┬───────────────────┘                               │
│                     │                                                   │
│  ┌──────────────────▼───────────────────┐                               │
│  │   React Frontend (TypeScript)        │                               │
│  │   • React Three Fiber (3D)           │                               │
│  │   • Recharts / Nivo (charts)         │                               │
│  │   • Framer Motion (animations)       │                               │
│  │   • AI Chatbot Interface             │                               │
│  └──────────────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 📋 PHASE BREAKDOWN

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 0: DATA ACQUISITION (Day 1)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS (You Must Do)

#### 0A. Download BTS Flight Data (PRIMARY — 6M+ rows)
**Source:** https://www.transtats.bts.gov/DL_SelectFields.asp?gnoession_ID=6&Table_ID=236
- Select "Reporting Carrier On-Time Performance (1987-present)"
- **Select these fields** (EXACTLY):
  ```
  Year, Quarter, Month, DayofMonth, DayOfWeek, FlightDate,
  Reporting_Airline, IATA_CODE_Reporting_Airline, Tail_Number,
  Flight_Number_Reporting_Airline,
  Origin, OriginCityName, OriginState,
  Dest, DestCityName, DestState,
  CRSDepTime, DepTime, DepDelay, DepDelayMinutes, DepDel15, DepTimeBlk,
  TaxiOut, WheelsOff, WheelsOn, TaxiIn,
  CRSArrTime, ArrTime, ArrDelay, ArrDelayMinutes, ArrDel15, ArrTimeBlk,
  Cancelled, CancellationCode, Diverted,
  CRSElapsedTime, ActualElapsedTime, AirTime, Flights, Distance, DistanceGroup,
  CarrierDelay, WeatherDelay, NASDelay, SecurityDelay, LateAircraftDelay
  ```
- Download **Jan 2023 → Dec 2024** (24 monthly files ≈ 6.5M rows each year)
- Save each CSV to: `data/raw/flights/`

**WHY MANUAL:** BTS requires clicking through a web form with CAPTCHA-like behavior. No direct API.

#### 0B. Download Airport Reference Data
**Source:** https://ourairports.com/data/airports.csv
- Download directly (single CSV)
- Save to: `data/reference/airports.csv`

**This one Claude can help download** — but verify it works.

#### 0C. Download Weather Data (OPTIONAL BUT IMPRESSIVE)
**Source:** https://www.ncei.noaa.gov/access/search/data-search/global-hourly
- OR use Kaggle: https://www.kaggle.com/datasets/sobhanmoosavi/us-weather-events
- Save to: `data/raw/weather/`

#### 0D. Indian Aviation Data (FOR COMPARISON SECTION)
**Source:** https://www.kaggle.com/datasets/anshulmehtakaggl/dgca-airline-data-india
- OR: https://data.gov.in/search?title=aviation
- Save to: `data/raw/india/`

### 🟢 CLAUDE TASKS (I Will Do)
- ✅ Already created: `scripts/process_data.py` (ETL pipeline)
- ✅ Already created: `sql/00_schema.sql` (DuckDB views)
- ✅ Already created: Directory structure, config, requirements

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 1: DATA ENGINEERING & SQL (Days 2-3)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS
| Task | What You Do | Time |
|------|-------------|------|
| Run ETL | `cd flight-delay-analytics && python scripts/process_data.py` | 5 min |
| Verify DuckDB | Open DuckDB CLI or run test query to confirm data loaded | 2 min |

### 🟢 CLAUDE TASKS
| Task | What Claude Builds | Status |
|------|-------------------|--------|
| ETL Pipeline | `scripts/process_data.py` — CSV → Parquet → DuckDB | ✅ Done |
| Schema SQL | `sql/00_schema.sql` — Views for daily, carrier, route | ✅ Done |
| Data Quality SQL | `sql/01_data_quality.sql` — Null checks, distributions | ✅ Done |
| Exploratory SQL | `sql/02_exploratory.sql` — Deep analysis queries | ✅ Done |
| **Advanced SQL** | `sql/03_advanced_analytics.sql` — Window functions, rankings, CTEs | 🔜 Build |
| **Weather Join** | `scripts/merge_weather.py` — Join weather data to flights | 🔜 Build |
| **Indian Data** | `scripts/process_india.py` — Clean Indian aviation data | 🔜 Build |

### SQL Files Claude Will Create:

#### `sql/03_advanced_analytics.sql` — The Interview Killer
```sql
-- Top 5 airlines by on-time performance using RANK()
-- Delay cascade analysis using LAG() window function
-- Airport congestion scoring with percentile ranks
-- Month-over-month delay trend with moving averages
-- Route-level delay decomposition (weather vs carrier vs NAS)
-- Hub airport efficiency comparison
-- Day-of-week × Hour-of-day delay heatmap data
-- Cancellation pattern analysis by season
-- Carrier market share vs delay correlation
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 2: PYTHON ANALYSIS & ML (Days 3-5)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS
| Task | What You Do | Time |
|------|-------------|------|
| Run notebooks | Execute Jupyter notebooks Claude creates | 10 min |
| Review charts | Look at generated visualizations, suggest tweaks | 15 min |
| Screenshot best charts | Save PNGs for README and presentation | 5 min |

### 🟢 CLAUDE TASKS
| Task | File | Description |
|------|------|-------------|
| EDA Notebook | `python-analysis/01_eda.ipynb` | Distributions, correlations, outliers |
| Delay Deep Dive | `python-analysis/02_delay_analysis.ipynb` | Weather vs Carrier vs NAS decomposition |
| Airport Analysis | `python-analysis/03_airport_analysis.ipynb` | Hub comparison, efficiency scoring |
| Seasonal Analysis | `python-analysis/04_seasonal_trends.ipynb` | Monthly patterns, holiday impact |
| Indian Comparison | `python-analysis/05_india_comparison.ipynb` | DGCA data analysis |
| ML Model | `python-analysis/06_delay_prediction.ipynb` | Random Forest delay predictor + SHAP |
| Export for Excel | `python-analysis/07_export_excel.py` | Generate Excel with pivot tables |
| Chart Generator | `python-analysis/utils/chart_styles.py` | McKinsey-style chart formatting |

### McKinsey-Style Charts Claude Will Generate:
```
• Muted color palette (navy #1B3A5C, accent #E85D3A, neutral grays)
• Clean grid lines (light gray, no box border)
• Clear title + subtitle pattern:
    Title: "Evening Flights Show 32% Higher Delay Rates"
    Subtitle: "Hourly arrival delay rate, US domestic flights 2023-2024"
• Source attribution at bottom left
• Minimal chart junk — no 3D effects, no gradient fills
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 3: EXCEL DASHBOARD (Day 5)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS
| Task | What You Do | Time |
|------|-------------|------|
| Open in Excel | Open the .xlsx Claude generates | 1 min |
| Create Pivot Tables | Use the "Analysis" sheet data to create pivots | 20 min |
| Format Dashboard | Apply colors, alignment per Claude's layout guide | 15 min |
| Add Slicers | Insert slicers for Year, Carrier, Airport | 10 min |
| Screenshot | Save dashboard screenshot for README | 2 min |

**WHY MANUAL:** Excel pivot tables and formatting require the desktop app.
Claude generates the DATA and LAYOUT GUIDE — you build the visual.

### 🟢 CLAUDE TASKS
| Task | Description |
|------|-------------|
| Generate .xlsx | Pre-formatted Excel with Summary, Raw Data, Pivot Source sheets |
| Layout Guide | Exact cell positions, colors, chart types for the dashboard |
| Pivot Specifications | Exact field placements for each pivot table |

### Excel Layout Claude Will Specify:
```
Sheet: "Dashboard"
┌────────────────────────────────────────────────────────┐
│ Row 1-2: Title bar (dark navy background)              │
│ "Airline Operations Performance Dashboard"              │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│ Row 3-5: │ Total    │ On-Time  │ Delay    │ Cancel     │
│ KPI Cards│ Flights  │ Rate     │ Rate     │ Rate       │
│          │ 6.2M     │ 79.8%    │ 20.2%    │ 2.1%      │
├──────────┴──────────┴──────────┼──────────┴────────────┤
│ Row 6-18: Delay by Hour        │ Top 10 Airlines       │
│ (Bar chart)                    │ (Horizontal bar)      │
├────────────────────────────────┼───────────────────────┤
│ Row 19-30: Monthly Trend       │ Delay Cause Breakdown │
│ (Line chart)                   │ (Pie/Donut chart)     │
└────────────────────────────────┴───────────────────────┘
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 4: POWER BI DASHBOARD (Days 6-7)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS (This phase is mostly manual)
| Task | What You Do | Time |
|------|-------------|------|
| Open Power BI Desktop | Download free from Microsoft if needed | 5 min |
| Import Data | Load the Parquet or exported CSVs Claude prepares | 5 min |
| Build Dashboard | Follow Claude's EXACT layout specification below | 2-3 hrs |
| Add DAX Measures | Copy DAX formulas Claude provides | 30 min |
| Publish to Web | Power BI Service → Publish to Web → Get embed URL | 10 min |
| Screenshot | Save for README | 2 min |

**WHY MANUAL:** Power BI Desktop is a GUI application. No CLI/API for building visuals.

### 🟢 CLAUDE TASKS
| Task | Description |
|------|-------------|
| Data Export | `scripts/export_powerbi.py` — Optimized CSV/Parquet for PBI |
| DAX Measures | Complete DAX formulas for all KPIs |
| Layout Spec | Exact visual placement, colors, chart types |
| Theme JSON | Custom Power BI theme file (McKinsey style) |

### Power BI Layout Claude Will Specify:

```
PAGE 1: "Executive Overview"
┌─────────────────────────────────────────────────────────┐
│ HEADER: Airline Operations Intelligence Dashboard       │
│ Slicers: [Year ▼] [Quarter ▼] [Carrier ▼] [Airport ▼] │
├───────────┬───────────┬───────────┬─────────────────────┤
│ KPI Card  │ KPI Card  │ KPI Card  │ KPI Card            │
│ Total     │ On-Time % │ Avg Delay │ Cancel %            │
│ Flights   │           │ (min)     │                     │
├───────────┴───────────┴───────────┴─────────────────────┤
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │ Monthly Delay Trend  │  │ Delay Cause Breakdown  │    │
│  │ (Line + Area chart)  │  │ (Stacked Bar)          │    │
│  └─────────────────────┘  └────────────────────────┘    │
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────┐    │
│  │ Top 15 Airlines     │  │ Hour × Day Heatmap     │    │
│  │ (Horizontal bar)    │  │ (Matrix visual)        │    │
│  └─────────────────────┘  └────────────────────────┘    │
└──────────────────────────────────────────────────────────┘

PAGE 2: "Airport Deep Dive"
┌──────────────────────────────────────────────────────────┐
│ Map visual (bubble map of US airports, size = delay rate)│
│ Airport comparison table with conditional formatting     │
│ Route-level drilldown                                    │
└──────────────────────────────────────────────────────────┘

PAGE 3: "Delay Root Cause Analysis"
┌──────────────────────────────────────────────────────────┐
│ Waterfall: delay decomposition                           │
│ Scatter: flight volume vs delay rate                     │
│ Treemap: delay minutes by carrier                        │
└──────────────────────────────────────────────────────────┘
```

### DAX Measures Claude Will Provide:
```dax
// On-Time Rate
On-Time % =
DIVIDE(
    COUNTROWS(FILTER(flights, flights[arr_del15] = 0 && flights[cancelled] = 0)),
    COUNTROWS(FILTER(flights, flights[cancelled] = 0)),
    0
)

// Delay Rate
Delay % = 1 - [On-Time %]

// Average Delay (excluding cancelled)
Avg Delay Min =
CALCULATE(
    AVERAGE(flights[arr_delay_minutes]),
    flights[cancelled] = 0
)

// Cancellation Rate
Cancel % =
DIVIDE(
    COUNTROWS(FILTER(flights, flights[cancelled] = 1)),
    COUNTROWS(flights),
    0
)

// Year-over-Year Delay Change
YoY Delay Change =
VAR CurrentYear = [Avg Delay Min]
VAR PriorYear = CALCULATE([Avg Delay Min], SAMEPERIODLASTYEAR(dim_calendar[flight_date]))
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, 0)
```

### Power BI Theme JSON (McKinsey Style):
```json
{
  "name": "AirlineAnalytics",
  "dataColors": [
    "#1B3A5C", "#E85D3A", "#2D8EBF", "#F4A261",
    "#6C757D", "#264653", "#E76F51", "#2A9D8F"
  ],
  "background": "#FFFFFF",
  "foreground": "#1B3A5C",
  "tableAccent": "#E85D3A",
  "visualStyles": {
    "*": {
      "*": {
        "wordWrap": [{"show": true}],
        "title": [{
          "fontColor": {"solid": {"color": "#1B3A5C"}},
          "fontSize": 12,
          "fontFamily": "Segoe UI Semibold"
        }]
      }
    }
  }
}
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 5: BACKEND API (Days 7-8)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS
| Task | What You Do | Time |
|------|-------------|------|
| Get API Key | Get an Anthropic/OpenAI API key for chatbot | 5 min |
| Create .env | Add `LLM_API_KEY=sk-...` to `.env` file | 1 min |
| Test API | Run `uvicorn backend.main:app --reload` and test | 5 min |

### 🟢 CLAUDE TASKS (Almost everything)
| Task | File | Description |
|------|------|-------------|
| Main App | `backend/main.py` | FastAPI app with CORS, routers |
| Analytics Router | `backend/routers/analytics.py` | 15+ analytics endpoints |
| Chatbot Router | `backend/routers/chatbot.py` | NL query → SQL → response |
| Query Service | `backend/services/query_engine.py` | Safe DuckDB query execution |
| Chatbot Service | `backend/services/chatbot_engine.py` | LLM + SQL intent mapping |
| Data Models | `backend/models/schemas.py` | Pydantic response models |
| Export Router | `backend/routers/export.py` | CSV/JSON data export |

### API Endpoints Claude Will Build:
```
GET  /api/v1/analytics/overview          → KPI summary
GET  /api/v1/analytics/delays/by-hour    → Hourly delay heatmap data
GET  /api/v1/analytics/delays/by-carrier → Airline ranking
GET  /api/v1/analytics/delays/by-airport → Airport comparison
GET  /api/v1/analytics/delays/causes     → Weather vs Carrier vs NAS
GET  /api/v1/analytics/delays/trends     → Monthly time series
GET  /api/v1/analytics/delays/seasonal   → Season-level patterns
GET  /api/v1/analytics/routes/top        → Best/worst routes
GET  /api/v1/analytics/cancellations     → Cancellation analysis
GET  /api/v1/analytics/india/comparison  → Indian airport comparison
GET  /api/v1/analytics/predictions       → ML model predictions

POST /api/v1/chatbot/query               → Natural language query
GET  /api/v1/chatbot/suggestions         → Sample questions

GET  /api/v1/export/{format}             → Download data as CSV/JSON
GET  /health                             → Health check
```

### Chatbot Architecture:
```
User Query: "Which airline has the least delays?"
         │
         ▼
┌─────────────────────────┐
│  Intent Classification   │
│  (keyword matching +     │
│   LLM if available)      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Query Template Mapping  │
│  "least delays" →        │
│  airline_ranking_query   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  DuckDB Execution        │
│  (parameterized query)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Response Formatting     │
│  • Text insight          │
│  • Data table            │
│  • Chart data (optional) │
└─────────────────────────┘
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 6: 3D FRONTEND WEBSITE (Days 8-11)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS
| Task | What You Do | Time |
|------|-------------|------|
| Power BI Embed URL | Get the publish-to-web URL from Power BI Service | 10 min |
| Update .env | Add `VITE_POWERBI_EMBED_URL=...` | 1 min |
| Test locally | `cd frontend && npm run dev` | 2 min |
| Visual review | Check animations, responsiveness | 15 min |

### 🟢 CLAUDE TASKS (Almost everything)
| Task | File | Description |
|------|------|-------------|
| App Shell | `frontend/src/App.tsx` | Router + layout + page structure |
| Landing Page | `frontend/src/pages/Landing.tsx` | 3D globe + hero section |
| Insights Page | `frontend/src/pages/Insights.tsx` | Key findings with charts |
| Dashboard Page | `frontend/src/pages/Dashboard.tsx` | PBI embed + live charts |
| Chatbot Page | `frontend/src/pages/Chatbot.tsx` | Chat interface |
| 3D Globe | `frontend/src/components/Globe.tsx` | Animated globe with routes |
| 3D Particles | `frontend/src/components/Particles.tsx` | Background particle system |
| Navbar | `frontend/src/components/Navbar.tsx` | Sticky nav with scroll |
| KPI Cards | `frontend/src/components/KPICard.tsx` | Animated counter cards |
| Charts | `frontend/src/components/charts/*` | Recharts/Nivo wrappers |
| Chat Widget | `frontend/src/components/ChatWidget.tsx` | Chat bubble + messages |
| API Client | `frontend/src/api/client.ts` | Axios API wrapper |
| Hooks | `frontend/src/hooks/useAnalytics.ts` | Custom data hooks |
| Styles | `frontend/src/index.css` | Tailwind + custom styles |
| Theme | `frontend/src/theme/colors.ts` | Consistent color system |

### Website Sections:
```
┌──────────────────────────────────────────────────────┐
│  SECTION 1: HERO (Full viewport)                      │
│  ┌────────────────────────────────────────────────┐  │
│  │         🌍 3D ROTATING GLOBE                   │  │
│  │      (flight paths animated on globe)           │  │
│  │                                                  │  │
│  │  "Airline Operations Intelligence Platform"      │  │
│  │  Analyzing 6.5M+ flights to uncover             │  │
│  │  operational inefficiencies                      │  │
│  │                                                  │  │
│  │  [Explore Insights ↓]  [View Dashboard]         │  │
│  └────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────┤
│  SECTION 2: KPI OVERVIEW (Scroll-triggered)          │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                   │
│  │6.5M │ │79.8%│ │20.2%│ │ 2.1%│                    │
│  │Flts │ │OnTm │ │Dly  │ │Cncl │                    │
│  └─────┘ └─────┘ └─────┘ └─────┘                    │
│  (animated count-up on scroll into view)             │
├──────────────────────────────────────────────────────┤
│  SECTION 3: KEY INSIGHTS (McKinsey slide style)      │
│  ┌──────────────────┐  ┌──────────────────┐         │
│  │ "Evening flights  │  │ "Carrier issues  │         │
│  │  (6-9 PM) show   │  │  cause 42% of    │         │
│  │  32% higher      │  │  all delays —     │         │
│  │  delay rates"    │  │  not weather"     │         │
│  │  [Chart below]   │  │  [Chart below]   │         │
│  └──────────────────┘  └──────────────────┘         │
├──────────────────────────────────────────────────────┤
│  SECTION 4: INTERACTIVE DASHBOARD                    │
│  ┌──────────────────────────────────────────────┐   │
│  │  Power BI Embed (iframe)                      │   │
│  │  + Live React charts from API                 │   │
│  └──────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────┤
│  SECTION 5: AI CHATBOT                               │
│  ┌──────────────────────────────────────────────┐   │
│  │  💬 "Ask anything about flight delays..."     │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │ User: "Which airline has least delays?"│  │   │
│  │  │ Bot:  "Based on 2023-24 data,          │  │   │
│  │  │        Hawaiian Airlines (HA) leads    │  │   │
│  │  │        with 87.2% on-time rate..."     │  │   │
│  │  │        [Shows bar chart]               │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────┤
│  SECTION 6: METHODOLOGY                              │
│  Architecture diagram, tech stack icons, data flow   │
├──────────────────────────────────────────────────────┤
│  FOOTER                                              │
│  GitHub link, contact, credits                       │
└──────────────────────────────────────────────────────┘
```

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## PHASE 7: DEPLOYMENT & POLISH (Days 11-12)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 🔴 MANUAL TASKS
| Task | What You Do | Time |
|------|-------------|------|
| GitHub repo | Create repo, push code | 10 min |
| Vercel deploy | Connect frontend repo to Vercel | 10 min |
| Railway/Render | Deploy backend API | 15 min |
| Test live | Verify everything works end-to-end | 15 min |
| Screenshots | Take final screenshots for README | 10 min |

### 🟢 CLAUDE TASKS
| Task | File | Description |
|------|------|-------------|
| README | `README.md` | Full professional README |
| .gitignore | `.gitignore` | Proper ignores |
| Docker | `Dockerfile`, `docker-compose.yml` | Containerization |
| Deploy configs | `vercel.json`, `Procfile` | Deploy configurations |
| Architecture SVG | `docs/architecture.svg` | System diagram |

---

# 🔌 CONNECTORS & TOOLS FOR CLAUDE TO HELP

## How to Use Claude Most Effectively at Each Phase:

### Phase 0 (Data):
```
YOU: Download CSVs manually from BTS website
CLAUDE: "Here are the exact steps and field selections"
CONNECTOR: None needed — manual browser download
```

### Phase 1 (SQL + ETL):
```
YOU: Run `python scripts/process_data.py`
CLAUDE: Writes all SQL files, ETL scripts
CONNECTOR: Claude reads/writes files directly in your project
```

### Phase 2 (Python Analysis):
```
YOU: Run Jupyter notebooks, screenshot best charts
CLAUDE: Writes complete notebooks with analysis code
CONNECTOR: Claude creates .ipynb files → you run in Jupyter
         Claude creates .py scripts → you run in terminal
```

### Phase 3 (Excel):
```
YOU: Open Excel, build pivot tables + dashboard
CLAUDE: Generates .xlsx with data + layout guide
CONNECTOR: Use /xlsx skill — Claude generates Excel files directly
```

### Phase 4 (Power BI):
```
YOU: Build entire dashboard in Power BI Desktop
CLAUDE: Provides DAX formulas, layout spec, theme JSON, data exports
CONNECTOR: Claude generates Power BI-ready CSVs + theme file
         (Power BI has no API for dashboard creation)
```

### Phase 5 (Backend):
```
YOU: Run server, set API key in .env
CLAUDE: Writes ALL backend code
CONNECTOR: Claude reads/writes files directly
```

### Phase 6 (Frontend):
```
YOU: Run `npm run dev`, test in browser
CLAUDE: Writes ALL frontend code
CONNECTOR: Claude reads/writes files + preview tool for testing
```

### Phase 7 (Deploy):
```
YOU: Push to GitHub, connect Vercel/Railway
CLAUDE: Writes README, Docker files, deploy configs
CONNECTOR: Claude can use Vercel MCP connector for deployment
```

---

# 📊 EFFORT SPLIT SUMMARY

| Phase | Claude Does | You Do | Your Time |
|-------|------------|--------|-----------|
| 0. Data | 5% | 95% (downloads) | 1-2 hours |
| 1. SQL/ETL | 95% | 5% (run scripts) | 15 min |
| 2. Python | 90% | 10% (run + review) | 30 min |
| 3. Excel | 40% | 60% (build in app) | 45 min |
| 4. Power BI | 30% | 70% (build in app) | 3 hours |
| 5. Backend | 95% | 5% (run + test) | 15 min |
| 6. Frontend | 95% | 5% (run + review) | 20 min |
| 7. Deploy | 70% | 30% (push + config) | 45 min |
| **TOTAL** | **~75%** | **~25%** | **~7 hours** |

---

# 🏢 HOW McKINSEY / BCG EMPLOYEES PRESENT PROJECTS

## Their Resume Format:
```
EXPERIENCE
───────────────────────────────────────────────
[Company Name] | [Role] | [Date Range]

• Built airline operations analytics platform analyzing 6.5M+ flight
  records, identifying $2.3B in annual delay-related revenue losses
  across 15 major US carriers

• Developed delay root-cause decomposition model revealing carrier
  operational inefficiencies (42% of delays) dominate weather impact
  (18%), contrary to industry assumptions

• Designed executive dashboard reducing C-suite reporting time by 60%,
  adopted by 3 VP-level stakeholders for quarterly operational reviews

• Engineered ML prediction model (Random Forest, 82% accuracy) for
  flight delay forecasting, enabling proactive crew scheduling

KEY IMPACT: Recommendations projected to reduce average departure
delays by 12 minutes across hub airports, representing ~$180M annual
savings for a major carrier
```

## Their Presentation Style:
```
SLIDE 1: "The Problem"
→ "Flight delays cost US airlines $28.2B annually"
→ One powerful statistic, one clean visual

SLIDE 2: "Our Approach"
→ Architecture diagram showing data flow
→ "Analyzed 6.5M flights across 350+ airports"

SLIDE 3: "Key Finding #1"
→ "Evening flights (6-9 PM) show 32% higher delays"
→ Clean chart with callout

SLIDE 4: "Key Finding #2"
→ "Carrier inefficiencies, not weather, drive most delays"
→ Stacked bar showing delay decomposition

SLIDE 5: "Recommendations"
→ 3 actionable bullet points
→ Estimated impact

SLIDE 6: "Implementation Roadmap"
→ 30/60/90 day plan
```

## What Makes It McKinsey-Level:
```
❌ "I analyzed airline data"
✅ "I identified $2.3B in addressable operational inefficiencies"

❌ "I built a dashboard"
✅ "I designed an executive decision-support system adopted by VP stakeholders"

❌ "I used Python and SQL"
✅ "I engineered an end-to-end analytics pipeline processing 6.5M records"

❌ "Delhi has the most delays"
✅ "Delhi's evening congestion pattern suggests infrastructure capacity gaps,
    not weather, as the primary delay driver — addressable through slot
    optimization and strategic scheduling shifts"
```

## The "So What" Framework (McKinsey's Secret):
```
Every insight MUST answer: "So what? What should we DO about it?"

INSIGHT: Evening flights have higher delays
SO WHAT: Airlines should redistribute capacity to morning slots

INSIGHT: Carrier delays dominate weather delays
SO WHAT: Investment should shift from weather systems to
         ground operations and crew management

INSIGHT: Hub airports have disproportionate delays
SO WHAT: Spoke routing strategies could reduce cascade effects
```

---

# 🎯 KEY INSIGHTS YOU SHOULD HIGHLIGHT
(Claude will calculate exact numbers from your data)

| # | Insight | Business Implication |
|---|---------|---------------------|
| 1 | Evening flights (6-9 PM) show ~30% higher delay rates | Reschedule capacity to morning windows |
| 2 | Carrier inefficiencies cause ~40% of delays vs ~18% weather | Invest in operations, not just weather systems |
| 3 | Top 10 hub airports account for ~60% of all delay minutes | Target hub improvements for maximum ROI |
| 4 | Late aircraft cascading is the fastest-growing delay cause | Implement buffer scheduling between rotations |
| 5 | Summer (Jun-Aug) delays are ~25% higher than other seasons | Pre-position extra crew during peak season |
| 6 | Budget carriers have paradoxically better on-time rates | Simplied operations = fewer delay cascade points |

---

# 📋 YOUR EXACT EXECUTION CHECKLIST

## Week 1:
- [ ] Day 1: Download ALL data (BTS, airports, weather, India)
- [ ] Day 1: Run ETL pipeline
- [ ] Day 2: Ask Claude to build SQL + Python analysis
- [ ] Day 3: Run all notebooks, review insights
- [ ] Day 4: Ask Claude to build Excel export
- [ ] Day 4: Build Excel dashboard (manual in Excel)
- [ ] Day 5: Start Power BI dashboard (manual)

## Week 2:
- [ ] Day 6: Finish Power BI dashboard
- [ ] Day 7: Ask Claude to build Backend API
- [ ] Day 8: Ask Claude to build Frontend website
- [ ] Day 9: Test everything end-to-end
- [ ] Day 10: Ask Claude to write README + deploy configs
- [ ] Day 10: Deploy to Vercel + Railway
- [ ] Day 11: Polish, screenshots, final README
- [ ] Day 12: Push to GitHub, share

---

# 💬 EXACT PROMPTS TO GIVE CLAUDE AT EACH PHASE

## After downloading data:
```
"I've downloaded the BTS flight data CSVs to data/raw/flights/
and airports.csv to data/reference/. Please run the ETL pipeline
and then build the advanced SQL analytics file with window functions,
rankings, and all the interview-killer queries."
```

## For Python analysis:
```
"Build the complete Python analysis notebooks:
1. EDA with McKinsey-style charts
2. Delay deep dive (weather vs carrier decomposition)
3. Airport efficiency analysis
4. Seasonal trends
5. Indian airport comparison
6. ML delay prediction model with SHAP explanations
Use the DuckDB database at data/processed/flights.duckdb"
```

## For Backend:
```
"Build the complete FastAPI backend with:
- Analytics API endpoints for all dashboard data
- AI chatbot that maps natural language to SQL queries
- DuckDB query engine with safety limits
- Pydantic models for all responses"
```

## For Frontend:
```
"Build the complete React frontend with:
- 3D globe landing page using React Three Fiber
- Insights section with animated KPI cards
- Dashboard page with Power BI embed + live charts
- Chatbot interface with message history
- Smooth scroll animations with Framer Motion
- Tailwind CSS styling, dark navy + orange accent theme"
```

## For Final Polish:
```
"Write the professional README.md with:
- Business-focused problem statement
- Architecture diagram (ASCII art)
- Key insights (the strong McKinsey-style ones)
- Business recommendations
- Tech stack
- How to run
- Screenshots section (I'll add images later)
Also create Docker files and deployment configs."
```

---

# 🚀 FINAL QUALITY CHECKLIST

Before submitting / sharing:

- [ ] README has business-focused problem statement (not technical)
- [ ] README has 5+ strong insights with "So What" implications
- [ ] README has architecture diagram
- [ ] Dashboard looks like McKinsey consulting output
- [ ] SQL includes window functions, CTEs, advanced queries
- [ ] Python analysis has clean, well-commented notebooks
- [ ] Backend API has 10+ endpoints with proper error handling
- [ ] Frontend has smooth 3D animations (not laggy)
- [ ] Chatbot returns real data-backed answers
- [ ] Code has proper comments and docstrings
- [ ] .gitignore excludes data files, .env, venv
- [ ] No API keys committed to repo
- [ ] Project runs with clear setup instructions

---

*This plan was designed to produce a FAANG/consulting-tier portfolio project.
Follow it phase by phase. Claude handles ~75% of the code.
You handle data downloads, GUI tools (Excel/Power BI), and deployment.*
