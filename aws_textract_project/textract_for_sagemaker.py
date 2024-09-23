# File: ./aws_textract_project/textract_for_sagemaker.py

import boto3
import json
import os
import tempfile
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS Configuration
S3_BUCKET = 'w2-datasets'
S3_REGION = 'us-east-1'  # Replace with your AWS region

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=S3_REGION)
textract_client = boto3.client('textract', region_name=S3_REGION)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_ml_json(textract_response, document_name):
    """
    Generates a simplified JSON from Textract response.
    
    :param textract_response: Textract API response
    :param document_name: Name of the processed document
    :return: Dictionary containing extracted words and their bounding boxes
    """
    output_data = []
    for block in textract_response['Blocks']:
        if block['BlockType'] == 'WORD':
            word_data = {
                'Text': block['Text'],
                'BoundingBox': {
                    'Left': block['Geometry']['BoundingBox']['Left'],
                    'Top': block['Geometry']['BoundingBox']['Top'],
                    'Width': block['Geometry']['BoundingBox']['Width'],
                    'Height': block['Geometry']['BoundingBox']['Height']
                }
            }
            output_data.append(word_data)
    final_output = {
        'DocumentName': document_name,
        'Words': output_data
    }
    return final_output

def process_textract(document_name):
    """
    Processes a document using Textract and uploads the OCR output to S3.

    :param document_name: Name of the document to process
    :return: Dictionary containing extracted words and their bounding boxes
    """
    logger.info(f"Starting Textract processing for document: {document_name}")

    # Define S3 keys
    s3_input_key = f'input/raw_file/{document_name}'
    s3_output_key = f'output/json/ML_{os.path.splitext(document_name)[0]}.json'

    # Call Textract to analyze the document
    try:
        response = textract_client.analyze_document(
            Document={'S3Object': {'Bucket': S3_BUCKET, 'Name': s3_input_key}},
            FeatureTypes=['FORMS', 'TABLES']
        )
        logger.info("Textract analysis completed.")
    except Exception as e:
        logger.error(f"Error during Textract analysis: {e}")
        raise e

    # Generate simplified OCR JSON
    ocr_json = generate_ml_json(response, document_name)

    # Save OCR JSON to a temporary file
    temp_dir = tempfile.gettempdir()
    ocr_filename = f'ML_{os.path.splitext(document_name)[0]}.json'
    ocr_filepath = os.path.join(temp_dir, ocr_filename)
    try:
        with open(ocr_filepath, 'w') as f:
            json.dump(ocr_json, f, indent=4)
        logger.info(f"OCR JSON saved to temporary file: {ocr_filepath}")
    except Exception as e:
        logger.error(f"Error saving OCR JSON: {e}")
        raise e

    # Upload OCR JSON to S3
    try:
        s3_client.upload_file(ocr_filepath, S3_BUCKET, s3_output_key)
        logger.info(f"OCR JSON uploaded to S3 at: {s3_output_key}")
    except Exception as e:
        logger.error(f"Error uploading OCR JSON to S3: {e}")
        raise e

    # Clean up temporary file
    try:
        os.remove(ocr_filepath)
        logger.info(f"Temporary OCR JSON file deleted: {ocr_filepath}")
    except Exception as e:
        logger.warning(f"Error deleting temporary file: {e}")

    return ocr_json
