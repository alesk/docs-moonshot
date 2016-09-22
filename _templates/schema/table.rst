.. _{{bq_table | slug}}:

{{bq_table}}
=================

{% if doc is not none %}
{{doc}}
{% else %}
Documentation missing.
{% endif %}

Fields
------

{% macro type_link(field) %}
{% if field.is_linkable %}:ref:`{{field.qualified_type_name}} <{{field.qualified_type_name | slug}}>`{% else %}{{field.type.type}}{% endif %}
{% endmacro %}

{% macro required(field) %}
{% if not field.type.nullable %}*required*{% else %}*can contain NULL*{% endif %}
{% endmacro %}

{% for field in fields %}
.. _{{field.id | slug}}:

- **{{field.name}}**: {{ type_link(field) }}, {{ required(field) }}

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
