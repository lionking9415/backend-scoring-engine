"""
Start the BEST Galaxy Scoring Engine API server with Supabase persistence.
Usage: python3 run_server.py [--no-db] [--port PORT]
"""

import argparse
import uvicorn
from scoring_engine.api import create_app


def main():
    parser = argparse.ArgumentParser(description="BEST Galaxy Scoring Engine API")
    parser.add_argument("--no-db", action="store_true", help="Run without Supabase (in-memory mode)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    args = parser.parse_args()

    use_database = not args.no_db
    app = create_app(use_database=use_database)

    mode = "in-memory" if args.no_db else "Supabase"
    print(f"Starting BEST Galaxy API on {args.host}:{args.port} ({mode} mode)")
    print(f"Docs: http://localhost:{args.port}/docs")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
