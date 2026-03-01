#!/usr/bin/env python
"""Test script for agent fixes - outputs to JSON."""

import asyncio
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.agent import run_query


async def test_query(query: str, user_id: str = "test"):
    """Run a test query and return the result."""
    result = await run_query(query, user_id=user_id)
    return {
        "query": query,
        "success": result.get("success"),
        "response": result.get("response"),
        "query_type": result.get("query_type"),
        "count": result.get("count", "N/A"),
        "company": result.get("company", "N/A"),
    }


async def main():
    """Run all tests."""
    results = []

    # Test 1: Count by brand - Volvo
    print("Test 1: Volvo 2024...")
    results.append(await test_query("quantos volvo em 2024"))

    # Test 2: Count by brand - Fiat
    print("Test 2: Fiat 2024...")
    results.append(await test_query("quantos fiat emplacaram em 2024"))

    # Test 3: Count by company - using "radiante" (exists in DB)
    print("Test 3: Radiante...")
    results.append(await test_query("radiante"))

    # Test 4: Count by company with year
    print("Test 4: Radiante 2024...")
    results.append(await test_query("quantos caminhoes a radiante comprou em 2024"))

    # Save to JSON file
    output_file = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "test_results.json"
    )
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
