# import os
# import json
# import re
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.exceptions import OutputParserException

# load_dotenv()

# def normalize_token(t: str) -> str:
#     """
#     Standardizes tech terms. 
#     e.g. "React.js" -> "react" (matches "React" in portfolio)
#     """
#     t = str(t).lower().strip()
#     t = t.replace('.', '') 
#     t = re.sub(r'js$', '', t) 
#     t = re.sub(r'[^a-z0-9 +#]', '', t)
#     return " ".join(t.split())

# class Chain:
#     def __init__(self):
#         # Llama-3.3-70b-Versatile (Current SOTA on Groq Free Tier)
#         self.llm = ChatGroq(
#             temperature=0.0, 
#             groq_api_key=os.getenv("GROQ_API_KEY"), 
#             model_name="llama-3.3-70b-versatile"
#         )

#     def clean_json_output(self, content):
#         """
#         Cleans output to ensure valid JSON.
#         """
#         content = str(content)
#         if "```" in content:
#             content = content.replace("```json", "").replace("```", "")
#         content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
#         return content.strip()

#     def extract_jobs(self, cleaned_text):
#         prompt_extract = PromptTemplate.from_template(
#             """
#             ### SCRAPED TEXT FROM WEBSITE:
#             {page_data}

#             ### INSTRUCTION:
#             The scraped text is from a career page. Extract the job postings.
#             Return a valid JSON array where each item has:
#             - role: The job title
#             - company: The name of the company hiring
#             - experience: Years of experience or level (e.g., Junior, Senior)
#             - skills: A list of specific technical skills mentioned
#             - description: A brief summary of the job responsibilities
#             - location: The job location
            
#             STRICTLY RETURN ONLY JSON. NO PREAMBLE.
#             """
#         )
#         chain_extract = prompt_extract | self.llm
#         res = chain_extract.invoke(input={"page_data": cleaned_text})
        
#         clean_content = self.clean_json_output(res.content)
        
#         try:
#             parsed = json.loads(clean_content)
#         except json.JSONDecodeError:
#             try:
#                 start = clean_content.find('[')
#                 end = clean_content.rfind(']') + 1
#                 if start != -1 and end != -1:
#                     parsed = json.loads(clean_content[start:end])
#                 else:
#                     start = clean_content.find('{')
#                     end = clean_content.rfind('}') + 1
#                     parsed = [json.loads(clean_content[start:end])]
#             except Exception:
#                 raise OutputParserException("Unable to parse jobs")
                
#         return parsed if isinstance(parsed, list) else [parsed]

#     def extract_required_skills(self, job_text):
#         prompt = PromptTemplate.from_template(
#             """
#             ### JOB DESCRIPTION:
#             {job}

#             ### INSTRUCTION:
#             Identify ALL technical skills, tools, and methodologies required or preferred for this job.
            
#             INCLUDE:
#             1. Languages & Frameworks (Python, React, C, etc.)
#             2. Tools & Platforms (AWS, Docker, Git, SVN, Jira, Kubernetes)
#             3. Methodologies (Agile, Scrum, CI/CD, TDD)
#             4. Concepts (REST API, Microservices, System Design)
            
#             Return JSON: {{"required_skills": ["skill1", "skill2"]}}
#             """
#         )
#         chain = prompt | self.llm
#         res = chain.invoke({"job": job_text})
        
#         clean_content = self.clean_json_output(res.content)
        
#         try:
#             parsed = json.loads(clean_content)
#         except json.JSONDecodeError:
#             try:
#                 start = clean_content.find('{')
#                 end = clean_content.rfind('}') + 1
#                 parsed = json.loads(clean_content[start:end])
#             except:
#                 parsed = {"required_skills": []}

#         skills = parsed.get("required_skills", [])
#         unique_skills = list(set(skills))
        
#         return {
#             "required_skills": unique_skills,
#             "normalized_required_skills": [normalize_token(s) for s in unique_skills]
#         }

#     def detect_work_authorization(self, job_text):
#         prompt = PromptTemplate.from_template(
#             """
#             ### JOB TEXT:
#             {job}

#             ### INSTRUCTION:
#             Analyze the text for STRICT work authorization restrictions.
            
#             CRITICAL: Check for these restrictive phrases (or variations):
#             1. "U.S. Person" (This implies Citizen or Green Card under ITAR).
#             2. "Ability to obtain a security clearance" (This usually requires Citizenship).
#             3. "US Citizens Only", "US Citizenship required", "Must be a US Citizen".
#             4. "Green Card Only", "Green Card Holder", "GC only".
#             5. "No visa sponsorship", "Must be authorized to work without sponsorship".
            
#             Return ONLY valid JSON:
#             {{
#               "visa_analysis": {{
#                   "green_card_only": boolean, 
#                   "us_citizen_only": boolean, 
#                   "no_h1b": boolean, 
#                   "no_opt_cpt": boolean, 
#                   "security_clearance": boolean 
#               }},
#               "analysis": "Brief quote of the restriction found, or 'No restrictions found'"
#             }}
#             """
#         )
#         chain = prompt | self.llm
#         res = chain.invoke({"job": job_text})
        
#         clean_content = self.clean_json_output(res.content)
        
#         try:
#             parsed = json.loads(clean_content)
#         except Exception:
#              # Fallback default
#             parsed = {
#                 "visa_analysis": {
#                     "green_card_only": False,
#                     "us_citizen_only": False,
#                     "no_h1b": False,
#                     "no_opt_cpt": False,
#                     "security_clearance": False
#                 }, 
#                 "analysis": "Error parsing visa data"
#             }

#         return parsed

#     def write_mail(self, job, links, matched_skills):
#         prompt_email = PromptTemplate.from_template(
#             """
#             ### JOB DESCRIPTION:
#             {job_description}

#             ### CANDIDATE'S MATCHING SKILLS:
#             {matched_skills}

#             ### CANDIDATE'S PORTFOLIO LINKS:
#             {link_list}

#             ### INSTRUCTION:
#             You are Jemil Dharia, a Master’s student in Computer Science at Arizona State University.
#             Write a cold email to the hiring manager.
            
#             Guidelines:
#             1. Keep it professional but concise.
#             2. Mention the company name if available.
#             3. Connect your {matched_skills} to their requirements.
#             4. Do not include a subject line in the body.
#             """
#         )
        
#         chain_email = prompt_email | self.llm
#         res = chain_email.invoke({
#             "job_description": str(job), 
#             "link_list": links,
#             "matched_skills": ", ".join(matched_skills)
#         })
        
#         return self.clean_json_output(res.content)


import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.exceptions import OutputParserException

load_dotenv()

def normalize_token(t: str) -> str:
    """
    Standardizes tech terms. 
    e.g. "React.js" -> "react" (matches "React" in portfolio)
    """
    t = str(t).lower().strip()
    t = t.replace('.', '') 
    t = re.sub(r'js$', '', t) 
    t = re.sub(r'[^a-z0-9 +#]', '', t)
    return " ".join(t.split())

class Chain:
    def __init__(self):
        # Llama-3.3-70b-Versatile
        self.llm = ChatGroq(
            temperature=0.0, 
            groq_api_key=os.getenv("GROQ_API_KEY"), 
            model_name="llama-3.3-70b-versatile"
        )

    def clean_json_output(self, content):
        content = str(content)
        if "```" in content:
            content = content.replace("```json", "").replace("```", "")
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        return content.strip()

    def analyze_job(self, cleaned_text):
        """
        Consolidated function: Extracts Job Details, Skills, and Visa Analysis in ONE pass.
        This saves ~66% of input tokens compared to separate calls.
        """
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}

            ### INSTRUCTION:
            You are an expert technical recruiter. Extract job details, technical requirements, and legal restrictions.
            
            1. **Job Details**: Extract role, company, location, experience level, and a detailed description.
            2. **Skills**: Identify ALL technical skills, tools, and methodologies (Languages, Cloud, DevOps, Agile, etc.).
            3. **Work Authorization (CRITICAL)**: specific search for:
               - "U.S. Person" / "Citizen Only" / "Security Clearance"
               - "Green Card" / "Permanent Resident"
               - "No Sponsorship" / "No H1B" / "No CPT/OPT"

            ### OUTPUT FORMAT (STRICT JSON ONLY):
            {{
                "role": "Job Title",
                "company": "Company Name",
                "location": "City, State",
                "experience": "Junior/Senior/Years",
                "description": "Detailed summary...",
                "required_skills": ["Python", "React", "AWS", "Agile", "Git", "Docker"],
                "visa_analysis": {{
                    "green_card_only": boolean,
                    "us_citizen_only": boolean,
                    "no_h1b": boolean,
                    "no_opt_cpt": boolean,
                    "security_clearance": boolean,
                    "analysis": "Quote the specific restriction found or 'No restrictions detected'"
                }}
            }}
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        
        clean_content = self.clean_json_output(res.content)
        
        try:
            parsed = json.loads(clean_content)
        except json.JSONDecodeError:
            try:
                # Fallback extraction logic
                start = clean_content.find('{')
                end = clean_content.rfind('}') + 1
                parsed = json.loads(clean_content[start:end])
            except Exception:
                raise OutputParserException("Unable to parse job analysis")
        
        # Normalize skills immediately for the portfolio matcher
        raw_skills = parsed.get("required_skills", [])
        parsed["normalized_required_skills"] = [normalize_token(s) for s in list(set(raw_skills))]
        
        return parsed

    def write_mail(self, job, links, matched_skills):
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}

            ### CANDIDATE'S MATCHING SKILLS:
            {matched_skills}

            ### CANDIDATE'S PORTFOLIO LINKS:
            {link_list}

            ### INSTRUCTION:
            You are Jemil Dharia, a Master’s student in Computer Science at Arizona State University.
            Write a cold email to the hiring manager.
            
            Guidelines:
            1. Keep it professional but concise.
            2. Mention the company name if available.
            3. Connect your {matched_skills} to their requirements.
            4. Do not include a subject line in the body.
            """
        )
        
        chain_email = prompt_email | self.llm
        res = chain_email.invoke({
            "job_description": json.dumps(job), # Pass the whole job object for context
            "link_list": links,
            "matched_skills": ", ".join(matched_skills)
        })
        
        return self.clean_json_output(res.content)