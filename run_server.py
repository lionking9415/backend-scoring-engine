"""
Start the BEST Galaxy Scoring Engine API server with Supabase persistence.
Usage: python3 run_server.py [--no-db] [--port PORT]

On Google Cloud Run the $PORT environment variable is injected at runtime.
The CLI --port flag overrides it for local development.
"""

import argparse
import os
import uvicorn
from scoring_engine.api import create_app


def main():
    parser = argparse.ArgumentParser(description="BEST Galaxy Scoring Engine API")
    parser.add_argument("--no-db", action="store_true", help="Run without Supabase (in-memory mode)")
    parser.add_argument(
        "--port",
        type=int,
        # Cloud Run injects PORT; fall back to 8080 (Cloud Run default), then 8000 locally.
        default=int(os.environ.get("PORT", 8080)),
        help="Port to listen on (default: $PORT env var, then 8080)",
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    use_database = not args.no_db
    app = create_app(use_database=use_database)

    mode = "in-memory" if args.no_db else "Supabase"
    print(f"Starting BEST Galaxy API on {args.host}:{args.port} ({mode} mode)")
    print(f"Docs: http://localhost:{args.port}/docs")

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
