import json
import boto3
import os

region = os.environ['AWS_REGION']
s3=boto3.client('s3')
textract = boto3.client('textract', region_name=region)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('invoices')

# This is the function that is invoked every time a new object/file is uploaded to the S3 bucket
def lambda_handler(event, context):

    # When this function is invoked by S3 through the Event notification feature,
    # it sends a json with information related to the event, including the bucket name where
    # the event occurred and the object key that was uploaded.
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Calling Amazon Textract analyze_expense method
    # It returns one JSON with the extracted data from the image document
    # Check the docs to visualize the response format
    # https://docs.aws.amazon.com/textract/latest/dg/API_AnalyzeExpense.html
    response = textract.analyze_expense(Document={
        'S3Object': {
            'Bucket': bucket,
            'Name': key
        }
    })

    # Calling the function that parses the JSON to get only the information needed
    # The function returns one string with all the lines extracted from the image and one
    # object ready to be inserted into the DynamoDB table.
    invoice_data_lines = parse_invoice_data(response)
    
    data = invoice_data_lines[0]
    lines = invoice_data_lines[1]

    # Calling bedrock to get extra insights about the invoice.
    rock = enhance_with_bedrock(lines)
    data['llm_analysis'] = rock['output']['message']['content'][0]['text']

    # Inserting the final structured data into the DynamoDB table.
    insert_into_db(data)

    bucket_random_number = bucket.split('-')[-1]
    object_txt_key = key.split('.')[0]
    # Store it opened so if it is needed for any reason
    # it is not necessary to reprocess.
    s3.put_object(
        Bucket=f'lab-invoices-txt-{bucket_random_number}',
        Key=f'{object_txt_key}.txt',
        Body='\n'.join(lines)
    )

    return {
        'statusCode': 200,
        'body': json.dumps('Invoice successfully processed!')
    }

def parse_invoice_data(textract_response):
    # The final structure to be used to store into the database.
    invoice_data = {
        'invoice_id': None,
        'due_date': None,
        'receipt_date': None,
        'invoice_number': None,
        'total': None,
        'line_items': [],
        'llm_analysis': None
    }

    # Parsing the JSON returned by Amazon Textract analyze_expense method.
    expense_doc = textract_response['ExpenseDocuments'][0]
    for field in expense_doc['SummaryFields']:
        if field['Type']['Text'] == 'DUE_DATE':
            invoice_data['due_date'] = field['ValueDetection']['Text']
        if field['Type']['Text'] == 'INVOICE_RECEIPT_DATE':
            invoice_data['receipt_date'] = field['ValueDetection']['Text']
        if field['Type']['Text'] == 'INVOICE_RECEIPT_ID':
            invoice_data['invoice_number'] = field['ValueDetection']['Text']
            invoice_data['invoice_id'] = field['ValueDetection']['Text']
        if field['Type']['Text'] == 'TOTAL':
            invoice_data['total'] = field['ValueDetection']['Text']
    items = []
    items_prices = []
    for field in expense_doc['LineItemGroups']:
        for subfield in field['LineItems']:
            if subfield['LineItemExpenseFields']:
                for expense_field in subfield['LineItemExpenseFields']:
                    if expense_field['Type']['Text'] == 'ITEM':
                        items.append(expense_field['ValueDetection']['Text'])
                    if expense_field['Type']['Text'] == 'PRICE':
                        items_prices.append(expense_field['ValueDetection']['Text'])
    for item, price in zip(items, items_prices):
        invoice_data['line_items'].append({'item': item, 'price': price})
    lines = []
    for field in expense_doc['Blocks']:
        if field['BlockType'] == 'LINE':
            lines.append(field['Text'])
    return (invoice_data, lines)

def insert_into_db(data):
    try:
        response = table.put_item(Item=data)
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def enhance_with_bedrock(text_content):
    bedrock_runtime = boto3.client('bedrock-runtime')
    model_id='amazon.nova-lite-v1:0'

    prompt = f"""
    From the invoice text below, please try to check for any inconsistencies in the data and also if there are any unusual charges:
    
    Invoice text: {text_content}
    """
    
    body = json.dumps({
        "inferenceConfig": {
            "maxTokens": 1000,
            "temperature": 0.7,
            "topP": 0.9,
            "stopSequences": []
        },
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    })
    
    response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
    response_body = json.loads(response.get('body').read())
    return response_body
