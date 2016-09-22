.. _{{namespace | slug}}:

{{name}}
=========================================================================================

{{doc}}

.. toctree::
  :maxdepth: 1
  :titlesonly:

{% for table, link in tables.items() %}
  {{table}} <tables/{{link}}>
{% endfor %}
