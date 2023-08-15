from pathlib import Path


def read_secret(secret_name, default=''):
    file = Path('/run/secrets') / secret_name
    if not file.is_file():
        log.error(f"Can't read secret {secret_name}. Path {file} doesn't exist")
        return default
    with file.open() as f:
        return f.read().strip()

DB_PASSWORD = read_secret('db_password')
