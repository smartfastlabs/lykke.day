import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader, pass_context
from lykke.core.config import settings
from lykke.domain import value_objects

if TYPE_CHECKING:
    from lykke.application.repositories import TemplateRepositoryReadOnlyProtocol

USER_TEMPLATE_PATH: Path = (Path(settings.DATA_PATH) / "config" / "templates").resolve()
TEMPLATE_PATH: Path = Path(__file__).resolve().parents[3] / "templates"


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


env = Environment(
    loader=ChoiceLoader(
        [
            FileSystemLoader(USER_TEMPLATE_PATH),
            FileSystemLoader(TEMPLATE_PATH),
        ]
    )
)
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


def template_display_name(value: str) -> str:
    """Generate a display name from a template value."""
    cleaned = value.replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else value


async def create_template_environment(
    template_repo: "TemplateRepositoryReadOnlyProtocol",
    _user_id: UUID,
) -> Environment:
    """Create a Jinja2 environment with user overrides + system templates."""
    user_templates = await template_repo.search(value_objects.TemplateQuery())
    user_dict = {
        to_template_name(
            build_template_key(template.usecase, template.key)
        ): template.content
        for template in user_templates
    }

    environment = Environment(
        loader=ChoiceLoader(
            [
                DictLoader(user_dict),
                FileSystemLoader(TEMPLATE_PATH),
            ]
        )
    )
    _register_template_helpers(environment)
    return environment


async def render_for_user(
    usecase: str,
    part: str,
    template_repo: "TemplateRepositoryReadOnlyProtocol",
    user_id: UUID,
    **kwargs: Any,
) -> str:
    """Render a template for a user, applying DB overrides if present."""
    environment = await create_template_environment(template_repo, user_id)
    template_key = build_template_key(usecase, part)
    template = environment.get_template(to_template_name(template_key))
    return textwrap.dedent(template.render(**kwargs)).strip()
