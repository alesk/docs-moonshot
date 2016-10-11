.. _{{qualified_name | slug}}:

{{qualified_name}}
=================

{% if doc is not none %}
{{doc | indent_avro_doc(0)}}
{% else %}
Documentation missing.
{% endif %}

Symbols
-------

{% for symbol in symbols -%}
- {{symbol}}
{% endfor -%}
