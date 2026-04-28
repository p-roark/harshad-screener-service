"""In-memory strategy config cache."""
_configs: dict = {}

def get_configs() -> dict:
    return _configs

def load_configs():
    pass

def start_monthly_refresh():
    pass

def stop_refresh():
    pass
