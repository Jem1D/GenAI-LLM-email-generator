import streamlit as st
from langchain_community.document_loaders import WebBaseLoader

from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from scrape import get_cleaned_text_from_url
import re


def create_streamlit_app(llm, portfolio, clean_text):
    st.title("Job Seeker Cold Email Generator")
    st.write("Generate personalized cold emails to reach out to potential employers.")

    url_input = st.text_input("Enter a URL:", value="https://careers.adobe.com/us/en/job/R147746/2025-Intern-Software-Engineer")
    submit_button = st.button("Submit")

    if submit_button:
        try:
            # loader = WebBaseLoader([url_input])
            # data = clean_text(loader.load().pop().page_content)
            # data = re.sub(r'\s+', ' ', data).strip()
            # data = data.strip()[:6000]
            data = get_cleaned_text_from_url(url_input)
            data = data[:6000]
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(data)
            for job in jobs:
                job_text = job.get('description', '') + " " + ", ".join(job.get('skills', []))
                links = portfolio.query_links(job_text)
                filtered_links = [link for link in links if '#' not in link]
                email = llm.write_mail(job, filtered_links)
                st.code(email, language='markdown')
        except Exception as e:
            st.error(f"An Error Occurred: {e}")


if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)


