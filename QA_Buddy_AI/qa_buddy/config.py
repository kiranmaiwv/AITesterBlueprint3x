import os


class Config:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    QDRANT_URL = os.environ.get("QDRANT_URL", "")
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
    QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "qa_buddy")

    JIRA_URL = os.environ.get("JIRA_URL", "")
    JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
    JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
    JIRA_JQL = os.environ.get("JIRA_JQL", "")

    # fastembed runs the model locally — no API key needed
    EMBEDDING_DIM = 384  # bge-small-en-v1.5

    @property
    def is_groq_configured(self):
        return bool(self.GROQ_API_KEY)

    @property
    def is_qdrant_configured(self):
        return bool(self.QDRANT_URL) and bool(self.QDRANT_API_KEY)

    @property
    def is_jira_configured(self):
        return all([self.JIRA_URL, self.JIRA_EMAIL, self.JIRA_API_TOKEN])

    @property
    def is_embedder_ready(self):
        return True  # fastembed runs locally, always available


config = Config()
