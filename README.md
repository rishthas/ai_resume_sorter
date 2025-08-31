# Resume Ranking System

A Python-based resume ranking system that uses OpenAI's GPT models to analyze and rank resumes based on job description requirements. The system automatically extracts candidate information, evaluates skills against job requirements, and generates detailed Excel reports.

## 🚀 Features

- **Job Description Based Ranking**: Automatically creates scoring criteria from your job description
- **AI-Powered Analysis**: Uses OpenAI GPT models to evaluate resumes intelligently
- **Multiple Format Support**: Processes PDF, DOCX, and TXT resume files
- **Candidate Information Extraction**: Automatically extracts names, emails, and phone numbers
- **Excel Report Generation**: Creates formatted Excel files with rankings and detailed scores
- **Dynamic Scoring**: Scoring criteria adapts to your specific job requirements
- **Configurable Settings**: All paths and settings managed through environment variables

## 📋 Requirements

- Python 3.8 or higher
- OpenAI API key
- Virtual environment (recommended)

## 🛠 Installation

1. **Clone or download the project files**

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Create a `.env` file in the project root directory with the following variables:

```env
# Required: OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Required: File and Folder Paths
INPUT_FOLDER=/path/to/your/resume/folder
OUTPUT_EXCEL=/path/to/output/resume_rankings.xlsx
JD_FILE=/path/to/your/job_description.txt

# Required: AI Model Configuration
MODEL=gpt-3.5-turbo
```

### Environment Variables Explained

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key from platform.openai.com | `sk-proj-abc123...` |
| `INPUT_FOLDER` | Path to folder containing resume files (PDF/DOCX/TXT) | `/home/user/resumes` |
| `OUTPUT_EXCEL` | Path where the Excel ranking report will be saved | `/home/user/rankings.xlsx` |
| `JD_FILE` | Path to your job description text file | `/home/user/job_description.txt` |
| `MODEL` | OpenAI model to use (gpt-3.5-turbo, gpt-4, etc.) | `gpt-3.5-turbo` |

## 📝 Job Description Setup

1. **Create a job description file** (e.g., `job_description.txt`)
2. **Include the following sections**:
   - Job title and overview
   - Required skills and technologies
   - Preferred/bonus skills
   - Experience requirements
   - Responsibilities

### Example Job Description:
```text
Job Title: Full Stack Developer

Job Description:
We are seeking a skilled Full Stack Developer to join our team.

Required Skills:
- Strong proficiency in Python and Django framework (3+ years)
- Experience with React.js and modern JavaScript (ES6+)
- Knowledge of HTML5, CSS3, and responsive design
- Experience with REST API development
- Proficiency with Git version control

Preferred Skills:
- Experience with test automation frameworks (Selenium, Jest, Pytest)
- Knowledge of mobile app development (Flutter/React Native)
- Experience with cloud platforms (AWS/Azure)
- Understanding of DevOps practices

Experience: 3-5 years of relevant experience required
```

## 🏃‍♂️ How to Run

1. **Ensure your environment is set up**:
   ```bash
   source venv/bin/activate  # Activate virtual environment
   ```

2. **Verify your configuration**:
   - `.env` file exists with all required variables
   - Job description file exists at the specified path
   - Resume folder exists and contains PDF/DOCX/TXT files
   - Output folder is writable

3. **Run the script**:
   ```bash
   python resume_ranker.py
   ```

## 📊 Output

The script generates an Excel file with the following columns:

| Column | Description |
|--------|-------------|
| Rank | Position based on total score |
| File Name | Original resume filename |
| Candidate Name | Extracted candidate name |
| Email | Extracted email address |
| Phone | Extracted phone number |
| [Skill] Score | Individual scores for each skill from job description |
| Total Score | Sum of all skill scores (out of 100) |
| Summary | AI-generated explanation of the scoring |

## 🔧 Troubleshooting

### Common Issues

1. **Missing Environment Variables**:
   ```
   [ERROR] Missing required environment variables in .env file:
   - OPENAI_API_KEY
   ```
   **Solution**: Check your `.env` file and ensure all required variables are set.

2. **Job Description Not Found**:
   ```
   [ERROR] Job description file not found: /path/to/job_description.txt
   ```
   **Solution**: Verify the `JD_FILE` path in your `.env` file and ensure the file exists.

3. **No Resume Files Found**:
   ```
   No resume files found in the input folder.
   ```
   **Solution**: Check that your `INPUT_FOLDER` contains PDF, DOCX, or TXT files.

4. **OpenAI API Errors**:
   ```
   [ERROR] OpenAI API failed: Error code: 401
   ```
   **Solution**: Verify your `OPENAI_API_KEY` is correct and has sufficient credits.

### File Format Support

- **PDF**: Supported (requires `textract`)
- **DOCX**: Supported (requires `textract`)
- **TXT**: Supported
- **DOC**: Limited support through `textract`

## 🎯 How It Works

1. **Configuration Loading**: Reads settings from `.env` file
2. **Job Description Analysis**: Uses OpenAI to create custom scoring criteria from your job description
3. **Resume Processing**: 
   - Extracts text from each resume file
   - Extracts candidate contact information
   - Scores resume against job requirements
4. **Ranking**: Sorts candidates by total score
5. **Report Generation**: Creates formatted Excel file with results

## 💡 Tips for Better Results

1. **Write Detailed Job Descriptions**: More specific requirements lead to better scoring
2. **Use Appropriate Model**: `gpt-4` provides more accurate results but costs more
3. **Organize Resume Files**: Keep only relevant resumes in the input folder
4. **Review Results**: The AI scoring should be used as a starting point for human review

## 📄 License

This project is open source. Feel free to modify and distribute as needed.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your environment configuration
3. Ensure all file paths are correct and accessible
