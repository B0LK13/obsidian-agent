import os
import asyncio
from pkm_agent.llm import OpenAIProvider
from pkm_agent.llm.base import Message
async def verify_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set.")
        print("Please export it: $env:OPENAI_API_KEY='sk-...'")
        return
    print(f"🔑 Found API Key: {api_key[:8]}...{api_key[-4:]}")
    print("⏳ Testing connection to OpenAI (gpt-4o-mini)...")
    try:
        provider = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
        
        messages = [Message(role="user", content="Hello, reply with 'OK' if you can hear me.")]
        
        response = await provider.generate(messages)
        
        print("\n✅ SUCCESS! API Connection Verified.")
        print(f"🤖 Model Response: {response}")
        print("\nYour API key is valid and has sufficient quota.")
        
    except Exception as e:
        print(f"\n❌ FAILURE: Could not connect to OpenAI.")
        print(f"Error details: {e}")
        
        if "429" in str(e):
            print("\n⚠️  Diagnosis: Quota Exceeded (429)")
            print("Even if you topped up, it might take a few minutes to reflect.")
            print("Or you might be hitting a rate limit.")
        elif "401" in str(e):
            print("\n⚠️  Diagnosis: Invalid API Key (401)")
if __name__ == "__main__":
    try:
        asyncio.run(verify_openai())
    except KeyboardInterrupt:
        pass