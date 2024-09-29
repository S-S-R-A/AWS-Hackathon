# File: ./aws_sagemaker/predict.py

import boto3
import json
import argparse
import os
import logging
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load endpoint name
ENDPOINT_NAME_FILE = 'endpoint_name.txt'
if not os.path.exists(ENDPOINT_NAME_FILE):
    logger.error(f"Endpoint name file '{ENDPOINT_NAME_FILE}' not found.")
    exit(1)
with open(ENDPOINT_NAME_FILE, 'r') as f:
    endpoint_name = f.read().strip()

# Load label mapping
LABEL_MAPPING_FILE = 'label_mapping.json'
if not os.path.exists(LABEL_MAPPING_FILE):
    logger.error(f"Label mapping file '{LABEL_MAPPING_FILE}' not found.")
    exit(1)
with open(LABEL_MAPPING_FILE, 'r') as f:
    idx_to_label = json.load(f)
    # Convert keys to integers
    idx_to_label = {int(k): v for k, v in idx_to_label.items()}
# Initialize predictor with JSONSerializer
try:
    predictor = Predictor(
        endpoint_name=endpoint_name,
        serializer=JSONSerializer(),        # Send payload as JSON
        deserializer=JSONDeserializer()     # Receive response as JSON
    )
    logger.info(f"SageMaker Predictor initialized for endpoint '{endpoint_name}'.")
except Exception as e:
    logger.error(f"Failed to initialize Predictor: {e}")
    exit(1)

def predict_text(predictor, ocr_json, idx_to_label, threshold=0.5):
  
    if not predictor:
        logger.error("Predictor is not initialized.")
        return None, None

    # Extract text from OCR JSON
    words = ocr_json.get('Words', [])
    text = ' '.join([word['Text'] for word in words])

    if not text.strip():
        logger.warning("No text extracted from OCR JSON.")
        return None, None

    # Prepare payload
    payload = {"instances": [text]}

    # Send JSON payload to SageMaker
    try:
        response = predictor.predict(payload)
        logger.info(f"SageMaker response: {response}")

        if response and isinstance(response, list):
            prediction_result = response[0]
            labels = prediction_result.get('label', [])
            probabilities = prediction_result.get('prob', [])
            logger.info(f"Labels: {labels}, Probabilities: {probabilities}")

            if labels and probabilities:
                label_idx_str = labels[0].replace('__label__', '')
                try:
                    label_idx = int(label_idx_str)
                    confidence = probabilities[0]
                    predicted_label = idx_to_label.get(label_idx, "Unknown")
                    logger.info(f"Predicted Label: {predicted_label}, Confidence: {confidence}")
                    return predicted_label, confidence
                except ValueError:
                    logger.error(f"Invalid label format: {labels[0]}")
                    return None, None
        else:
            logger.error("Invalid response format from SageMaker.")
            return None, None

    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        return None, None

    return None, None


def get_sagemaker_prediction(data, threshold=0.05):
    """
    Wrapper function to get prediction from SageMaker.

    :param data: Dictionary containing OCR data
    :param threshold: Confidence threshold
    :return: Predicted label and confidence
    """
    ocr_json = data
    return predict_text(predictor, ocr_json, idx_to_label, threshold)

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Predict document type using SageMaker.")
    parser.add_argument('--input-json', type=str, required=True, help='Path to the OCR JSON file')
    parser.add_argument('--threshold', type=float, default=0.5, help='Confidence threshold for prediction')
    args = parser.parse_args()

    # Read OCR JSON file
    input_json_path = args.input_json
    if not os.path.exists(input_json_path):
        logger.error(f"OCR JSON file '{input_json_path}' not found.")
        exit(1)
    with open(input_json_path, 'r') as f:
        ocr_json = json.load(f)

    # Predict form type
    predicted_label, confidence = predict_text(
        predictor, ocr_json, idx_to_label, threshold=args.threshold
    )

    if predicted_label:
        print(f'Predicted label: {predicted_label}, Confidence: {confidence}')
    else:
        print('The model could not determine the form type.')