from django import forms
from .models import ResumeUploadSession


class ResumeUploadForm(forms.ModelForm):
    """Form for uploading resumes and job description"""

    class Meta:
        model = ResumeUploadSession
        fields = ['job_description', 'zip_file']
        widgets = {
            'job_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter the job description here...\n\nInclude:\n- Job title\n- Required skills\n- Preferred skills\n- Experience requirements\n- Responsibilities'
            }),
            'zip_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.zip'
            })
        }
        labels = {
            'job_description': 'Job Description',
            'zip_file': 'Upload Resumes (ZIP file)'
        }
        help_texts = {
            'job_description': 'Provide a detailed job description including required and preferred skills.',
            'zip_file': 'Upload a ZIP file containing resumes in PDF, DOCX, or TXT format.'
        }

    def clean_zip_file(self):
        """Validate the uploaded file"""
        zip_file = self.cleaned_data.get('zip_file')

        if zip_file:
            # Check file extension
            if not zip_file.name.endswith('.zip'):
                raise forms.ValidationError('Please upload a ZIP file.')

            # Check file size (limit to 50MB)
            if zip_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must be less than 50MB.')

        return zip_file

    def clean_job_description(self):
        """Validate job description"""
        job_description = self.cleaned_data.get('job_description')

        if job_description:
            # Check minimum length
            if len(job_description.strip()) < 50:
                raise forms.ValidationError('Job description must be at least 50 characters long.')

        return job_description
