from django import template

register = template.Library()


@register.simple_tag
def url_replace(request, field, value):
    """
    Template tag to replace or add a GET parameter in the current URL

    Usage example:
    <a href="?{% url_replace request 'page' 3 %}">Page 3</a>
    """
    query_dict = request.GET.copy()
    query_dict[field] = value
    return query_dict.urlencode()