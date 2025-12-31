"""Generate TypeScript types from OpenAPI schema file."""

import subprocess
import sys
from pathlib import Path


def main():
    """Generate TypeScript types from openapi.json schema file."""
    backend_dir = Path(__file__).parent.parent
    frontend_dir = backend_dir.parent / "frontend"
    schema_file = backend_dir / "openapi.json"

    if not schema_file.exists():
        print(f"Error: {schema_file} not found. Run export_openapi_schema.py first.")
        sys.exit(1)

    output_dir = frontend_dir / "src" / "types" / "api"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate types using openapi-typescript
    # Output directly to the final location as a single file
    output_file = output_dir / "api.generated.ts"

    try:
        subprocess.run(
            [
                "npx",
                "openapi-typescript",
                str(schema_file),
                "-o",
                str(output_file),
            ],
            cwd=str(frontend_dir),
            check=True,
        )

        print(f"Types generated in {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating types: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
