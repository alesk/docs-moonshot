.. _{{qualified_name | slug}}:

{{title}}
=================

{% if doc is not none %}
{{doc}}
{% else %}
Documentation missing.
{% endif %}

Fields
------

{% macro type_link(field) %}
{% if field.is_linkable %}:ref:`{{field.type}} <{{field.type | slug}}>`{% else %}{{field.type}}{% endif %}
{% endmacro %}

{% macro required(field) %}
{% if not field.type.nullable %}*required*{% else %}*can contain NULL*{% endif %}
{% endmacro %}

{% macro type_signature(field) %}
{% if field.type.container == 'array' %}[{{ type_link(field) }}]{% else %}{{ type_link(field) }}{% endif %}
{% endmacro %}

{% for field in fields %}
.. _{{field.id | slug}}:

- **{{field.name}}**: {{ type_signature(field) }}, {{ required(field) }}

{% if field.doc is not none %}

  {{field.doc}}
{% endif %}

{% for link, origin_field in field.origin_fields.items() %}
{% if origin_field['doc'] is defined %}
  {{origin_field['doc']}} (:ref:`{{link}} <{{link | slug}}>`)
{% endif %}
{% endfor %}


{% endfor %}
