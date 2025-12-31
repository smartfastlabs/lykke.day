"""Split generated TypeScript types into multiple organized files."""
import re
from pathlib import Path
from typing import Dict, List, Tuple


def parse_generated_file(content: str) -> Dict[str, List[str]]:
    """Parse the generated TypeScript file and extract different sections.
    
    openapi-typescript generates a file with this structure:
    - export interface paths { ... }
    - export type components = { schemas: { ... }, parameters: { ... } }
    """
    sections = {
        "schemas": [],
        "paths": [],
        "parameters": [],
        "enums": [],
        "other": [],
    }

    lines = content.split("\n")
    i = 0
    
    # Extract header comments
    header_end = 0
    for j, line in enumerate(lines):
        if line.strip().startswith("export "):
            header_end = j
            break
    
    # Find paths interface
    paths_start = None
    paths_end = None
    for i, line in enumerate(lines):
        if "export interface paths" in line or "export type paths" in line:
            paths_start = i
            # Find matching closing brace
            brace_count = 0
            for j in range(i, len(lines)):
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count == 0 and j > i:
                    paths_end = j + 1
                    break
            if paths_start and paths_end:
                sections["paths"] = lines[paths_start:paths_end]
            break
    
    # Find components type/interface
    components_start = None
    components_end = None
    for i, line in enumerate(lines):
        if "export type components" in line or "export interface components" in line:
            components_start = i
            # Find matching closing brace
            brace_count = 0
            for j in range(i, len(lines)):
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count == 0 and j > i:
                    components_end = j + 1
                    break
            if components_start and components_end:
                # Extract schemas and parameters from components
                components_section = lines[components_start:components_end]
                extract_components(components_section, sections)
            break
    
    # Extract enum types (union types with string literals)
    for i, line in enumerate(lines):
        if re.match(r'^\s*export type \w+\s*=\s*"[^"]+"', line) or \
           re.match(r"^\s*export type \w+\s*=\s*'[^']+'", line):
            # Single line enum
            sections["enums"].append(line)
        elif "export type" in line and "|" in line and ("'" in line or '"' in line):
            # Multi-line enum - collect until semicolon
            enum_lines = [line]
            j = i + 1
            while j < len(lines) and ";" not in lines[j]:
                enum_lines.append(lines[j])
                j += 1
            if j < len(lines):
                enum_lines.append(lines[j])
            sections["enums"].extend(enum_lines)
            sections["enums"].append("")
    
    return sections


def extract_components(components_lines: List[str], sections: Dict[str, List[str]]):
    """Extract schemas and parameters from components section."""
    current_section = None
    brace_count = 0
    section_start = 0
    
    for i, line in enumerate(components_lines):
        # Detect schemas section
        if "schemas:" in line or '"schemas"' in line or "'schemas'" in line:
            current_section = "schemas"
            section_start = i
            brace_count = line.count("{") - line.count("}")
        # Detect parameters section
        elif "parameters:" in line or '"parameters"' in line or "'parameters'" in line:
            # Save previous section
            if current_section and section_start < i:
                sections[current_section].extend(components_lines[section_start:i])
                sections[current_section].append("")
            current_section = "parameters"
            section_start = i
            brace_count = line.count("{") - line.count("}")
        elif current_section:
            brace_count += line.count("{") - line.count("}")
            # If we've closed the current section
            if brace_count <= 0 and ("}" in line or "}" in components_lines[min(i+1, len(components_lines)-1)]):
                sections[current_section].extend(components_lines[section_start:i+1])
                sections[current_section].append("")
                current_section = None
                brace_count = 0


def write_section_file(output_dir: Path, filename: str, content: List[str], header: str):
    """Write a section to a file."""
    file_path = output_dir / filename
    with open(file_path, "w") as f:
        f.write(header)
        f.write("\n")
        # Remove trailing blank lines
        while content and not content[-1].strip():
            content.pop()
        f.write("\n".join(content))
        if content:
            f.write("\n")


def split_types_file(generated_file: Path, output_dir: Path):
    """Split a generated TypeScript file into multiple organized files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read generated file
    content = generated_file.read_text()

    # Extract header comments
    header_match = re.search(r"/\*.*?\*/", content, re.DOTALL)
    header = header_match.group(0) if header_match else "/* Generated from OpenAPI schema */"

    # Parse into sections
    sections = parse_generated_file(content)

    # Write each section to its file
    section_files = {
        "schemas": "schemas.ts",
        "paths": "paths.ts",
        "parameters": "parameters.ts",
        "enums": "enums.ts",
    }

    for section_name, filename in section_files.items():
        if sections[section_name]:
            write_section_file(
                output_dir,
                filename,
                sections[section_name],
                header,
            )

    # Handle "other" section - append to schemas if it exists
    if sections["other"]:
        schemas_file = output_dir / "schemas.ts"
        if schemas_file.exists():
            with open(schemas_file, "a") as f:
                f.write("\n")
                f.write("\n".join(sections["other"]))
                f.write("\n")
        else:
            write_section_file(
                output_dir,
                "schemas.ts",
                sections["other"],
                header,
            )

    # Create index.ts with re-exports
    index_content = [
        "// Re-export all types for convenience",
        "// Generated types from OpenAPI schema",
        "export * from './schemas';",
        "export * from './paths';",
        "export * from './parameters';",
        "export * from './enums';",
        "",
        "// Utility types",
        "export * from './utils';",
    ]
    index_file = output_dir / "index.ts"
    index_file.write_text("\n".join(index_content) + "\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: split_types.py <generated_file> <output_dir>")
        sys.exit(1)

    generated_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])

    split_types_file(generated_file, output_dir)
    print(f"Types split into {output_dir}")

