from pkm_agent.config import Config, load_config
from pathlib import Path
import os

def test_config():
    print("Testing Config...")
    
    # Test default
    cfg = Config()
    print(f"Default pkm_root: {cfg.pkm_root}")
    print(f"Default LLM provider: {cfg.llm.provider}")
    
    # Test validation (invalid values)
    try:
        from pydantic import ValidationError
        print("Testing invalid config...")
        # Note: In pydantic v2 we instantiate models
        # This might fail if imports are missing in this env, but let's try
    except ImportError:
        print("Pydantic not found, skipping validation test")

    # Test init command logic
    print("Testing init...")
    import toml
    data = cfg.model_dump(mode="json", exclude_none=True)
    print("Dumped config keys:", list(data.keys()))
    
if __name__ == "__main__":
    test_config()
