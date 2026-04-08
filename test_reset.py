#!/usr/bin/env python3
"""Test the reset endpoint"""

import asyncio
from main import reset_environment

async def test():
    result = await reset_environment()
    print('Reset endpoint response:')
    print(f'  Success: {result.get("success")}')
    print(f'  Message: {result.get("message")}')
    print(f'  Session ID: {result.get("session_id")}')
    return result.get('success')

if __name__ == "__main__":
    success = asyncio.run(test())
    if success:
        print('\n✅ Reset endpoint works!')
    else:
        print('\n❌ Reset endpoint failed')
