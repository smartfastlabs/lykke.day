"""Export OpenAPI schema from FastAPI app to JSON file."""
import json
from pathlib import Path

# Import FastAPI app
from planned.app import app


def main():
    """Export OpenAPI schema to openapi.json file."""
    schema = app.openapi()
    output_path = Path(__file__).parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2))
    print(f"OpenAPI schema exported to {output_path}")


if __name__ == "__main__":
    main()

