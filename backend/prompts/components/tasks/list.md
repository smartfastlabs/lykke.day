{% for task in tasks %}

- **{{ task.task_definition.name }}** ({{ task.status.value }})
  {% if task.task_definition.description %}
  - {{ task.task_definition.description }}
    {% endif %}
    {% if task.schedule %}
    {% if task.schedule.start_time and task.schedule.end_time %}
  - {{ task.schedule.start_time.strftime('%I:%M %p') }} - {{ task.schedule.end_time.strftime('%I:%M %p') }}
    {% elif task.schedule.start_time %}
  - Starts: {{ task.schedule.start_time.strftime('%I:%M %p') }}
    {% elif task.schedule.end_time %}
  - Due by: {{ task.schedule.end_time.strftime('%I:%M %p') }}
    {% endif %}
    {% endif %}
    {% if task.completed_at %}
  - Completed: {{ task.completed_at.strftime('%I:%M %p') }}
    {% endif %}

{% endfor %}
