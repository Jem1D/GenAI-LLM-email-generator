# import streamlit as st
# from chains import Chain
# from portfolio import Portfolio
# from utils import clean_text
# from scrape import get_cleaned_text_from_url
# import traceback

# st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
# st.title("Job Post Analyzer")

# url_input = st.text_input("Enter a job URL", value="https://jobs.ashbyhq.com/batoncorporation/bb3ab630-5e59-48b5-9794-00a225879a66")
# submit = st.button("Submit")

# def pretty(items):
#     if not items:
#         return "None found"
#     return "\n".join([f"• {i}" for i in items])

# if submit and url_input:
#     try:
#         with st.spinner("Scraping and analyzing..."):
#             raw = get_cleaned_text_from_url(url_input)
#             text = clean_text(raw[:30000])

#             chain = Chain()
#             jobs = chain.extract_jobs(text)
#             if not jobs:
#                 st.error("Could not extract job details.")
#                 st.stop()
            
#             job = jobs[0]
#             desc = job.get("description","")
#             full_job_text = f"{job.get('role','')} {desc} {job.get('skills','')}"

#             # --- JOB SUMMARY ---
#             st.subheader("Job Summary")
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.write("**Role:**", job.get("role",""))
#                 st.write("**Company:**", job.get("company","Unknown"))
#                 st.write("**Location:**", job.get("location",""))
#             with col2:
#                 st.write("**Experience:**", job.get("experience",""))

#             # --- WORK AUTHORIZATION ---
#             visa_data = chain.detect_work_authorization(text)
#             visa_flags = visa_data.get("visa_analysis", {})
#             st.subheader("Work Authorization")
            
#             is_restricted = False
            
#             # Check for specific restrictions
#             if visa_flags.get("us_citizen_only"):
#                 st.error("🔴 RESTRICTED: US Citizens Only")
#                 is_restricted = True
#             if visa_flags.get("green_card_only"):
#                 st.error("🔴 RESTRICTED: Green Card / Permanent Resident Only")
#                 is_restricted = True
#             if visa_flags.get("security_clearance"):
#                 st.error("🔴 RESTRICTED: Security Clearance Required")
#                 is_restricted = True
#             if visa_flags.get("no_h1b"):
#                 st.error("🔴 RESTRICTED: No H1B Sponsorship")
#                 is_restricted = True
#             if visa_flags.get("no_opt_cpt"):
#                 st.error("🔴 RESTRICTED: No CPT/OPT Accepted")
#                 is_restricted = True

#             if is_restricted:
#                 st.write(f"**Analysis:** {visa_data.get('analysis')}")
#             else:
#                 st.success("No strict visa restrictions detected (Standard CPT/OPT/H1B likely okay).")
#                 st.caption(f"Analysis: {visa_data.get('analysis')}")

#             st.divider()

#             # --- SKILLS ---
#             skills_data = chain.extract_required_skills(full_job_text)
#             portfolio = Portfolio()
#             match = portfolio.relevant_skills(skills_data["normalized_required_skills"])

#             col_req, col_match = st.columns(2)
#             with col_req:
#                 st.subheader("Required Skills")
#                 st.text(pretty(skills_data["required_skills"]))

#             with col_match:
#                 st.subheader("Your Matching Skills")
#                 if match["your_skills"]:
#                     for skill in match["your_skills"]:
#                         st.markdown(f":green[**{skill}**]")
#                 else:
#                     st.write("No direct matches found in portfolio.")

#             st.divider()

#             # --- PROJECTS & EMAIL ---
#             st.subheader("Relevant Projects")
#             if match["relevant_projects"]:
#                 for p in match["relevant_projects"]:
#                     st.markdown(f"**[{p['project']}]({p['link']})**")
#                     st.caption(f"Stack: {p['tech']}")
#                     st.write("---")
            
#             if st.button("Generate Cold Email"):
#                 links = [p["link"] for p in match["relevant_projects"] if p["link"]]
#                 email = chain.write_mail(job, links, match["your_skills"])
#                 st.subheader("Draft Email")
#                 st.code(email, language='markdown')

#     except Exception:
#         st.error("An error occurred")
#         st.write(traceback.format_exc())



import streamlit as st
from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from scrape import get_cleaned_text_from_url
import traceback

st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
st.title("Job Post Analyzer")

url_input = st.text_input("Enter a job URL", value="https://jobs.ashbyhq.com/batoncorporation/bb3ab630-5e59-48b5-9794-00a225879a66")
submit = st.button("Submit")

def pretty(items):
    if not items:
        return "None found"
    return "\n".join([f"• {i}" for i in items])

if submit and url_input:
    try:
        with st.spinner("Scraping and analyzing..."):
            # 1. Scrape
            raw = get_cleaned_text_from_url(url_input)
            text = clean_text(raw[:30000]) # Keep raw text for analysis

            chain = Chain()
            
            # 2. Analyze Job (ONE Single LLM Call)
            # This returns Job Details + Skills + Visa Analysis all at once
            job_data = chain.analyze_job(text)
            
            if not job_data:
                st.error("Could not analyze job details.")
                st.stop()

            # --- SECTION: JOB SUMMARY ---
            st.subheader("Job Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Role:**", job_data.get("role", "Unknown"))
                st.write("**Company:**", job_data.get("company", "Unknown"))
                st.write("**Location:**", job_data.get("location", "Unknown"))
            with col2:
                st.write("**Experience:**", job_data.get("experience", "Unknown"))

            # --- SECTION: WORK AUTHORIZATION ---
            visa_flags = job_data.get("visa_analysis", {})
            st.subheader("Work Authorization")
            
            is_restricted = False
            
            if visa_flags.get("us_citizen_only"):
                st.error("🔴 RESTRICTED: US Citizens Only")
                is_restricted = True
            if visa_flags.get("green_card_only"):
                st.error("🔴 RESTRICTED: Green Card / Permanent Resident Only")
                is_restricted = True
            if visa_flags.get("security_clearance"):
                st.error("🔴 RESTRICTED: Security Clearance Required")
                is_restricted = True
            if visa_flags.get("no_h1b"):
                st.error("🔴 RESTRICTED: No H1B Sponsorship")
                is_restricted = True
            if visa_flags.get("no_opt_cpt"):
                st.error("🔴 RESTRICTED: No CPT/OPT Accepted")
                is_restricted = True

            if is_restricted:
                st.write(f"**Analysis:** {visa_flags.get('analysis', 'Restriction detected')}")
            else:
                st.success("No strict visa restrictions detected (Standard CPT/OPT/H1B likely okay).")
                st.caption(f"Analysis: {visa_flags.get('analysis', '')}")

            st.divider()

            # --- SECTION: SKILLS MATCHING ---
            # The chain automatically added 'normalized_required_skills' for us
            required_skills = job_data.get("required_skills", [])
            normalized_skills = job_data.get("normalized_required_skills", [])
            
            portfolio = Portfolio()
            match = portfolio.relevant_skills(normalized_skills)

            col_req, col_match = st.columns(2)
            
            # LEFT COLUMN: Required Skills
            with col_req:
                st.subheader("Required Skills")
                if required_skills:
                    for skill in required_skills:
                        st.markdown(f"- {skill}")
                else:
                    st.markdown("No specific technical skills extracted.")

            # RIGHT COLUMN: Matching Skills (Visually identical structure, just colored)
            with col_match:
                st.subheader("Your Matching Skills")
                if match["your_skills"]:
                    for skill in match["your_skills"]:
                        # Use same bullet format, but add color
                        st.markdown(f"- :green[{skill}]")
                else:
                    st.markdown("No direct matches found in portfolio.")

            st.divider()

            # --- SECTION: RELEVANT PROJECTS (COMPACT) ---
            st.subheader("Relevant Projects")
            if match["relevant_projects"]:
                for p in match["relevant_projects"]:
                    # Combined into one line: [Title](Link) - Stack
                    st.markdown(f"* **[{p['project']}]({p['link']})** — *{p['tech']}*")
            else:
                st.write("No specific projects matched.")
            
            # --- SECTION: EMAIL GENERATION ---
            if st.button("Generate Cold Email"):
                links = [p["link"] for p in match["relevant_projects"] if p["link"]]
                # Pass the full job_data object since it contains description, role, etc.
                email = chain.write_mail(job_data, links, match["your_skills"])
                st.subheader("Draft Email")
                st.code(email, language='markdown')

    except Exception:
        st.error("An error occurred")
        st.write(traceback.format_exc())