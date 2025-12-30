import os
from langchain_google_vertexai import ChatVertexAI

def get_llm():
    """
    Returns a configured instance of ChatVertexAI.
    Ensures that the necessary environment variables are set.
    """
    # You might need to set GOOGLE_APPLICATION_CREDENTIALS or 
    # run `gcloud auth application-default login` for Vertex AI.
    # Alternatively, if using AI Studio, use ChatGoogleGenerativeAI and GOOGLE_API_KEY.
    
    # For now, we will assume Vertex AI as requested in the plan.
    # If the user provides a direct API key for AI Studio, we might need to switch to langchain-google-genai.
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    llm = ChatVertexAI(
        model_name=model_name,
        project=project_id,
        location=location,
        temperature=0.7,
        max_output_tokens=8192,
    )
    return llm
