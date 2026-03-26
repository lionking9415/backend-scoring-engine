# Project Structure

## Root Directory

```
backend-scoring-engine/
├── README.md                    # Main project documentation
├── CONFIGURATION_GUIDE.md       # How to configure the system
├── PROJECT_STRUCTURE.md         # This file
├── .env                         # Supabase credentials (gitignored)
├── .env.example                 # Template for .env
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── run_server.py                # CLI to start API server
├── sample_run.py                # Demo script
├── sample_output.json           # Sample assessment output
├── sample_multi_output.json     # Sample multi-lens output
│
├── scoring_engine/              # Main Python package
│   ├── __init__.py
│   ├── config.py                # System configuration (thresholds, weights, archetypes)
│   ├── item_dictionary.py       # 52 assessment questions
│   ├── validation.py            # Input validation
│   ├── scoring.py               # Scoring pipeline
│   ├── framework.py             # PEI × BHP framework
│   ├── domains.py               # Domain classification
│   ├── archetypes.py            # Archetype assignment
│   ├── output.py                # JSON output builder
│   ├── interpretation.py        # AI narrative generation
│   ├── supabase_client.py       # Supabase client singleton
│   ├── database.py              # Database CRUD operations
│   ├── api.py                   # FastAPI REST API
│   └── engine.py                # Main orchestrator
│
├── tests/                       # Test suite (146 tests)
│   ├── test_validation.py
│   ├── test_scoring.py
│   ├── test_framework.py
│   ├── test_domains.py
│   ├── test_engine.py
│   ├── test_overlapping_weights.py
│   ├── test_archetypes.py
│   ├── test_api.py
│   └── test_supabase.py
│
├── docs/                        # Documentation
│   ├── Phase 1- Section 1.md    # Architecture overview
│   ├── Phase 1- Section 2.md    # Item dictionary spec
│   ├── Phase 1- Section 3.md    # Scoring pipeline
│   ├── Phase 1- Section 4.md    # PEI × BHP framework
│   ├── Phase 1- Section 5.md    # Domain aggregation
│   ├── Phase 1- Section 6.md    # Output schema
│   ├── Phase 1- Section 7.md    # AI interpretation
│   ├── Phase 1- Section 8.md    # Validation & error handling
│   ├── Phase 1- Section 9.md    # End-to-end integration
│   ├── _Intro Mapping.md        # Initial concept mapping
│   └── 🚀 Scope of Work (1).md  # Project scope
│
├── supabase/                    # Supabase configuration
│   └── supabase_migration.sql   # SQL to create tables
│
└── frontend/                    # React frontend (optional)
    ├── public/
    │   └── index.html           # HTML template
    ├── src/
    │   ├── components/
    │   │   ├── AssessmentForm.js  # 52-question form
    │   │   └── Results.js         # Results dashboard
    │   ├── App.js               # Main app
    │   └── index.js             # Entry point
    ├── package.json
    └── README.md
```

## Quick Navigation

### For Developers
- **Getting Started**: `README.md`
- **Configuration**: `CONFIGURATION_GUIDE.md`
- **Run Tests**: `python3 -m pytest tests/ -v`
- **Start Server**: `python3 run_server.py`

### For Non-Technical Users
- **Change Settings**: Edit `scoring_engine/config.py` (see `CONFIGURATION_GUIDE.md`)
- **View Questions**: `scoring_engine/item_dictionary.py`

### For Database Setup
- **Supabase Migration**: `supabase/supabase_migration.sql`
- **Credentials**: `.env` (copy from `.env.example`)

### For Documentation
- **Phase 1 Specs**: `docs/Phase 1- Section X.md`
- **Project Scope**: `docs/🚀 Scope of Work (1).md`
- **Concept Map**: `docs/_Intro Mapping.md`
