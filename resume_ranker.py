import os
import textract
import json
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load .env file
load_dotenv()

# Validate required environment variables
api_key = os.getenv("OPENAI_API_KEY")
INPUT_FOLDER = os.getenv("INPUT_FOLDER")
OUTPUT_EXCEL = os.getenv("OUTPUT_EXCEL")
JD_FILE = os.getenv("JD_FILE")
MODEL = os.getenv("MODEL")

# Check all required environment variables
missing_vars = []
if not api_key:
    missing_vars.append("OPENAI_API_KEY")
if not INPUT_FOLDER:
    missing_vars.append("INPUT_FOLDER")
if not OUTPUT_EXCEL:
    missing_vars.append("OUTPUT_EXCEL")
if not JD_FILE:
    missing_vars.append("JD_FILE")
if not MODEL:
    missing_vars.append("MODEL")

if missing_vars:
    print("[ERROR] Missing required environment variables in .env file:")
    for var in missing_vars:
        print(f"  - {var}")
    print("\nPlease add all required variables to your .env file.")
    exit(1)

client = OpenAI(api_key=api_key)

# Display configuration
print(f"Configuration loaded:")
print(f"  INPUT_FOLDER: {INPUT_FOLDER}")
print(f"  OUTPUT_EXCEL: {OUTPUT_EXCEL}")
print(f"  JD_FILE: {JD_FILE}")
print(f"  MODEL: {MODEL}")
print("-" * 50)


def read_job_description():
    """Read job description from file"""
    try:
        with open(JD_FILE, "r", encoding="utf-8") as file:
            jd_content = file.read().strip()
        return jd_content
    except FileNotFoundError:
        print(f"[ERROR] Job description file not found: {JD_FILE}")
        print("Please create a job_description.txt file with the job requirements.")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read job description: {e}")
        return None


def create_optimized_prompt(job_description):
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
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print(f"[ERROR] Failed to create optimized prompt: {e}")
        return None


def extract_text(file_path):
    try:
        text = textract.process(file_path).decode("utf-8")
        return text.strip()
    except Exception as e:
        print(f"[ERROR] Failed to extract {file_path}: {e}")
        return ""


def extract_candidate_info(text):
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
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print(f"[ERROR] OpenAI API failed for candidate info extraction: {e}")
        return None


def rank_resume(text, optimized_criteria):
    """Rank resume using the optimized criteria from job description"""
    if not optimized_criteria:
        print(
            "[ERROR] No job description criteria available. Please ensure job_description.txt exists."
        )
        return None

    try:
        criteria_data = json.loads(optimized_criteria)
        evaluation_prompt = criteria_data.get("evaluation_prompt", "")

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

        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], temperature=0
        )
        answer = response.choices[0].message.content.strip()
        return answer

    except json.JSONDecodeError:
        print("[ERROR] Could not parse optimized criteria from job description")
        return None
    except Exception as e:
        print(f"[ERROR] OpenAI API failed: {e}")
        return None


def process_resume(file_path, optimized_criteria):
    text = extract_text(file_path)
    if not text:
        return None

    filename = os.path.basename(file_path)
    print(f"Processing: {filename}...")

    # Extract candidate information
    candidate_info_result = extract_candidate_info(text)
    candidate_info = {}
    if candidate_info_result:
        try:
            candidate_info = json.loads(candidate_info_result)
        except json.JSONDecodeError:
            print(f"[!] Could not parse candidate info for {filename}")
            candidate_info = {
                "name": "Not Found",
                "email": "Not Found",
                "phone": "Not Found",
            }
    else:
        candidate_info = {
            "name": "Not Found",
            "email": "Not Found",
            "phone": "Not Found",
        }

    # Get ranking scores using optimized criteria
    ranking_result = rank_resume(text, optimized_criteria)
    if not ranking_result:
        return None

    try:
        # Parse the JSON response
        ranking_data = json.loads(ranking_result)
        total_score = ranking_data.get("total_score", 0)
        summary = ranking_data.get("summary", "")

        # Get skill scores from the new format
        skill_scores = ranking_data.get("skill_scores", {})

        # Create resume data record with dynamic skill columns
        resume_data = {
            "File Name": filename,
            "Candidate Name": candidate_info.get("name", "Not Found"),
            "Email": candidate_info.get("email", "Not Found"),
            "Phone": candidate_info.get("phone", "Not Found"),
            "Total Score": total_score,
            "Summary": summary,
        }

        # Add individual skill scores
        for skill, score in skill_scores.items():
            resume_data[f"{skill} Score"] = score

        print(f"[✔] {filename} - Total Score: {total_score}/100")
        return resume_data

    except json.JSONDecodeError:
        print(f"[!] {filename} → Could not parse ranking result.")
        return None
    except Exception as e:
        print(f"[!] {filename} → Error processing: {e}")
        return None


def main():
    print("Resume Ranking System - Job Description Based")
    print("=" * 80)

    # Read and process job description
    print("Reading job description...")
    job_description = read_job_description()
    if not job_description:
        print("[ERROR] Job description is required to run this system.")
        print("Please create a job_description.txt file with the job requirements.")
        return

    print("Creating optimized ranking criteria from job description...")
    optimized_criteria = create_optimized_prompt(job_description)
    if not optimized_criteria:
        print("[ERROR] Failed to create optimized criteria from job description.")
        return

    print("✓ Optimized criteria created successfully")
    print("-" * 80)

    files = os.listdir(INPUT_FOLDER)
    resume_files = [f for f in files if f.lower().endswith((".pdf", ".docx", ".txt"))]

    if not resume_files:
        print("No resume files found in the input folder.")
        return

    print(f"Found {len(resume_files)} resume(s) to process...")
    print("-" * 80)

    # Process all resumes and collect data
    all_resume_data = []
    for f in resume_files:
        resume_data = process_resume(os.path.join(INPUT_FOLDER, f), optimized_criteria)
        if resume_data:
            all_resume_data.append(resume_data)

    if not all_resume_data:
        print("No resumes could be processed successfully.")
        return

    # Create DataFrame and sort by total score (descending)
    df = pd.DataFrame(all_resume_data)
    df = df.sort_values("Total Score", ascending=False)

    # Add rank column
    df.insert(0, "Rank", range(1, len(df) + 1))

    # Save to Excel with formatting
    try:
        with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Resume Rankings", index=False)

            # Get the workbook and worksheet for formatting
            workbook = writer.book
            worksheet = writer.sheets["Resume Rankings"]

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print("=" * 80)
        print(f"Excel file created successfully: {OUTPUT_EXCEL}")
        print(f"Total resumes processed: {len(all_resume_data)}")

        # Display job description based criteria if available
        if optimized_criteria:
            try:
                criteria_data = json.loads(optimized_criteria)
                print(f"\nRanking based on Job Description criteria:")
                print(
                    f"Total possible score: {criteria_data.get('total_max_score', 100)}"
                )
                print(
                    "Required skills:",
                    [
                        skill["skill"]
                        for skill in criteria_data.get("required_skills", [])
                    ],
                )
                print(
                    "Bonus skills:",
                    [skill["skill"] for skill in criteria_data.get("bonus_skills", [])],
                )
            except:
                pass

        print(f"\nTop 3 candidates:")
        for i, row in df.head(3).iterrows():
            print(
                f"{row['Rank']}. {row['Candidate Name']} - {row['Total Score']}/100 points"
            )

    except Exception as e:
        print(f"Error creating Excel file: {e}")
        print("Falling back to CSV...")
        csv_file = OUTPUT_EXCEL.replace(".xlsx", ".csv")
        df.to_csv(csv_file, index=False)
        print(f"CSV file created: {csv_file}")


if __name__ == "__main__":
    main()
