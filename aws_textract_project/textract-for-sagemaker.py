# File: ./aws-textract-project/textract-for-sagemaker.py

from flask import Flask, request, jsonify
import boto3
import json
import os
import tempfile  # For cross-platform temporary directory
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# AWS Configuration
S3_BUCKET = 'w2-datasets'
S3_REGION = 'us-east-1'  # Your AWS region

# AWS Clients
s3_client = boto3.client('s3', region_name=S3_REGION)
textract_client = boto3.client('textract', region_name=S3_REGION)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Generate output JSON for ML
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

@app.route('/upload-and-process', methods=['POST'])
def upload_and_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file and allowed_file(file.filename):
        # Secure the filename
        filename = secure_filename(file.filename)

        # Use a temporary directory that's OS-independent
        temp_dir = tempfile.gettempdir()
        local_filepath = os.path.join(temp_dir, filename)
        file.save(local_filepath)

        # Upload the file to S3 input path
        s3_input_key = f'input/raw_file/{filename}'
        s3_client.upload_file(local_filepath, S3_BUCKET, s3_input_key)

        # Remove the local file
        os.remove(local_filepath)

        # Process the file from S3
        output_prefix = 'output/json'
        try:
            process_file(s3_input_key, S3_BUCKET, textract_client, s3_client, output_prefix)
        except Exception as e:
            app.logger.error(f"Error processing file: {str(e)}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

        # Return success response with file URL
        file_url = f'https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_input_key}'
        return jsonify({'message': 'File uploaded and processed successfully', 'file_url': file_url}), 200
    else:
        return jsonify({'error': 'Allowed file types are png, jpg, jpeg, pdf'}), 400

def process_file(document_name, s3_bucket_name, textract_client, s3_client, output_prefix):
    # Skip if the object is not an image or PDF
    if not document_name.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
        print(f"Skipping file: {document_name}")
        return

    print(f"Processing file: {document_name}")

    # Generate the base name and determine the output path
    base_name = os.path.splitext(os.path.basename(document_name))[0]
    s3_output_key = f'{output_prefix}/ML_{base_name}.json'

    # Call Textract to analyze the document
    test_response = textract_client.analyze_document(
        Document={'S3Object': {'Bucket': s3_bucket_name, 'Name': document_name}},
        FeatureTypes=['FORMS', 'TABLES']
    )

    # Generate the output data
    output_data = generateMLJSON(test_response, document_name)

    # Save output data to a JSON file in the temporary directory
    temp_dir = tempfile.gettempdir()
    output_filename = f'ML_{base_name}.json'
    output_filepath = os.path.join(temp_dir, output_filename)
    with open(output_filepath, 'w') as file:
        json.dump(output_data, file, indent=4)

    # Upload the JSON file to S3 output path
    s3_client.upload_file(output_filepath, s3_bucket_name, s3_output_key)

    # Delete the local JSON file
    try:
        os.remove(output_filepath)
    except OSError as e:
        print(f"Error deleting file {output_filepath}: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=8080)
