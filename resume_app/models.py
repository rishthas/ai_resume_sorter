from django.db import models
import json


class ResumeUploadSession(models.Model):
    """Model to store resume upload sessions"""

    job_description = models.TextField()
    zip_file = models.FileField(upload_to='uploads/')
    created_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    results = models.JSONField(null=True, blank=True)
    criteria = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.id} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def get_results_count(self):
        """Return the number of processed resumes"""
        if self.results:
            return len(self.results)
        return 0
