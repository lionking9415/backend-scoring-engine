"""
Sample runner script — demonstrates the full scoring engine pipeline.
Generates a sample assessment, processes it through all lenses,
and outputs the complete JSON result.
"""

import json
import random
import logging
from scoring_engine.engine import process_assessment, process_multi_lens
from scoring_engine.item_dictionary import ITEM_DICTIONARY

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


def generate_sample_responses(seed=42):
    """Generate a realistic set of 52 responses with some variance."""
    random.seed(seed)
    responses = []
    for item in ITEM_DICTIONARY:
        responses.append({
            "item_id": item["item_id"],
            "response": random.randint(1, 4),
        })
    return responses


def main():
    print("=" * 70)
    print("  BEST Executive Function Galaxy Assessment™ — Sample Run")
    print("=" * 70)

    responses = generate_sample_responses()

    # --- Single Lens Processing ---
    print("\n📊 Processing single lens: STUDENT_SUCCESS\n")
    result = process_assessment(
        user_id="sample_user_001",
        report_type="STUDENT_SUCCESS",
        responses=responses,
        demographics={"age": 20, "role": "student", "environment": "university"},
    )

    # Print key results
    cs = result['construct_scores']
    print(f"  Quadrant:      {result['load_framework']['quadrant']}")
    print(f"  Load State:    {result['load_framework']['load_state']}")
    print(f"  Load Balance:  {result['load_framework']['load_balance']}")
    print(f"  PEI Score (domain-weighted): {cs['PEI_score']}")
    print(f"  BHP Score (domain-weighted): {cs['BHP_score']}")
    print(f"  PEI Score (per-item legacy): {cs.get('PEI_score_by_item', 'N/A')}")
    print(f"  BHP Score (per-item legacy): {cs.get('BHP_score_by_item', 'N/A')}")
    print(f"  Completion:    {result['metadata']['completion_rate']:.0%}")
    print(f"  Low Confidence:{result['metadata']['low_confidence']}")

    # Archetype
    arch = result.get('archetype', {})
    print(f"\n🎭 Archetype: {arch.get('archetype_id', 'N/A')} (confidence: {arch.get('confidence', 'N/A')})")
    print(f"   {arch.get('description', '')}")

    print("\n📈 Domain Profiles:")
    for d in result["domains"]:
        print(f"    #{d['rank']} {d['name']:35s} → {d['score']:.3f} ({d['classification']})")

    print(f"\n  Strengths:     {result['summary']['top_strengths']}")
    print(f"  Growth Edges:  {result['summary']['growth_edges']}")

    if "interpretation" in result:
        print("\n📝 Executive Summary:")
        print(f"  {result['interpretation']['executive_summary']}")

        print("\n📝 Quadrant Interpretation:")
        print(f"  {result['interpretation']['quadrant_interpretation']}")

        print("\n📝 PEI vs BHP Interpretation:")
        print(f"  {result['interpretation']['pei_bhp_interpretation']}")

    # Save full JSON
    with open("sample_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\n💾 Full output saved to sample_output.json")

    # --- Multi-Lens Processing ---
    print("\n" + "=" * 70)
    print("  Multi-Lens Processing (Same Data, 4 Report Types)")
    print("=" * 70)

    multi = process_multi_lens(
        user_id="sample_user_001",
        responses=responses,
    )

    for lens, report in multi["reports"].items():
        q = report["load_framework"]["quadrant"]
        interp = report["interpretation"]["executive_summary"][:80]
        print(f"\n  🔹 {lens}")
        print(f"    Quadrant: {q}")
        print(f"    Summary:  {interp}...")

    # Save multi-lens output
    with open("sample_multi_output.json", "w") as f:
        json.dump(multi, f, indent=2)
    print("\n💾 Multi-lens output saved to sample_multi_output.json")

    # --- API Info ---
    print("\n" + "=" * 70)
    print("  REST API")
    print("=" * 70)
    print("  To start the API server:")
    print("    python3 -m uvicorn scoring_engine.api:app --reload --port 8000")
    print("  Endpoints:")
    print("    POST /api/v1/assess           — Submit assessment")
    print("    GET  /api/v1/results/{id}     — Retrieve result by ID")
    print("    GET  /api/v1/results/user/{uid} — User results")
    print("    GET  /api/v1/health           — Health check")
    print("    GET  /docs                    — Interactive API docs")


if __name__ == "__main__":
    main()
