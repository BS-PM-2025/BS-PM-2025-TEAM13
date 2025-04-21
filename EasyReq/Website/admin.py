from django.contrib import admin
from .models import User, Department, Course, Request

# Register your models here.

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dept')
    search_fields = ('name', 'dept__name')

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'email', 'role', 'department')
    list_filter = ('role', 'department')
    search_fields = ('username', 'name', 'email', 'department__name')
    ordering = ('username',)

class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'dept', 'status', 'created')
    list_filter = ('status', 'student')
    search_fields = ('title', 'student__username')

admin.site.register(User, UserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Request, RequestAdmin)

