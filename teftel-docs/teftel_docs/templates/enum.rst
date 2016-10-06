.. _{{qualified_name | slug}}:

{{qualified_name}}
=================

{% if doc is not none %}
{{doc}}
{% else %}
Documentation missing.
{% endif %}
{{name}}

Symbols
-------

{% for symbol in symbols -%}
- {{symbol}}
{% endfor -%}
