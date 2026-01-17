#!/usr/bin/env python3
"""
Check for missing mappers between entities, schemas, tables, and repositories.

This script helps identify when you've added/modified an entity but forgot to:
- Add a schema for it
- Add a mapper function
- Add repository mapping methods
- Add a database table
"""

import ast
import os
import sys
from pathlib import Path
from typing import Any


def get_classes_from_file(file_path: Path, base_class_suffix: str) -> list[str]:
    """Extract class names ending with base_class_suffix from a Python file."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
        
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name.endswith(base_class_suffix):
                    # Remove the suffix to get the base name
                    base_name = node.name[: -len(base_class_suffix)]
                    classes.append(base_name)
        return classes
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []


def get_functions_from_file(file_path: Path, prefix: str) -> list[str]:
    """Extract function names starting with prefix from a Python file."""
    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith(prefix) and "_to_schema" in node.name:
                    # Extract the entity name from map_<entity>_to_schema
                    entity_name = node.name[len(prefix):-len("_to_schema")]
                    # Convert snake_case to PascalCase
                    pascal_name = "".join(word.capitalize() for word in entity_name.split("_"))
                    functions.append(pascal_name)
        return functions
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []


def check_repository_methods(file_path: Path) -> tuple[bool, bool]:
    """Check if repository has entity_to_row and row_to_entity methods."""
    try:
        with open(file_path) as f:
            content = f.read()
        
        has_entity_to_row = "def entity_to_row" in content
        has_row_to_entity = "def row_to_entity" in content
        
        return has_entity_to_row, has_row_to_entity
    except Exception:
        return False, False


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    result = [name[0].lower()]
    for char in name[1:]:
        if char.isupper():
            result.append("_")
            result.append(char.lower())
        else:
            result.append(char)
    return "".join(result)


def main() -> int:
    """Main function to check for missing mappers."""
    # Get script directory and project root
    script_dir = Path(__file__).parent.parent
    backend_dir = script_dir
    lykke_dir = backend_dir / "lykke"
    
    # Paths
    entities_dir = lykke_dir / "domain" / "entities"
    schemas_dir = lykke_dir / "presentation" / "api" / "schemas"
    mappers_file = schemas_dir / "mappers.py"
    tables_dir = lykke_dir / "infrastructure" / "database" / "tables"
    repos_dir = lykke_dir / "infrastructure" / "repositories"
    
    if not entities_dir.exists():
        print(f"Error: {entities_dir} not found", file=sys.stderr)
        return 1
    
    # Collect all entities
    entities = set()
    for file_path in entities_dir.glob("*.py"):
        if file_path.name == "__init__.py" or file_path.name == "base.py":
            continue
        entities.update(get_classes_from_file(file_path, "Entity"))
    
    # Collect all schemas
    schemas = set()
    for file_path in schemas_dir.glob("*.py"):
        if file_path.name in ["__init__.py", "base.py", "mappers.py"]:
            continue
        schemas.update(get_classes_from_file(file_path, "Schema"))
    
    # Collect all mapper functions
    mappers = set()
    if mappers_file.exists():
        mappers = set(get_functions_from_file(mappers_file, "map_"))
    
    # Collect all tables by reading the actual class names from table files
    tables = set()
    for file_path in tables_dir.glob("*.py"):
        if file_path.name in ["__init__.py", "base.py"]:
            continue
        try:
            with open(file_path) as f:
                content = f.read()
            # Look for class definitions that inherit from Base
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from Base (indicating it's a table)
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "Base":
                            tables.add(node.name)
                            break
        except Exception:
            pass
    
    # Check for issues
    critical_issues_found = False
    
    print("=" * 80)
    print("MAPPER COMPLETENESS CHECK")
    print("=" * 80)
    print()
    
    # Check for entities without schemas
    entities_without_schemas = entities - schemas
    if entities_without_schemas:
        critical_issues_found = True
        print("❌ ENTITIES WITHOUT SCHEMAS:")
        for entity in sorted(entities_without_schemas):
            schema_file = schemas_dir / f"{to_snake_case(entity)}.py"
            print(f"   - {entity}Entity")
            print(f"     → Create: {schema_file}")
            print(f"     → Add class: {entity}Schema")
        print()
    
    # Check for entities without mappers
    entities_without_mappers = entities - mappers
    if entities_without_mappers:
        critical_issues_found = True
        print("❌ ENTITIES WITHOUT MAPPER FUNCTIONS:")
        for entity in sorted(entities_without_mappers):
            print(f"   - {entity}Entity")
            print(f"     → Add to: {mappers_file}")
            print(f"     → Function: map_{to_snake_case(entity)}_to_schema()")
        print()
    
    # Check for entities without tables
    entities_without_tables = entities - tables
    # Data objects have been moved to entities, so no filtering needed
    
    if entities_without_tables:
        # This is a warning, not a critical issue (some entities may not need persistence)
        pass
        print("⚠️  ENTITIES WITHOUT DATABASE TABLES:")
        print("    (Verify these are intentional - some entities may not need persistence)")
        for entity in sorted(entities_without_tables):
            table_file = tables_dir / f"{to_snake_case(entity)}.py"
            print(f"   - {entity}Entity")
            print(f"     → Create: {table_file} (if needed)")
        print()
    
    # Check repositories for missing methods
    print("REPOSITORY MAPPING METHODS CHECK:")
    repos_with_issues = []
    for file_path in repos_dir.glob("*.py"):
        if file_path.name in ["__init__.py"]:
            continue
        if file_path.is_dir():
            continue
            
        has_entity_to_row, has_row_to_entity = check_repository_methods(file_path)
        
        if not has_entity_to_row or not has_row_to_entity:
            repos_with_issues.append((file_path.name, has_entity_to_row, has_row_to_entity))
    
    if repos_with_issues:
        print("⚠️  REPOSITORIES WITHOUT CUSTOM MAPPING METHODS:")
        print("    (These use base class defaults - verify if custom logic is needed)")
        for repo_name, has_e2r, has_r2e in repos_with_issues:
            print(f"   - {repo_name}")
            if not has_e2r:
                print(f"     → Missing: entity_to_row() method")
            if not has_r2e:
                print(f"     → Using default: row_to_entity() (check if custom logic needed)")
        print()
    else:
        print("✅ All repositories have custom mapping methods")
        print()
    
    # Summary
    print("=" * 80)
    if not critical_issues_found:
        print("✅ ALL CRITICAL CHECKS PASSED - All entities have schemas and mappers!")
        if repos_with_issues or entities_without_tables:
            print()
            print("Note: Some warnings above may need attention.")
    else:
        print("❌ CRITICAL ISSUES FOUND - Please add missing mappers/schemas")
        print()
        print("For guidance, see: .cursor/commands/object-schema-mapper-guide.md")
    print("=" * 80)
    
    return 1 if critical_issues_found else 0


if __name__ == "__main__":
    sys.exit(main())
