--------------------

Name: {{ name }}

Description: {{ description }}

Owner: [{{ owner }}]({{ url_for('main.user_view', username=owner, _external=True) }})

Create Time: {{ create_date }}

Update Time: {{ last_update }}

Export from: [GitMark]({{ url_for('main.index', _external=True) }})

Original Collection: [{{ name }}]({{ url_for('main.collection_detail', collection_id=id, _external=True) }})

--------------------

{% for repo in repos %}

### [{{ repo.get('full_name') }}]({{ repo.get('link') }})

{{ repo.get('desc') }}

<small>Language: {{ repo.get('language') }}</small>

{% if not loop.last %}
        
---------------------

{% endif %}


{% endfor %}