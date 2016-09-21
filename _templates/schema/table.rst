.. _{{bq_table | slug}}:

{{bq_table}}
=========

{{doc}}

Fields
------

{% for field in fields %}
.. _{{field.id | slug}}:

- **{{field.name}}**, {{field.type.type}}
{% if field.doc is not none %}{{field.doc}}{% endif %}
{% if field.type.origin is not none %}
origin: :ref:`{{field.type.origin}} <{{field.type.origin | slug }}>`
{% endif %}
  {% for usage in field.usages %}

   - :ref:`{{usage}} <{{usage | slug }}>`

  {% endfor %}

{% endfor %}
