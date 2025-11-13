import os
import json
import zipfile
import tempfile
import shutil
import textract
import pandas as pd
from openai import OpenAI
from datetime import datetime


class ResumeProcessingService:
    """Service class to handle resume processing and ranking"""

    def __init__(self, openai_api_key, model='gpt-3.5-turbo'):
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model

    def extract_text(self, file_path):
        """Extract text from resume file"""
        try:
            text = textract.process(file_path).decode('utf-8')
            return text.strip()
        except Exception as e:
            print(f"[ERROR] Failed to extract {file_path}: {e}")
            return ""

    def create_optimized_prompt(self, job_description):
        """Use OpenAI to create an optimized ranking prompt from job description"""
        prompt = f"""
You are an expert HR consultant specializing in creating technical recruitment assessment criteria.

Given the following job description, please analyze it and create a comprehensive scoring system for evaluating candidates' resumes.

Your task:
1. Identify the key technical skills, frameworks, and technologies mentioned
2. Categorize them by importance (Required vs Preferred/Bonus)
3. Create a point-based scoring system with clear criteria
4. Provide scoring guidelines for different experience levels

Job Description:
{job_description}

Please respond with a JSON object containing the optimized prompt structure:
{{
    "required_skills": [
        {{
            "skill": "skill name",
            "max_points": number,
            "description": "what this skill involves"
        }}
    ],
    "bonus_skills": [
        {{
            "skill": "skill name",
            "max_points": number,
            "description": "what this skill involves"
        }}
    ],
    "scoring_guidelines": {{
        "expert": "criteria for expert level",
        "intermediate": "criteria for intermediate level",
        "beginner": "criteria for beginner level"
    }},
    "total_max_score": number,
    "evaluation_prompt": "detailed prompt for evaluating resumes against this job description"
}}

Make sure the total points add up to 100 and focus on the most critical requirements from the job description.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            print(f"[ERROR] Failed to create optimized prompt: {e}")
            return None

    def extract_candidate_info(self, text):
        """Extract candidate information from resume text"""
        prompt = f"""
You are an expert HR assistant extracting candidate information from resumes.

Please extract the following information from the resume:
- Candidate Name (full name)
- Email address
- Phone number

Respond in the following JSON format:
{{
    "name": "<candidate full name>",
    "email": "<email address>",
    "phone": "<phone number>"
}}

If any information is not found, use "Not Found" as the value.

Resume:
{text[:2000]}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = response.choices[0].message.content.strip()
            return answer
        except Exception as e:
            print(f"[ERROR] OpenAI API failed for candidate info extraction: {e}")
            return None

    def rank_resume(self, text, optimized_criteria):
        """Rank resume using the optimized criteria from job description"""
        if not optimized_criteria:
            return None

        try:
            criteria_data = json.loads(optimized_criteria)
            evaluation_prompt = criteria_data.get('evaluation_prompt', '')

            # Create the actual ranking prompt
            prompt = f"""
{evaluation_prompt}

Please analyze the following resume and provide scores based on the criteria above.

Respond in the following JSON format:
{{
    "total_score": <number>,
    "skill_scores": {{
        "skill_name": <score>,
        ...
    }},
    "summary": "<brief explanation of scoring>"
}}

Resume:
{text[:3000]}
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            answer = response.choices[0].message.content.strip()
            return answer

        except json.JSONDecodeError:
            print("[ERROR] Could not parse optimized criteria from job description")
            return None
        except Exception as e:
            print(f"[ERROR] OpenAI API failed: {e}")
            return None

    def process_resume(self, file_path, filename, optimized_criteria):
        """Process a single resume file"""
        text = self.extract_text(file_path)
        if not text:
            return None

        print(f"Processing: {filename}...")

        # Extract candidate information
        candidate_info_result = self.extract_candidate_info(text)
        candidate_info = {}
        if candidate_info_result:
            try:
                candidate_info = json.loads(candidate_info_result)
            except json.JSONDecodeError:
                print(f"[!] Could not parse candidate info for {filename}")
                candidate_info = {"name": "Not Found", "email": "Not Found", "phone": "Not Found"}
        else:
            candidate_info = {"name": "Not Found", "email": "Not Found", "phone": "Not Found"}

        # Get ranking scores using optimized criteria
        ranking_result = self.rank_resume(text, optimized_criteria)
        if not ranking_result:
            return None

        try:
            # Parse the JSON response
            ranking_data = json.loads(ranking_result)
            total_score = ranking_data.get('total_score', 0)
            summary = ranking_data.get('summary', '')

            # Get skill scores from the new format
            skill_scores = ranking_data.get('skill_scores', {})

            # Create resume data record with dynamic skill columns
            resume_data = {
                'File Name': filename,
                'Candidate Name': candidate_info.get('name', 'Not Found'),
                'Email': candidate_info.get('email', 'Not Found'),
                'Phone': candidate_info.get('phone', 'Not Found'),
                'Total Score': total_score,
                'Summary': summary
            }

            # Add individual skill scores
            for skill, score in skill_scores.items():
                resume_data[f'{skill} Score'] = score

            print(f"[✔] {filename} - Total Score: {total_score}/100")
            return resume_data

        except json.JSONDecodeError:
            print(f"[!] {filename} → Could not parse ranking result.")
            return None
        except Exception as e:
            print(f"[!] {filename} → Error processing: {e}")
            return None

    def process_zip_file(self, zip_file_path, job_description):
        """
        Process a zip file containing resumes and return ranked results

        Args:
            zip_file_path: Path to the zip file containing resumes
            job_description: Job description text

        Returns:
            dict: Contains 'success', 'results', 'criteria', and optional 'error'
        """
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()

        try:
            # Extract zip file
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Find all resume files
            resume_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.lower().endswith(('.pdf', '.docx', '.txt', '.doc')):
                        resume_files.append(os.path.join(root, file))

            if not resume_files:
                return {
                    'success': False,
                    'error': 'No resume files found in the zip file. Please upload PDF, DOCX, or TXT files.'
                }

            # Create optimized criteria from job description
            print("Creating optimized ranking criteria from job description...")
            optimized_criteria = self.create_optimized_prompt(job_description)
            if not optimized_criteria:
                return {
                    'success': False,
                    'error': 'Failed to create optimized criteria from job description.'
                }

            # Process all resumes
            all_resume_data = []
            for resume_path in resume_files:
                filename = os.path.basename(resume_path)
                resume_data = self.process_resume(resume_path, filename, optimized_criteria)
                if resume_data:
                    all_resume_data.append(resume_data)

            if not all_resume_data:
                return {
                    'success': False,
                    'error': 'No resumes could be processed successfully.'
                }

            # Create DataFrame and sort by total score
            df = pd.DataFrame(all_resume_data)
            df = df.sort_values('Total Score', ascending=False)
            df.insert(0, 'Rank', range(1, len(df) + 1))

            # Parse criteria for display
            criteria_info = {}
            try:
                criteria_data = json.loads(optimized_criteria)
                criteria_info = {
                    'total_max_score': criteria_data.get('total_max_score', 100),
                    'required_skills': [skill['skill'] for skill in criteria_data.get('required_skills', [])],
                    'bonus_skills': [skill['skill'] for skill in criteria_data.get('bonus_skills', [])]
                }
            except:
                pass

            return {
                'success': True,
                'results': df.to_dict('records'),
                'total_processed': len(all_resume_data),
                'total_files': len(resume_files),
                'criteria': criteria_info
            }

        except zipfile.BadZipFile:
            return {
                'success': False,
                'error': 'Invalid zip file. Please upload a valid zip file.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing resumes: {str(e)}'
            }
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
