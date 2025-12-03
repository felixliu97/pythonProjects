"""
Amazon Bedrock API Cheatsheet (Python / boto3)
==============================================
This script provides a comprehensive reference for interacting with Amazon Bedrock using the AWS SDK for Python (boto3).

PREREQUISITES:
--------------
1.  **AWS Account**: You must have an active AWS account.
2.  **AWS Credentials**: Configure your local environment with valid credentials.
    -   Run `aws configure` in your terminal.
    -   Or set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` env vars.
3.  **Model Access**: You MUST enable access to specific models in the AWS Bedrock Console.
    -   Go to AWS Console -> Bedrock -> Model access -> Manage model access.
    -   Request access for Anthropic, Meta, Amazon, etc.
4.  **IAM Permissions**: Your AWS user/role needs permissions like:
    -   `bedrock:ListFoundationModels`
    -   `bedrock:InvokeModel`
    -   `bedrock:InvokeModelWithResponseStream`
    -   `bedrock:Retrieve` (for Knowledge Bases)
    -   `bedrock:RetrieveAndGenerate` (for Knowledge Bases)
5.  **Python Libraries**: Install boto3: `pip install boto3`

SECTIONS:
---------
1. Setup & Clients
2. List Available Models
3. Text Generation (Claude 3, Llama 3, Titan)
4. Streaming Responses
5. Embeddings
6. Image Generation
7. Knowledge Bases (Retrieve & Generate)
"""

import boto3
import json
import base64

# ==============================================================================
# 1. SETUP & CLIENTS
# ==============================================================================

def get_clients(region_name="us-east-1"):
    """
    Initializes the necessary Boto3 clients for Bedrock.
    
    Bedrock is split into multiple services/clients:
    1. 'bedrock': The Control Plane.
       - Used for management tasks like listing available models, getting model details, 
         and managing custom models.
       - It is NOT used for running inference.
       
    2. 'bedrock-runtime': The Data Plane.
       - Used for invoking models (running inference) for text, image, and embeddings.
       - This is the main client you will use for generation.
       
    3. 'bedrock-agent-runtime': The Agent Data Plane.
       - Used for interacting with Agents and Knowledge Bases.
       - Required for RAG (Retrieve) and RetrieveAndGenerate APIs.
    
    Args:
        region_name (str): AWS region (e.g., 'us-east-1', 'us-west-2'). 
                           Ensure the models you need are available in this region.
    """
    bedrock = boto3.client(service_name='bedrock', region_name=region_name)
    bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name=region_name)
    bedrock_agent_runtime = boto3.client(service_name='bedrock-agent-runtime', region_name=region_name)
    return bedrock, bedrock_runtime, bedrock_agent_runtime

# ==============================================================================
# 2. LIST AVAILABLE MODELS
# ==============================================================================

def list_models(bedrock_client):
    """
    Lists all foundation models available in the current region.
    
    Prerequisite:
    - IAM Permission: `bedrock:ListFoundationModels`
    
    Useful for:
    - Finding the exact `modelId` needed for invocation (e.g., "anthropic.claude-3-sonnet...").
    - Checking which models are supported in your region.
    """
    response = bedrock_client.list_foundation_models()
    
    print("Available Models:")
    for model in response['modelSummaries']:
        # modelId is the key identifier you need for invoke_model
        print(f"- {model['modelId']} ({model['providerName']})")

# ==============================================================================
# 3. TEXT GENERATION (INVOKE MODEL)
# ==============================================================================

def invoke_claude_3(runtime_client, prompt):
    """
    Invokes Anthropic Claude 3 (Sonnet, Haiku, or Opus).
    
    Prerequisite:
    - Model Access: Enabled for "Claude 3 Sonnet" in Bedrock Console.
    
    API Structure (Messages API):
    - Claude 3 uses the 'messages' format, similar to OpenAI's chat format.
    - `anthropic_version` is required.
    - `max_tokens` controls response length.
    """
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # Request body must be JSON formatted specifically for the model family
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }
    
    # invoke_model is a synchronous call
    response = runtime_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )
    
    # Response body is a stream, needs reading and decoding
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def invoke_llama_3(runtime_client, prompt):
    """
    Invokes Meta Llama 3 (8B Instruct).
    
    Prerequisite:
    - Model Access: Enabled for "Llama 3" in Bedrock Console.
    
    API Structure:
    - Llama 3 uses a simpler prompt-based structure (or chat template if formatted manually).
    - `max_gen_len`: Max new tokens to generate.
    - `temperature`: Randomness (0-1).
    - `top_p`: Nucleus sampling.
    """
    model_id = "meta.llama3-8b-instruct-v1:0"
    
    body = {
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature": 0.5,
        "top_p": 0.9
    }
    
    response = runtime_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['generation']

def invoke_titan_text(runtime_client, prompt):
    """
    Invokes Amazon Titan Text Express.
    
    Prerequisite:
    - Model Access: Enabled for "Titan Text G1 - Express".
    
    API Structure:
    - `inputText`: The prompt.
    - `textGenerationConfig`: Model parameters like maxTokenCount, temperature.
    """
    model_id = "amazon.titan-text-express-v1"
    
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0,
            "topP": 1
        }
    }
    
    response = runtime_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['results'][0]['outputText']

# ==============================================================================
# 4. STREAMING RESPONSES
# ==============================================================================

def invoke_with_stream(runtime_client, prompt):
    """
    Invokes a model with streaming response (Token-by-token).
    
    Why use this?
    - Reduces perceived latency (Time To First Token).
    - Better UX for chat applications.
    
    How it works:
    - Uses `invoke_model_with_response_stream`.
    - Returns an event stream generator.
    - You must iterate over the stream and decode chunks.
    """
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    }
    
    response = runtime_client.invoke_model_with_response_stream(
        modelId=model_id,
        body=json.dumps(body)
    )
    
    stream = response.get('body')
    if stream:
        for event in stream:
            # Each 'event' is a dictionary containing a 'chunk'
            chunk = event.get('chunk')
            if chunk:
                # Decode the bytes in the chunk
                chunk_json = json.loads(chunk.get('bytes').decode())
                
                # Claude 3 specific stream format:
                # Look for 'content_block_delta' events with 'text_delta'
                if chunk_json['type'] == 'content_block_delta':
                    if chunk_json['delta']['type'] == 'text_delta':
                        print(chunk_json['delta']['text'], end='', flush=True)

# ==============================================================================
# 5. EMBEDDINGS
# ==============================================================================

def generate_embeddings(runtime_client, text):
    """
    Generates vector embeddings for text using Titan Embeddings.
    
    Prerequisite:
    - Model Access: Enabled for "Titan Embeddings G1 - Text".
    
    Usage:
    - Convert text to vectors for RAG (Retrieval Augmented Generation), 
      semantic search, or clustering.
    """
    model_id = "amazon.titan-embed-text-v1"
    
    body = {
        "inputText": text
    }
    
    response = runtime_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )
    
    response_body = json.loads(response['body'].read())
    # Returns a list of floats (the vector)
    return response_body['embedding']

# ==============================================================================
# 6. IMAGE GENERATION
# ==============================================================================

def generate_image(runtime_client, prompt):
    """
    Generates an image using Titan Image Generator.
    
    Prerequisite:
    - Model Access: Enabled for "Titan Image Generator G1".
    
    Output:
    - Returns a Base64 encoded string of the image.
    - Must be decoded and saved as a binary file (e.g., .png).
    """
    model_id = "amazon.titan-image-generator-v1"
    
    body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": prompt
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "height": 512,
            "width": 512,
            "cfgScale": 8.0 # How strictly to follow the prompt
        }
    }
    
    response = runtime_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )
    
    response_body = json.loads(response['body'].read())
    base64_image = response_body['images'][0]
    
    # Save to file
    with open("generated_image.png", "wb") as f:
        f.write(base64.b64decode(base64_image))
    print("Image saved to generated_image.png")

# ==============================================================================
# 7. KNOWLEDGE BASES (RETRIEVE & GENERATE)
# ==============================================================================

def retrieve_from_kb(agent_runtime_client, query, kb_id):
    """
    Retrieves relevant text chunks from a managed Knowledge Base.
    
    Prerequisites:
    1.  **Knowledge Base**: Created in Bedrock Console (with Vector DB like OpenSearch Serverless).
    2.  **Data Source**: Documents indexed in the KB.
    3.  **KB ID**: The unique ID of your Knowledge Base.
    
    Args:
        kb_id (str): The Knowledge Base ID (e.g., 'ABC123XYZ').
        
    Returns:
        List of retrieval results containing text chunks and relevance scores.
    """
    response = agent_runtime_client.retrieve(
        knowledgeBaseId=kb_id,
        retrievalQuery={
            'text': query
        },
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 5, # Number of chunks to return (Default: 5)
                # 'overrideSearchType': 'HYBRID' | 'SEMANTIC' 
                # HYBRID: Combines keyword and semantic search (Recommended).
                # SEMANTIC: Pure vector similarity.
            }
        }
    )
    
    print(f"Retrieval Results for: '{query}'")
    for result in response['retrievalResults']:
        print(f"- {result['content']['text'][:100]}... (Score: {result['score']})")
    return response['retrievalResults']

def retrieve_and_generate(agent_runtime_client, query, kb_id, model_arn):
    """
    Performs RAG in a single API call: Retrieves context from KB and generates an answer.
    
    Prerequisites:
    1.  **Knowledge Base**: Created and populated.
    2.  **Model ARN**: The ARN of the foundation model to use for generation (e.g., Claude 3).
        - Format: arn:aws:bedrock:region::foundation-model/model-id
    
    Args:
        model_arn (str): Full ARN of the model (NOT just the modelId).
    
    Returns:
        The generated answer string.
    """
    response = agent_runtime_client.retrieve_and_generate(
        input={
            'text': query
        },
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': kb_id,
                'modelArn': model_arn,
                'retrievalConfiguration': {
                    'vectorSearchConfiguration': {
                        'numberOfResults': 5,
                        # 'overrideSearchType': 'HYBRID' | 'SEMANTIC'
                    }
                }
            }
        }
    )
    
    return response['output']['text']

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    try:
        # Initialize clients
        bedrock, bedrock_runtime, bedrock_agent_runtime = get_clients()
        
        # 1. List Models
        # list_models(bedrock)
        
        # 2. Text Generation
        print("--- Claude 3 ---")
        # print(invoke_claude_3(bedrock_runtime, "Explain quantum computing in one sentence."))
        
        # 3. Streaming
        print("\n--- Streaming Claude 3 ---")
        # invoke_with_stream(bedrock_runtime, "Write a haiku about coding.")
        
        # 4. Embeddings
        # emb = generate_embeddings(bedrock_runtime, "Hello World")
        # print(f"\nEmbedding length: {len(emb)}")
        
        # 7. Knowledge Bases (Replace with your actual IDs)
        # kb_id = "YOUR_KB_ID"
        # model_arn = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        
        # print("\n--- Retrieve ---")
        # retrieve_from_kb(bedrock_agent_runtime, "What is the company policy on remote work?", kb_id)
        
        # print("\n--- Retrieve & Generate ---")
        # answer = retrieve_and_generate(bedrock_agent_runtime, "Summarize remote work policy", kb_id, model_arn)
        # print(answer)
        
    except Exception as e:
        print(f"Error: {e}")
