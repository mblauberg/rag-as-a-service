#!/usr/bin/env python3
"""Test httpx redirect behavior"""
import httpx
import asyncio

async def test_redirects():
    print("Testing httpx redirect behavior...")

    # Test GET with redirect
    async with httpx.AsyncClient() as client:
        print("\n1. GET /api/v1/models (no trailing slash):")
        response = await client.get("http://localhost:8002/api/v1/models")
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        print(f"   History: {[r.status_code for r in response.history]}")

    # Test GET with follow_redirects=True explicitly
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("\n2. GET /api/v1/models with follow_redirects=True:")
        response = await client.get("http://localhost:8002/api/v1/models")
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        print(f"   History: {[r.status_code for r in response.history]}")

    # Test POST with redirect
    async with httpx.AsyncClient() as client:
        print("\n3. POST /api/v1/generate (no trailing slash):")
        payload = {"query": "test", "chunks": [], "model": "openai:gpt-4o"}
        response = await client.post("http://localhost:8002/api/v1/generate", json=payload)
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        print(f"   History: {[r.status_code for r in response.history]}")

if __name__ == "__main__":
    asyncio.run(test_redirects())
