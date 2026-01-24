"""DayTemplate command handlers."""

from .add_day_template_routine import (
    AddDayTemplateRoutineDefinitionCommand,
    AddDayTemplateRoutineDefinitionHandler,
)
from .add_day_template_time_block import (
    AddDayTemplateTimeBlockCommand,
    AddDayTemplateTimeBlockHandler,
)
from .create_day_template import CreateDayTemplateCommand, CreateDayTemplateHandler
from .delete_day_template import DeleteDayTemplateCommand, DeleteDayTemplateHandler
from .remove_day_template_routine import (
    RemoveDayTemplateRoutineDefinitionCommand,
    RemoveDayTemplateRoutineDefinitionHandler,
)
from .remove_day_template_time_block import (
    RemoveDayTemplateTimeBlockCommand,
    RemoveDayTemplateTimeBlockHandler,
)
from .update_day_template import UpdateDayTemplateCommand, UpdateDayTemplateHandler

__all__ = [
    "AddDayTemplateRoutineDefinitionCommand",
    "AddDayTemplateRoutineDefinitionHandler",
    "AddDayTemplateTimeBlockCommand",
    "AddDayTemplateTimeBlockHandler",
    "CreateDayTemplateCommand",
    "CreateDayTemplateHandler",
    "DeleteDayTemplateCommand",
    "DeleteDayTemplateHandler",
    "RemoveDayTemplateRoutineDefinitionCommand",
    "RemoveDayTemplateRoutineDefinitionHandler",
    "RemoveDayTemplateTimeBlockCommand",
    "RemoveDayTemplateTimeBlockHandler",
    "UpdateDayTemplateCommand",
    "UpdateDayTemplateHandler",
]
