from django.contrib import admin
from .models import ResumeUploadSession


@admin.register(ResumeUploadSession)
class ResumeUploadSessionAdmin(admin.ModelAdmin):
    """Admin configuration for ResumeUploadSession"""

    list_display = ['id', 'created_at', 'processed', 'get_results_count', 'has_error']
    list_filter = ['processed', 'created_at']
    search_fields = ['job_description', 'error_message']
    readonly_fields = ['created_at', 'results', 'criteria', 'error_message']
    ordering = ['-created_at']

    fieldsets = (
        ('Upload Information', {
            'fields': ('job_description', 'zip_file', 'created_at')
        }),
        ('Processing Status', {
            'fields': ('processed', 'error_message')
        }),
        ('Results', {
            'fields': ('results', 'criteria'),
            'classes': ('collapse',)
        }),
    )

    def has_error(self, obj):
        """Display if session has error"""
        return bool(obj.error_message)
    has_error.boolean = True
    has_error.short_description = 'Has Error'
