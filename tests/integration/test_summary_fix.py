#!/usr/bin/env python3
"""Test script to verify AI summary generation works."""
import asyncio
import httpx
import sys

async def test_search_with_model():
    """Test search endpoint with model to verify summary generation."""

    # First, let's search with a model to see if summary is generated
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Perform a search with a model
            search_request = {
                "query": "test query",
                "limit": 5,
                "model": "openai:gpt-5-mini"
            }

            print("Testing search with model: openai:gpt-5-mini")
            print(f"Request: {search_request}")

            response = await client.post(
                "http://localhost:8000/api/v1/search",
                json=search_request
            )

            print(f"\nResponse status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"\nSearch results:")
                print(f"  Query: {data.get('query')}")
                print(f"  Total results: {data.get('total_results')}")
                print(f"  Model used: {data.get('model_used')}")
                print(f"  Summary: {data.get('summary')}")

                if data.get('summary') and data.get('model_used'):
                    print("\n✅ SUCCESS: AI summary is being generated!")
                    return True
                else:
                    print("\n❌ FAILURE: Summary or model_used is None")
                    print(f"Full response: {data}")
                    return False
            else:
                print(f"❌ FAILURE: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_search_with_model())
    sys.exit(0 if success else 1)
