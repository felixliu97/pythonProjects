import boto3  # Import the boto3 library for AWS services
import json  # Import the json library for working with JSON data
import time  # Import the time library for generating timestamps
from botocore.exceptions import ClientError  # Import the ClientError exception from botocore

def format_body(system_prompt, user_prompt):
    # Generate a random seed or use the current timestamp
    random_seed = int(time.time())

    # Format the prompt for the model with system instructions, seed, and user input
    formatted_prompt = f"""
    <|begin_of_text|>
        <|start_header_id|>system<|end_header_id|>
            {system_prompt}
            <|eot_id|>
        <|start_header_id|>seed<|end_header_id|>
        {random_seed}
        <|eot_id|>    
        <|start_header_id|>user<|end_header_id|>
            *Study Notes*: "{user_prompt}"
            <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
    """
    
    # Create a native request dictionary with the formatted prompt and generation parameters
    native_request = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": formatted_prompt
                    }
                ]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 512,
            "temperature": 0.8,
            "topP": 0.9
        }
    }
    
    # Convert the native request to JSON.
    body = json.dumps(native_request)
    
    return body

def invoke_bedrock(model_id, body):
    # Create a Bedrock Runtime client in the AWS Region of your choice.
    client = boto3.client("bedrock-runtime")
    try:
        # Invoke the model with the request.
        response = client.invoke_model(modelId=model_id, body=body)

    except (ClientError, Exception) as e:
        # Handle exceptions when invoking the model
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        exit(1)
    
    # Decode the response body from the model.
    model_response = json.loads(response["body"].read())
        
    return model_response

def lambda_handler(event, context):
    # Set the model ID, e.g., Nova Lite.
    model_id = "amazon.nova-lite-v1:0"

    # Get the study notes from the event payload
    user_prompt = event['notes']

    # Define the system prompt for the model
    system_prompt = """You are an AI that generates flash cards from study notes. When provided with *Study Notes*, you will produce an array of objects where each object represents a flash card. Each flash card object must have a "front" property containing the question and a "back" property containing the answer. The output should be an array with three flash card objects. Do not include anything else other than the array of flash cards. Your response should ONLY contain the array of objects in the following format:
[ {"front": "question here", "back": "answer here"},
{"front": "question here", "back": "answer here"},
{"front": "question here", "back": "answer here"} ]"""

    # Format the model-specific request body
    body = format_body(system_prompt, user_prompt)

    # Invoke the Bedrock model with the formatted request body
    response = invoke_bedrock(model_id, body)
    
    # Print the model's response
    print(response)
    
    # Tweak the formatting for the javascript application
    modresponse = response['output']['message']['content'][0]['text']
    finalresponse = {'generation': modresponse}
    # Return the response as the Lambda function's output
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',  # Allow cross-origin requests
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        'body': json.dumps(finalresponse)
    }
