import textwrap
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, pass_context

TEMPLATE_PATH: Path = Path(__file__).resolve().parents[3] / "templates"
BASE_PERSONALITY_DIR = "base_personalities"
DEFAULT_BASE_PERSONALITY_SLUG = "default"


@pass_context
def fmt_time(_context: dict[str, Any], value: Any) -> str:
    return str(value.strftime("%I:%M%p")).lower()


@pass_context
def fmt_datetime(context: dict[str, Any], value: Any) -> str:
    current_time = context.get("current_time")
    if current_time is not None and value.tzinfo and current_time.tzinfo:
        value = value.astimezone(current_time.tzinfo)
    return f"{value.date().isoformat()} {value.strftime('%I:%M%p').lower()}"


def kv_line(indent: str, key: str, value: Any) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return ""
    return f"\n{indent}{key}: {value}"


def _register_template_helpers(environment: Environment) -> None:
    environment.globals["fmt_time"] = fmt_time
    environment.globals["fmt_datetime"] = fmt_datetime
    environment.globals["kv_line"] = kv_line


env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
_register_template_helpers(env)


def render(template_name: str, /, **kwargs: Any) -> str:
    template = env.get_template(template_name)
    rendered = template.render(**kwargs)
    return textwrap.dedent(str(rendered)).strip()


def normalize_template_key(key: str) -> str:
    """Normalize a template key by stripping a .j2 suffix if present."""
    return key[:-3] if key.endswith(".j2") else key


def build_template_key(usecase: str, part: str) -> str:
    """Build a template key from use case and part."""
    cleaned_usecase = usecase.strip().strip("/")
    cleaned_part = part.strip().strip("/")
    if cleaned_usecase.startswith("usecases/"):
        usecase_path = cleaned_usecase
    else:
        usecase_path = f"usecases/{cleaned_usecase}"
    return f"{usecase_path}/{cleaned_part}"


def to_template_name(key: str) -> str:
    """Convert a template key to a Jinja2 template filename."""
    normalized = normalize_template_key(key)
    return f"{normalized}.j2"


def list_system_templates() -> list[dict[str, str]]:
    """List system templates from the file system with usecase + part."""
    templates: list[dict[str, str]] = []
    usecases_root = TEMPLATE_PATH / "usecases"
    if not usecases_root.exists():
        return templates
    for path in sorted(usecases_root.rglob("*.j2")):
        relative = path.relative_to(usecases_root)
        if len(relative.parts) != 2:
            continue
        usecase, filename = relative.parts
        part = normalize_template_key(filename)
        content = path.read_text(encoding="utf-8")
        templates.append({"usecase": usecase, "part": part, "content": content})
    return templates


def list_base_personalities() -> list[dict[str, str]]:
    """List available base personality templates."""
    base_root = TEMPLATE_PATH / BASE_PERSONALITY_DIR
    if not base_root.exists():
        return [{"slug": DEFAULT_BASE_PERSONALITY_SLUG, "label": "Default"}]

    personalities = []
    for path in sorted(base_root.glob("*.j2")):
        slug = path.stem
        personalities.append(
            {"slug": slug, "label": template_display_name(slug)}
        )

    if not any(item["slug"] == DEFAULT_BASE_PERSONALITY_SLUG for item in personalities):
        personalities.insert(0, {"slug": DEFAULT_BASE_PERSONALITY_SLUG, "label": "Default"})

    return personalities


def resolve_base_personality_slug(slug: str | None) -> str:
    """Validate base personality slug with fallback to default."""
    if not slug:
        return DEFAULT_BASE_PERSONALITY_SLUG

    base_root = TEMPLATE_PATH / BASE_PERSONALITY_DIR
    candidate = base_root / f"{slug}.j2"
    if candidate.exists():
        return slug
    return DEFAULT_BASE_PERSONALITY_SLUG


def template_display_name(value: str) -> str:
    """Generate a display name from a template value."""
    cleaned = value.replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else value


def create_template_environment() -> Environment:
    """Create a Jinja2 environment for system templates."""
    environment = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
    _register_template_helpers(environment)
    return environment


def render_for_user(
    usecase: str,
    part: str,
    base_personality_slug: str | None = None,
    **kwargs: Any,
) -> str:
    """Render a system template."""
    environment = create_template_environment()
    template_key = build_template_key(usecase, part)
    template = environment.get_template(to_template_name(template_key))
    resolved_slug = resolve_base_personality_slug(base_personality_slug)
    kwargs.setdefault("base_personality_slug", resolved_slug)
    return textwrap.dedent(template.render(**kwargs)).strip()
