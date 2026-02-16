import pandas as pd
import chromadb
import uuid
import re
import os

def normalize_token(t: str) -> str:
    """
    Standardizes tech terms. 
    e.g. "React.js" -> "react" (matches "React" in portfolio)
    """
    t = str(t).lower().strip()
    # Remove dots so "Node.js" -> "nodejs", "React.js" -> "reactjs"
    t = t.replace('.', '') 
    # Remove "js" at the end if present
    t = re.sub(r'js$', '', t) 
    # Clean up other chars
    t = re.sub(r'[^a-z0-9 +#]', '', t)
    return " ".join(t.split())

class Portfolio:
    def __init__(self, file_path="resource/my_portfolio.csv"):
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Portfolio file not found at {file_path}")
            
        self.data = pd.read_csv(file_path).fillna("")
        self.chroma_client = chromadb.PersistentClient('vectorstore')
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")

    def load_portfolio(self):
        if self.collection.count() == 0:
            for _, row in self.data.iterrows():
                tech_stack = row.get('Techstack', '')
                desc = row.get('Description', '')
                project_name = row.get('Project', '')
                
                doc_text = f"{tech_stack} {desc} {project_name}"
                
                self.collection.add(
                    documents=[doc_text],
                    metadatas=[{
                        "project": project_name,
                        "link": row.get('Link', ''),
                        "tech": tech_stack
                    }],
                    ids=[str(uuid.uuid4())]
                )

    def relevant_skills(self, normalized_required_skills, top_k=5):
        self.load_portfolio()
        
        # Build a map of normalized user tokens to original display names
        user_skill_map = {}
        for _, row in self.data.iterrows():
            techs = str(row.get("Techstack", "")).split(",")
            for t in techs:
                norm = normalize_token(t)
                if norm:
                    user_skill_map[norm] = t.strip()

        matched_skills = []
        for req_skill_norm in normalized_required_skills:
            for user_skill_norm, user_skill_display in user_skill_map.items():
                
                # Check 1: Exact Match
                if req_skill_norm == user_skill_norm:
                    matched_skills.append(user_skill_display)
                    break
                
                # Check 2: Substring Match (Bidirectional)
                # Matches "Reactjs" (req) with "React" (user)
                if req_skill_norm in user_skill_norm or user_skill_norm in req_skill_norm:
                    # Filter out very short partial matches to avoid noise (e.g. "c" in "react")
                    if len(user_skill_norm) > 1 and len(req_skill_norm) > 1:
                        matched_skills.append(user_skill_display)
                        break
        
        matched_skills = list(set(matched_skills))

        # Query links
        query_text = " ".join(normalized_required_skills)
        results = self.collection.query(query_texts=[query_text], n_results=top_k)
        metadatas = results.get("metadatas", [[]])[0]

        projects = []
        seen_links = set()
        for m in metadatas:
            link = m.get("link", "")
            if link and link not in seen_links:
                projects.append({
                    "project": m.get("project", ""),
                    "link": link,
                    "tech": m.get("tech", "")
                })
                seen_links.add(link)

        return {
            "your_skills": matched_skills,
            "relevant_projects": projects
        }