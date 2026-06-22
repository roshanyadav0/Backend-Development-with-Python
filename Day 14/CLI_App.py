import sys
import json

class ConfigNotFoundError(Exception):
    """Raised when config file is missing."""
    pass

def load_config(filepath):
    """Load a JSON config file safely."""
    try:
        with open(filepath, "r") as f:
            config = json.load(f)

    except FileNotFoundError:
        raise ConfigNotFoundError(
            f"Config file '{filepath}' not found.\n"
            f"  Tip: Create it or use --config <path>"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in '{filepath}': {e}")
    
    else:
        print(f"Config loaded: {len(config)} settings found.")
        return config
    
    finally:
        print("[LOG] load_config() finished.")   # always logs


def run_cli():
    # Simulate CLI argument: python app.py --config settings.json
    args = sys.argv[1:]

    if "--config" in args:
        idx = args.index("--config")
        filepath = args[idx + 1]
    else:
        filepath = "config.json"   # default

    try:
        config = load_config(filepath)
        print(f"App Name: {config.get('app_name', 'Unknown')}")

    except ConfigNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)       # exit with error code

    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    except Exception as e:
        print(f"[CRITICAL] Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    run_cli()