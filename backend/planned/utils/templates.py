import textwrap
from pathlib import Path

from jinja2 import ChoiceLoader, Environment, FileSystemLoader

from planned import settings

USER_TEMPLATE_PATH: Path = (Path(settings.DATA_PATH) / "config" / "prompts").resolve()
TEMPLATE_PATH: Path = Path(__file__).parent.parent.parent / "prompts"
print(TEMPLATE_PATH)

env = Environment(
    loader=ChoiceLoader(
        [
            FileSystemLoader(USER_TEMPLATE_PATH),
            FileSystemLoader(TEMPLATE_PATH),
        ]
    )
)


def render(template_name: str, **kwargs) -> str:
    template = env.get_template(template_name)
    return textwrap.dedent(template.render(**kwargs)).strip()
