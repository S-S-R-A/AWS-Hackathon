import sys
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import boto3
from aws_textract_project.textract_for_sagemaker import process_textract, allowed_file
from werkzeug.utils import secure_filename
from aws_sagemaker.predict import get_sagemaker_prediction

app = Flask(__name__)
CORS(app)

# AWS Configuration
S3_BUCKET = 'w2-datasets'
S3_REGION = 'us-east-1'  # Replace with your AWS region

# Initialize AWS S3 client
s3_client = boto3.client('s3', region_name=S3_REGION)

def upload_file_to_s3(file, filename):
    try:
        s3_client.upload_fileobj(file, S3_BUCKET, f'input/raw_file/{filename}')
        # Generate a pre-signed URL valid for 1 hour
        file_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': f'input/raw_file/{filename}'},
            ExpiresIn=3600  # URL valid for 1 hour
        )
        return file_url
    except Exception as e:
        app.logger.error(f"Failed to upload file to S3: {e}")
        raise e

def get_prediction_result_from_s3(result_filename):
    try:
        # Download the result file from S3
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_result_file:
            s3_client.download_fileobj(
                S3_BUCKET,
                f'output/result/{result_filename}',
                temp_result_file
            )
            temp_result_file_path = temp_result_file.name

        # Read the JSON data from the temporary file
        with open(temp_result_file_path, 'r') as f:
            result_data = json.load(f)

        # Clean up the temporary file
        os.remove(temp_result_file_path)

        return result_data

    except Exception as e:
        app.logger.error(f"Failed to read prediction result from S3: {e}")
        return None

def clear_input_folder():
    try:
        # List all objects in the 'input/raw_file/' folder
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix='input/raw_file/')
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # Delete each object
                s3_client.delete_object(Bucket=S3_BUCKET, Key=obj['Key'])
        app.logger.info("Input folder cleared successfully.")
    except Exception as e:
        app.logger.error(f"Failed to clear input folder: {e}")
        raise e

@app.route('/upload-and-process', methods=['POST'])
def upload_and_process():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    filename = secure_filename(file.filename)

    try:
        # Clear the input folder in the S3 bucket before uploading a new file
        clear_input_folder()

        # Upload the file to S3
        file_url = upload_file_to_s3(file, filename)

        # Process the file with Textract
        textract_output = process_textract(filename)  # Assumes filename is the key in S3

        # Get SageMaker prediction
        prediction, confidence = get_sagemaker_prediction(textract_output)

        # Save the prediction result to S3
        result_data = {
            "file_url": file_url,
            "predicted_label": prediction if prediction else "Unknown",
            "confidence": confidence if confidence else 0
        }

        # Use a fixed result filename
        result_filename = "result.json"

        # Save the result data to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_result_file:
            json.dump(result_data, temp_result_file)
            temp_result_file_path = temp_result_file.name

        # Upload the result file to S3 under 'output/result/'
        s3_client.upload_file(
            temp_result_file_path,
            S3_BUCKET,
            f'output/result/{result_filename}'
        )

        # Clean up the temporary file
        os.remove(temp_result_file_path)

        # Generate a pre-signed URL for the result file
        result_file_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': f'output/result/{result_filename}'},
            ExpiresIn=3600  # URL valid for 1 hour
        )

        return jsonify({
            "file_url": file_url,
            "result_file_url": result_file_url,
            "predicted_label": prediction if prediction else "Unknown",
            "confidence": confidence if confidence else 0
        }), 200

    except Exception as e:
        app.logger.error(f"Error in upload_and_process: {e}")
        return jsonify({"error": str(e)}), 500

# Existing endpoints
@app.route('/process-textract', methods=['POST'])
def process_textract_endpoint():
    data = request.json
    document_name = data.get('document_name')

    try:
        textract_output = process_textract(document_name)
        return jsonify({"textract_output": textract_output}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-prediction', methods=['POST'])
def get_prediction_endpoint():
    data = request.json
    try:
        prediction = get_sagemaker_prediction(data)
        return jsonify({"prediction": prediction}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-prediction-result', methods=['GET'])
def get_prediction_result():
    # Since the result filename is fixed, you can optionally remove the query parameter
    result_filename = request.args.get('result_filename', 'result.json')

    result_data = get_prediction_result_from_s3(result_filename)
    if result_data:
        return jsonify(result_data), 200
    else:
        return jsonify({"error": "Failed to retrieve prediction result"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
