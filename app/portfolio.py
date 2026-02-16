import pandas as pd
import chromadb
import uuid
import os


class Portfolio:
    def __init__(self, file_path="resource/my_portfolio.csv"):
        self.file_path = file_path
        self.data = pd.read_csv(file_path)
        self.chroma_client = chromadb.PersistentClient('vectorstore')
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")
        # self.chroma_client.delete_collection("portfolio")


    def load_portfolio(self):
        if not self.collection.count():
            for _, row in self.data.iterrows():
                # Combine tech stack + description for semantic context
                doc_text = f"{row['Techstack']}. {row['Description']}"
                self.collection.add(
                    documents=[doc_text],
                    metadatas={
                        "project": row["Project"],
                        "link": row["Link"]
                    },
                    ids=[str(uuid.uuid4())]
                )

    def query_links(self, job_text):
        # Accept a single text string (e.g., full job description + skills)
        results = self.collection.query(query_texts=[job_text], n_results=3)
        metadatas = results.get("metadatas", [[]])[0]

        # Return formatted list of relevant projects and links
        return [
            f"{meta['project']}: {meta['link']}"
            for meta in metadatas
        ]
