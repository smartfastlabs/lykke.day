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
    # Note: openapi-typescript generates a single file, we'll split it manually
    temp_output = output_dir / "api.generated.ts"

    try:
        subprocess.run(
            [
                "npx",
                "openapi-typescript",
                str(schema_file),
                "-o",
                str(temp_output),
            ],
            cwd=str(frontend_dir),
            check=True,
        )

        # Split the generated file into multiple files
        try:
            from split_types import split_types_file
            split_types_file(temp_output, output_dir)
        except ImportError:
            # If split_types can't be imported, try running it as a script
            split_script = Path(__file__).parent / "split_types.py"
            subprocess.run(
                [
                    sys.executable,
                    str(split_script),
                    str(temp_output),
                    str(output_dir),
                ],
                check=True,
            )
        finally:
            temp_output.unlink()  # Remove temp file

        print(f"Types generated in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating types: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
