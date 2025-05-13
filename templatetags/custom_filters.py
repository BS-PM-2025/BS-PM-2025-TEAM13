from django import template

register = template.Library()

@register.filter
def filter_by_role(users, role):
    """Filter users by role"""
    return [user for user in users if user.role == role]

@register.filter
def filter_by_status(requests, status):
    """Filter requests by status"""
    return [req for req in requests if req.status == status]