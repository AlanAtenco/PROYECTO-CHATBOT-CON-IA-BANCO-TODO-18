from pathlib import Path
import py_compile
import sys

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent
errors = []

python_files = [
    ROOT / "rasa" / "actions" / "actions.py",
    ROOT / "backend" / "main.py",
]

for file_path in python_files:
    try:
        py_compile.compile(str(file_path), doraise=True)
        print(f"OK Python: {file_path.relative_to(ROOT)}")
    except Exception as exc:
        errors.append(f"ERROR Python {file_path}: {exc}")

if yaml is not None:
    yaml_files = [
        ROOT / "docker-compose.yml",
        ROOT / "rasa" / "domain.yml",
        ROOT / "rasa" / "data" / "rules.yml",
        ROOT / "rasa" / "data" / "stories.yml",
        ROOT / "rasa" / "endpoints.yml",
    ]
    for file_path in yaml_files:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                yaml.safe_load(handle)
            print(f"OK YAML: {file_path.relative_to(ROOT)}")
        except Exception as exc:
            errors.append(f"ERROR YAML {file_path}: {exc}")
else:
    print("PyYAML no está instalado; se omite validación YAML.")

required_files = [
    ROOT / "database" / "init" / "01_banking_schema.sql",
    ROOT / "rasa" / "actions" / "Dockerfile",
]
for file_path in required_files:
    if file_path.exists():
        print(f"OK archivo: {file_path.relative_to(ROOT)}")
    else:
        errors.append(f"FALTA archivo requerido: {file_path}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("Validación básica completada correctamente.")
