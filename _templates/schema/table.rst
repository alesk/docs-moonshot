.. _``{{bq_table | slug}}``::

{{table}}
=========

{{doc}}

Fields
======

{% for field in fields %}
.. _``{{field.id | slug}}``::

- **{{field.name}}**, {{field.type}}
  {% if field.doc is not none %}{{field.doc}}{% endif %}
  {% if field.origin is not none %}

  origin: :ref:``{{field.origin}} <{{field.origin | slug }}>``
  {% endif %}
  {% for usage in field.usages %}

   - :ref:``{{usage}} <{{usage | slug }}>``
  {% endfor %}
{% endfor %}
