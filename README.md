# BEST Executive Function Galaxy Assessment™ — Backend Scoring Engine

## Phase 1: Foundation (Architecture + Core Scoring Engine)

A modular, config-driven backend scoring engine for Dr. Sherilyn Crump's BEST Executive Function Galaxy Assessment™. Processes 52-question assessments (A/B/C/D format) through a PEI × BHP load interaction model with **overlapping domain contributions**, archetype assignment, and generates structured JSON outputs for report generation across 4 lenses. Includes a **FastAPI REST API** and **Supabase** persistence layer.

---

## Architecture

```
Frontend (Assessment UI)
    ↓
REST API (FastAPI)         → scoring_engine/api.py
    ↓
Validation Layer           → scoring_engine/validation.py
    ↓
Scoring Engine             → scoring_engine/scoring.py
    ↓
Domain-Weighted Indices    → scoring_engine/scoring.py (overlapping weight matrix)
    ↓
PEI × BHP Framework       → scoring_engine/framework.py
    ↓
Domain Aggregation         → scoring_engine/domains.py
    ↓
Archetype Assignment       → scoring_engine/archetypes.py
    ↓
JSON Output Generator      → scoring_engine/output.py
    ↓
AI Interpretation Layer    → scoring_engine/interpretation.py
    ↓
Supabase Storage           → scoring_engine/database.py + supabase_client.py
    ↓
Report Output (UI / PDF / Dashboard)
```

## Core Concepts

| Concept | Description |
|---------|-------------|
| **PEI** | Probability Environment Index — external environmental load |
| **BHP** | Behavioral Health Probability — internal regulatory capacity |
| **EF**  | Executive Function = f(PEI × BHP) |
| **Overlapping Domains** | Domains contribute to BOTH indices with different configurable weights |
| **Quadrants** | Q1: Aligned Flow, Q2: Capacity Strain, Q3: Overload, Q4: Underutilized |
| **Load States** | Surplus Capacity → Stable → Balanced → Emerging Strain → Critical Overload |
| **Archetypes** | 16 behavioral archetypes mapped from quadrant + load state |
| **Report Lenses** | Personal/Lifestyle, Student Success, Professional/Leadership, Family Ecosystem |

## Project Structure

```
scoring_engine/
├── __init__.py            # Package init, version
├── config.py              # ALL thresholds, domains, weight matrix, archetypes (config-driven)
├── item_dictionary.py     # 52-item coding dictionary (Section 2)
├── validation.py          # Input validation & error handling (Section 8)
├── scoring.py             # Scoring pipeline, aggregation, overlapping domain weights (Section 3, 5)
├── framework.py           # PEI × BHP quadrant/load model (Section 4)
├── domains.py             # Domain classification & AIMS mapping (Section 5)
├── archetypes.py          # 16-archetype assignment engine (Phase 1 stub)
├── output.py              # JSON output schema builder (Section 6)
├── interpretation.py      # AI narrative generation (Section 7)
├── supabase_client.py     # Supabase client singleton (credentials from .env)
├── database.py            # Supabase persistence layer (CRUD operations)
├── api.py                 # FastAPI REST API (submission + retrieval)
└── engine.py              # Main orchestrator (Section 9)

tests/
├── test_validation.py     # 19 tests — validation & error handling
├── test_scoring.py        # 20 tests — scoring pipeline
├── test_framework.py      # 16 tests — PEI × BHP framework
├── test_domains.py        # 17 tests — domain aggregation
├── test_engine.py         # 27 tests — end-to-end integration
├── test_overlapping_weights.py  # 10 tests — overlapping domain weight matrix
├── test_archetypes.py     # 12 tests — archetype assignment
├── test_api.py            # 14 tests — REST API endpoints
└── test_supabase.py       # 11 tests — Supabase integration

sample_run.py              # Demo script with sample output
supabase_migration.sql     # SQL to create tables in Supabase
.env                       # Supabase credentials (gitignored)
.env.example               # Template for .env file
```

## Quick Start

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure Supabase
cp .env.example .env
# Edit .env with your Supabase project URL and anon key

# Run the SQL migration in Supabase Dashboard → SQL Editor
# (paste contents of supabase/supabase_migration.sql)

# Run tests (146 tests)
python3 -m pytest tests/ -v

# Run sample assessment
python3 sample_run.py

# Start REST API server (in-memory mode — no Supabase needed)
python3 run_server.py --no-db

# Start REST API server (with Supabase persistence)
python3 run_server.py

# Then visit http://localhost:8000/docs for interactive API docs
```

### Frontend Setup (Optional)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Visit http://localhost:3000 to take the assessment
```

**Note**: The backend must be running on `http://localhost:8000` for the frontend to work.

## Supabase Setup

1. **Create a Supabase project** at [supabase.com](https://supabase.com)
2. **Copy credentials** to `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key-here
   ```
3. **Run the migration** — go to Supabase Dashboard → SQL Editor → paste `supabase_migration.sql` → Run
4. **Tables created**:
   - `assessment_results` — stores all scored assessments with full JSON output
   - `aims_responses` — tracks AIMS function responses (Phase 2)
5. **Row Level Security** is enabled with anon read/write policies
6. **Fallback**: If Supabase is unavailable, the API automatically falls back to in-memory storage

## Key Design Principles

1. **Separation of Concerns** — Framework config is separate from scoring logic. Change thresholds/weights in `config.py` without touching core code.
2. **Overlapping Domain Contributions** — Domains can feed BOTH PEI and BHP indices with different weights via a configurable weight matrix. This is the key architectural differentiator.
3. **Same Data, Different Interpretation** — Scoring is done ONCE. Only the report lens changes the narrative, never the scores.
4. **Deterministic** — Same input always produces same output. No rounding until final output stage.
5. **Traceable** — Every item preserves its full scoring trace: raw → adjusted → weighted → normalized.
6. **Configurable** — Thresholds, weights, domain definitions, classification bands, and archetypes are all in `config.py`.

## Overlapping Domain Weight Matrix

The key architectural feature — domains can contribute to BOTH indices with DIFFERENT weights:

```python
# In config.py — change weights here, scoring logic stays untouched
DOMAIN_INDEX_WEIGHTS = {
    "EXECUTIVE_FUNCTION_SKILLS": {"PEI": 0.0, "BHP": 1.0},       # BHP only
    "ENVIRONMENTAL_DEMANDS":     {"PEI": 1.0, "BHP": 0.0},       # PEI only
    "EMOTIONAL_REGULATION":      {"PEI": 0.3, "BHP": 1.0},       # overlapping
    "BEHAVIORAL_PATTERNS":       {"PEI": 0.0, "BHP": 1.0},       # BHP only
    "COGNITIVE_CONTROL":         {"PEI": 0.0, "BHP": 1.0},       # BHP only
    "MOTIVATIONAL_SYSTEMS":      {"PEI": 0.4, "BHP": 0.8},       # overlapping
    "INTERNAL_STATE_FACTORS":    {"PEI": 0.6, "BHP": 0.7},       # overlapping
}
```

## Scoring Pipeline

```
Raw Response
    → Direction Adjustment (reverse scoring if applicable)
    → Weight Application (default 1.0)
    → Normalization (0.0–1.0 scale)
    → Domain Aggregation (average of normalized scores per domain)
    → Index Computation (PEI & BHP via overlapping domain weight matrix)
    → Load Framework (quadrant + load state)
    → Archetype Assignment (16 archetypes)
    → JSON Output
    → AI Interpretation (narrative blocks)
```

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/assess` | Submit assessment responses, returns scored output |
| `GET` | `/api/v1/results/{id}` | Retrieve stored result by ID |
| `GET` | `/api/v1/results/user/{user_id}` | Retrieve all results for a user |
| `GET` | `/api/v1/health` | System health check |
| `GET` | `/docs` | Interactive Swagger API documentation |

### Example API Request

```bash
curl -X POST http://localhost:8000/api/v1/assess \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "report_type": "STUDENT_SUCCESS",
    "responses": [
      {"item_id": "Q01", "response": 4},
      {"item_id": "Q02", "response": 2}
    ],
    "demographics": {"age": 20, "role": "student"},
    "include_interpretation": true
  }'
```

## Python API Usage

```python
from scoring_engine.engine import process_assessment

result = process_assessment(
    user_id="user_001",
    report_type="STUDENT_SUCCESS",
    responses=[
        {"item_id": "Q01", "response": 4},
        {"item_id": "Q02", "response": 2},
        # ... all 52 items
    ],
    demographics={"age": 20, "role": "student"},
)

# result contains: metadata, construct_scores, load_framework, domains,
#   summary, archetype, items, interpretation
```

### Multi-Lens Processing

```python
from scoring_engine.engine import process_multi_lens

results = process_multi_lens(
    user_id="user_001",
    responses=[...],  # same 52 responses
)
# results["reports"]["STUDENT_SUCCESS"]
# results["reports"]["PERSONAL_LIFESTYLE"]
# results["reports"]["PROFESSIONAL_LEADERSHIP"]
# results["reports"]["FAMILY_ECOSYSTEM"]
```

## Phase 1 Milestone Benchmarks

- ✅ System correctly processes sample assessments
- ✅ Outputs accurate domain + total scores
- ✅ Config system allows adjustments without rewriting code
- ✅ Overlapping domain contributions with configurable weight matrix
- ✅ Archetype assignment (16 archetypes)
- ✅ REST API with submission and retrieval endpoints
- ✅ Supabase persistence layer (with in-memory fallback)
- ✅ 146 tests passing
- ✅ JSON output is structured, serializable, and complete
- ✅ AI interpretation layer generates lens-specific narratives
