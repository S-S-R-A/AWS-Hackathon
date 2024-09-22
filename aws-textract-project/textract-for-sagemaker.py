from flask import Flask, request, jsonify
import boto3
import json
import os

app = Flask(__name__)

# Generate a hash map that can be used to retrieve any block given an id
def genBlockMap(blocks):
    key_map = {}
    value_map = {}
    block_map = {}

    # Create a map of blocks using block IDs
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        
        # Store KEY and VALUE blocks in separate dictionaries
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            elif 'VALUE' in block['EntityTypes']:
                value_map[block_id] = block
    return key_map, value_map, block_map
    

def get_text_for_block(block, block_map):
    text = ""
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = block_map[child_id]
                    if child_block['BlockType'] == 'WORD':
                        text += child_block['Text'] + " "
    return text.strip()

def generateMLJSON(test_response, document_name):
    # Loop through the blocks in the test_response
    output_data = []
    for block in test_response['Blocks']:
        if block['BlockType'] == 'WORD':
            # Create a dictionary with word text and its bounding box details
            word_data = {
                'Text': block['Text'],
                'BoundingBox': {
                    'Left': block['Geometry']['BoundingBox']['Left'],
                    'Top': block['Geometry']['BoundingBox']['Top'],
                    'Width': block['Geometry']['BoundingBox']['Width'],
                    'Height': block['Geometry']['BoundingBox']['Height']
                }
            }
            # Add this dictionary to the list
            output_data.append(word_data)
    final_output = {
        'DocumentName': document_name,
        'Words': output_data
    }
    return final_output

def list_all_objects(s3_client, bucket_name, prefix=''):
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    all_objects = []
    for page in page_iterator:
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
    return all_objects

def process_file(document_name, s3_bucket_name, textract_client, s3_client, output_prefix):
    # Skip if the object is a directory (ends with '/')
    if document_name.endswith('/'):
        print(f"Skipping file: {document_name}")
        return

    # Skip if the object is not an image or PDF (adjust extensions as needed)
    if not document_name.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
        print(f"Skipping file: {document_name}")
        return

    print(f"Processing file: {document_name}")

    # Generate the base name and determine the output path
    base_name = os.path.splitext(os.path.basename(document_name))[0]
    s3_object_name = f'{output_prefix}/ML{base_name}.json'

    # Generate the local output filepath
    output_filepath = f'aws-textract-project/out/ML{base_name}.json'

    # Call Textract to analyze the document
    test_response = textract_client.analyze_document(
        Document={'S3Object': {'Bucket': s3_bucket_name, 'Name': document_name}},
        FeatureTypes=['FORMS', 'TABLES']
    )

    # Generate the output data
    output_data = generateMLJSON(test_response, document_name)

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    # Write the output data to a JSON file
    with open(output_filepath, 'w') as file:
        json.dump(output_data, file, indent=4)

    # Upload the JSON file back to S3
    s3_client.upload_file(output_filepath, s3_bucket_name, s3_object_name)

    # Delete the local JSON file to save space
    try:
        os.remove(output_filepath)
    except OSError as e:
        print(f"Error deleting file {output_filepath}: {e}")

def process_directory(s3_bucket_name, textract_client, s3_client, max_files=100):
    # List all directories in the datasets folder
    # datasets = [
    #     'datasets/1040_1', 'datasets/1040_2', 'datasets/2106_1', 'datasets/2106_2', 
    #     'datasets/2441', 'datasets/4562_1', 'datasets/4562_2', 'datasets/6251',
    #     'datasets/sch_a', 'datasets/sch_b', 'datasets/sch_c_1', 'datasets/sch_c_2',
    #     'datasets/sch_d_1', 'datasets/sch_d_2', 'datasets/sch_e_1', 'datasets/sch_e_2',
    #     'datasets/sch_f_1', 'datasets/sch_f_2', 'datasets/sch_se_1', 'datasets/sch_se_2'
    # ]


    datasets = ['datasets/sch_d_2', 'datasets/sch_e_1', 'datasets/sch_e_2',
        'datasets/sch_f_1', 'datasets/sch_f_2', 'datasets/sch_se_1', 'datasets/sch_se_2'
    ]
    for dataset in datasets:
        original_folder = f'{dataset}/original/'
        ocr_output_folder = f'{dataset}/ocr_output/'

        print(f"Processing documents in {original_folder}...")

        # List all objects in the original folder
        all_objects = list_all_objects(s3_client, s3_bucket_name, prefix=original_folder)

        # Process only up to the maximum number of files (100)
        processed_count = 0
        for obj in all_objects:
            if processed_count >= max_files:
                print(f"Reached limit of {max_files} files for {original_folder}.")
                break
            document_name = obj['Key']
            process_file(document_name, s3_bucket_name, textract_client, s3_client, ocr_output_folder)
            processed_count += 1

@app.route('/process-file', methods=['POST'])
def process_file_endpoint():
    data = request.json
    document_name = data.get('document_name')
    s3_bucket_name = 'w2-datasets'

    textract = boto3.client('textract', region_name='us-east-1')
    s3 = boto3.client('s3')

    output_prefix = 'output/json'
    
    try:
        process_file(document_name, s3_bucket_name, textract, s3, output_prefix)
        return jsonify({"message": "File processed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


"""
const processFile = async () => {
    const response = await fetch('/process-file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            document_name: 'input/raw_file/some-file.pdf'
        })
    });
    const data = await response.json();
    console.log(data.message);
}
"""
