import boto3
import json
import argparse
import os
from sagemaker.predictor import Predictor
from sagemaker.serializers import JSONSerializer
from sagemaker.deserializers import JSONDeserializer

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--input-json', type=str, required=True, help='Path to the OCR JSON file')
parser.add_argument('--threshold', type=float, default=0.5, help='Confidence threshold for prediction')
args = parser.parse_args()

# Load endpoint name
with open('endpoint_name.txt', 'r') as f:
    endpoint_name = f.read().strip()

# Load label mapping
with open('label_mapping.json', 'r') as f:
    idx_to_label = json.load(f)

# Initialize predictor
predictor = Predictor(
    endpoint_name=endpoint_name,
    serializer=JSONSerializer(),
    deserializer=JSONDeserializer()
)

def predict_text(predictor, ocr_json, idx_to_label, threshold=0.5):
    # Extract text from OCR JSON
    words = ocr_json.get('Words', [])
    text = ' '.join([word['Text'] for word in words])
    payload = [text]  # BlazingText expects a list of texts
    
    # Make prediction
    response = predictor.predict(payload)
    predictions = response
    
    if predictions:
        labels = predictions[0].get('label', [])
        probabilities = predictions[0].get('prob', [])
        if labels and probabilities:
            # Get label with highest probability
            label_idx = int(labels[0].replace('__label__', ''))
            confidence = probabilities[0]
            if confidence >= threshold:
                predicted_label = idx_to_label[str(label_idx)]
                return predicted_label, confidence
    return None, None

# Read OCR JSON file
with open(args.input_json, 'r') as f:
    ocr_json = json.load(f)

# Predict form type
predicted_label, confidence = predict_text(
    predictor, ocr_json, idx_to_label, threshold=args.threshold
)

if predicted_label:
    print(f'Predicted label: {predicted_label}, Confidence: {confidence}')
else:
    print('The model could not determine the form type.')
