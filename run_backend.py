"""
Script to run the PKM Agent Backend Server persistently.
This starts the WebSocket Sync Server and the File Watcher.
"""
import asyncio
import logging
import signal
import sys
from pkm_agent.app import PKMAgentApp
from pkm_agent.config import Config
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("pkm_agent_server.log")
    ]
)
logger = logging.getLogger("server")

async def main():
    print("🚀 Starting PKM Agent Backend Server...")
    
    # Configure path to the demo vault
    vault_path = Path("C:/Users/Admin/Documents/B0LK13v2/B0LK13v2/demo_vault")
    if not vault_path.exists():
        print(f"⚠️  Warning: Vault path not found: {vault_path}")
        print("   Creating it now...")
        vault_path.mkdir(parents=True, exist_ok=True)

    config = Config()
    config.pkm_root = vault_path
    
    app = PKMAgentApp(config)
    
    # Handle shutdown signals
    stop_event = asyncio.Event()
    
    def handle_signal():
        print("\n🛑 Shutdown signal received...")
        stop_event.set()

    # Register signal handlers (works on Windows for CTRL+C)
    try:
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGINT, handle_signal)
        loop.add_signal_handler(signal.SIGTERM, handle_signal)
    except NotImplementedError:
        # Windows specific signal handling if needed
        pass

    try:
        await app.initialize()
        print(f"✅ Server running at ws://127.0.0.1:27125")
        print(f"✅ Watching vault: {vault_path}")
        print("Press CTRL+C to stop.")
        
        # Keep running until signal
        while not stop_event.is_set():
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt received...")
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
    finally:
        print("Shutting down...")
        await app.close()
        print("Goodbye! 👋")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
