# Django Resume Sorter - Web Application

A Django web application that allows users to upload resumes in a zip file along with a job description, and get AI-powered rankings and analysis results on a beautiful web interface.

## Features

- **Web-Based Upload**: Upload resumes via a user-friendly web interface
- **ZIP File Support**: Upload multiple resumes at once in a single ZIP file
- **Job Description Analysis**: Paste or type the job description directly in the form
- **AI-Powered Ranking**: Uses OpenAI GPT models to intelligently rank candidates
- **Beautiful Results Display**: View ranked candidates with scores, contact info, and summaries
- **Session History**: Access previous analysis sessions
- **Admin Interface**: Manage upload sessions via Django admin
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- pip (Python package installer)

### Installation

1. **Clone the repository** (if you haven't already)

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   MODEL=gpt-3.5-turbo
   ```

4. **Run migrations** (if not already done):
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - Open your browser and go to: `http://localhost:8000`
   - Admin interface: `http://localhost:8000/admin`

## Usage Guide

### Uploading Resumes

1. **Navigate to the home page** (`http://localhost:8000`)

2. **Prepare your files**:
   - Create a ZIP file containing all the resumes you want to analyze
   - Supported formats: PDF, DOCX, TXT, DOC
   - Example: `resumes.zip` containing `john_doe.pdf`, `jane_smith.docx`, etc.

3. **Fill in the form**:
   - **Job Description**: Paste the complete job description including:
     - Job title and overview
     - Required skills and technologies
     - Preferred/bonus skills
     - Experience requirements
     - Responsibilities

   - **Upload ZIP File**: Select your prepared ZIP file

4. **Click "Process Resumes"**: The application will:
   - Extract all resumes from the ZIP file
   - Analyze the job description to create scoring criteria
   - Evaluate each resume against the criteria
   - Extract candidate contact information
   - Rank candidates by score

5. **View Results**: After processing, you'll be redirected to the results page showing:
   - Ranked list of candidates
   - Individual scores and summaries
   - Contact information (email, phone)
   - Job requirements analysis

### Viewing History

- Click "History" in the navigation to see all previous processing sessions
- Click "View Results" on any session to see the rankings again

### Admin Interface

Access the Django admin at `http://localhost:8000/admin` to:
- View all upload sessions
- See processing details
- Troubleshoot errors
- Manage data

## Project Structure

```
ai_resume_sorter/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── resume_ranker.py         # Original CLI script
├── db.sqlite3              # SQLite database
├── resume_sorter_project/   # Django project settings
│   ├── settings.py         # Project configuration
│   ├── urls.py            # Main URL routing
│   └── wsgi.py            # WSGI application
├── resume_app/             # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── forms.py           # Form definitions
│   ├── urls.py            # App URL routing
│   ├── admin.py           # Admin configuration
│   ├── services.py        # Resume processing service
│   ├── templatetags/      # Custom template filters
│   └── templates/         # HTML templates
│       └── resume_app/
│           ├── base.html      # Base template
│           ├── home.html      # Upload page
│           ├── results.html   # Results page
│           └── session_list.html  # History page
└── media/                  # Uploaded files (auto-created)
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes | - |
| `MODEL` | OpenAI model to use | No | `gpt-3.5-turbo` |
| `SECRET_KEY` | Django secret key | No | Auto-generated |
| `DEBUG` | Enable debug mode | No | `True` |
| `ALLOWED_HOSTS` | Allowed hosts (production) | No | `[]` |

### Recommended Models

- **gpt-3.5-turbo**: Fast and cost-effective, good for most use cases
- **gpt-4**: More accurate analysis, higher cost
- **gpt-4-turbo**: Balance between speed and accuracy

## API Usage and Costs

The application makes OpenAI API calls for:
1. **Job description analysis** (1 call per upload session)
2. **Candidate information extraction** (1 call per resume)
3. **Resume ranking** (1 call per resume)

**Example cost** (using gpt-3.5-turbo):
- Analyzing 10 resumes: ~$0.10-0.20 USD
- Analyzing 50 resumes: ~$0.50-1.00 USD

Costs vary based on:
- Resume length
- Job description complexity
- Model selected

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   - Ensure your `.env` file exists and contains `OPENAI_API_KEY`
   - Restart the Django server after adding the key

2. **"No resume files found in the zip file"**
   - Ensure your ZIP file contains PDF, DOCX, or TXT files
   - Check that files are not in nested folders

3. **Database errors**
   - Run `python manage.py migrate` to apply migrations
   - Delete `db.sqlite3` and run migrations again

4. **Import errors**
   - Reinstall dependencies: `pip install -r requirements.txt`
   - Ensure you're using Python 3.8+

5. **Textract extraction issues**
   - Ensure PDFs are not scanned images (OCR not included)
   - Try converting PDFs to DOCX format
   - Use text-based file formats when possible

## Development

### Running in Development Mode

```bash
# Start the development server
python manage.py runserver

# Run on a different port
python manage.py runserver 8080

# Run on all interfaces
python manage.py runserver 0.0.0.0:8000
```

### Creating Migrations

```bash
# After modifying models
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Collecting Static Files

```bash
# For production deployment
python manage.py collectstatic
```

## Production Deployment

### Preparation

1. **Update settings**:
   - Set `DEBUG = False` in `.env`
   - Configure `ALLOWED_HOSTS`
   - Set a strong `SECRET_KEY`

2. **Use a production database**:
   - PostgreSQL (recommended)
   - MySQL
   - SQLite (not recommended for production)

3. **Set up a production server**:
   - Use Gunicorn or uWSGI
   - Configure Nginx or Apache
   - Enable HTTPS

4. **Configure media and static files**:
   ```bash
   python manage.py collectstatic
   ```

### Example Gunicorn Setup

```bash
# Install Gunicorn
pip install gunicorn

# Run the application
gunicorn resume_sorter_project.wsgi:application --bind 0.0.0.0:8000
```

### Example Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Considerations

1. **Never commit `.env` file** - Contains sensitive API keys
2. **Use strong SECRET_KEY** in production
3. **Enable HTTPS** for production deployments
4. **Limit file upload sizes** - Default is 50MB
5. **Validate ZIP files** - Application checks for valid ZIP format
6. **Sanitize user input** - Django provides built-in protection

## Database Schema

### ResumeUploadSession Model

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| job_description | Text | Job description text |
| zip_file | File | Uploaded ZIP file |
| created_at | DateTime | Upload timestamp |
| processed | Boolean | Processing status |
| results | JSON | Ranking results |
| criteria | JSON | Scoring criteria |
| error_message | Text | Error details (if any) |

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source. See LICENSE file for details.

## Support

For issues or questions:
1. Check this documentation
2. Review the troubleshooting section
3. Check your environment configuration
4. Verify API keys and credentials

## Credits

Built with:
- Django - Web framework
- OpenAI GPT - AI analysis
- Bootstrap 5 - UI components
- Textract - Document parsing
- Pandas - Data processing
