from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from .models import ResumeUploadSession
from .forms import ResumeUploadForm
from .services import ResumeProcessingService
import os


def home(request):
    """Home page with upload form"""
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the upload session
            session = form.save(commit=False)
            session.save()

            # Process the resumes
            try:
                # Get OpenAI API key from environment
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    messages.error(request, 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.')
                    return redirect('home')

                # Get model from environment or use default
                model = os.getenv('MODEL', 'gpt-3.5-turbo')

                # Initialize the service
                service = ResumeProcessingService(api_key, model)

                # Process the zip file
                result = service.process_zip_file(
                    session.zip_file.path,
                    session.job_description
                )

                if result['success']:
                    # Update session with results
                    session.processed = True
                    session.results = result['results']
                    session.criteria = result.get('criteria', {})
                    session.save()

                    messages.success(
                        request,
                        f'Successfully processed {result["total_processed"]} out of {result["total_files"]} resumes!'
                    )
                    return redirect('results', session_id=session.id)
                else:
                    # Update session with error
                    session.error_message = result['error']
                    session.save()
                    messages.error(request, result['error'])
                    return redirect('home')

            except Exception as e:
                session.error_message = str(e)
                session.save()
                messages.error(request, f'Error processing resumes: {str(e)}')
                return redirect('home')
    else:
        form = ResumeUploadForm()

    # Get recent sessions
    recent_sessions = ResumeUploadSession.objects.filter(processed=True)[:5]

    return render(request, 'resume_app/home.html', {
        'form': form,
        'recent_sessions': recent_sessions
    })


def results(request, session_id):
    """Display results for a session"""
    session = get_object_or_404(ResumeUploadSession, id=session_id)

    if not session.processed:
        messages.warning(request, 'This session has not been processed yet.')
        return redirect('home')

    return render(request, 'resume_app/results.html', {
        'session': session,
        'results': session.results,
        'criteria': session.criteria
    })


def session_list(request):
    """List all processing sessions"""
    sessions = ResumeUploadSession.objects.all()
    return render(request, 'resume_app/session_list.html', {
        'sessions': sessions
    })
