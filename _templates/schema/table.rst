.. _{{bq_table | slug}}:

{{bq_table}}
=========

{% if doc is not none %}
{{doc}}
{% else %}
Documentation missing.
{% endif %}

Fields
------

{% for field in fields %}
.. _{{field.id | slug}}:

- **{{field.name}}**, {{field.type.type}}{% if not field.type.nullable %}, *required*{% endif %}

{% if field.origin_doc is not none %}

  {{field.origin_doc}}
{% endif %}
{% if field.doc is not none %}

  {{field.doc}}
{% endif %}
{% if field.type.origin is not none %}

  origin: :ref:`{{field.type.origin}} <{{field.type.origin | slug }}>`
{% endif %}
{% if field.usages|length > 0 %}

  usages:
  {% for usage in field.usages %}
   - :ref:`{{usage}} <{{usage | slug }}>`
  {% endfor %}

{% endif %}

{% endfor %}
