.. _{{qualified_name}}:

Table {{file_name}}
=========================================================================================
`See in Big Query`_

{{doc}}

Fields
------

{% for field in fields %}
{% set field_link %}{{qualified_name}}#{{field.name}}{% endset %}
.. _`{{field_link | slug}}`::

- **{{field.name}}** {% if field.link %}:ref:`{{field.link|slug}}`{% else %} {{field.type_name}}{% endif %}
field link: {{field.link}}
{% if field.nullable == False%}, required{% endif %}

{% if field.doc %}  {{field.doc}}{% endif %}

{% endfor %}


.. _See in Big Query: https://bigquery.cloud.google.com/table/analytics-warehouse-staging:warehouse_prototype.{{bq_table}}

Discussion
----------

.. raw:: html

    <div id="disqus_thread"></div>
    <script>
         var disqus_config = function () {
         this.page.url = "https://shiny.toptal.net/docs/schema/{{file_name}}";  // Replace PAGE_URL with your page's canonical URL variable
         this.page.identifier = "/docs/schema/{{file_name}}"; // Replace PAGE_IDENTIFIER with your page's unique identifier variable
         };

        (function() { // DON'T EDIT BELOW THIS LINE
            var d = document, s = d.createElement('script');
            s.src = '//shiny-toptal-com-docs.disqus.com/embed.js';
            s.setAttribute('data-timestamp', +new Date());
            (d.head || d.body).appendChild(s);
        })();
    </script>
    <noscript>Please enable JavaScript to view the <a href="https://disqus.com/?ref_noscript">comments powered by Disqus.</a></noscript>
