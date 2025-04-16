{% set page_content = get_page(path=path) %}
{% if page_content %}
## {{ page_content.title }}

{{ page_content.content | safe }}

[続きを読む →]({{ page_content.permalink }})
{% else %}
指定されたページが見つかりませんでした。
{% endif %}
