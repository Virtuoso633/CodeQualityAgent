#!/usr/bin/env python3
from pathlib import Path
import os
import sys
import asyncio

# Add project root so imports from the repo work
sys.path.append(str(Path(__file__).parent.parent))

# Ensure API key present before importing client (some modules read settings at import time)
if not os.getenv("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY is not set. Export it first, e.g.:")
    print("   export GEMINI_API_KEY=your_new_key_here")
    raise SystemExit(2)

# Import after verifying env var
from models.gemini.gemini_client import get_gemini_client

async def run_test():
    try:
        client = get_gemini_client()
    except Exception as e:
        print(f"❌ Failed to create Gemini client: {e}")
        return 2

    try:
        ok = await client.test_connection()
        if ok:
            print("✅ Gemini API connection successful")
            return 0
        else:
            print("❌ Gemini API connection failed (unexpected response)")
            return 1
    except Exception as e:
        print(f"❌ Error while testing connection: {e}")
        return 2

if __name__ == "__main__":
    code = asyncio.run(run_test())
    raise SystemExit(code)