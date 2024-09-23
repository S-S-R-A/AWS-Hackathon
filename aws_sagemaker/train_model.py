import boto3
import sagemaker
import json
import os
from sagemaker import get_execution_role
from sklearn.model_selection import train_test_split
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--bucket-name', type=str, required=True, help='S3 bucket name containing the datasets')
parser.add_argument('--prefix', type=str, default='datasets', help='Prefix for your datasets in S3')
args = parser.parse_args()

# Initialize SageMaker session and role
sagemaker_session = sagemaker.Session()
role = 'arn:aws:iam::715841371006:role/SageMakerExecutionRole'

bucket_name = args.bucket_name
prefix = args.prefix
# Initialize S3 resource
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)

# Collect dataset names
dataset_names = ['1040_1', '1040_2', '2106_1', '2106_2', 
         '2441', '4562_1', '4562_2', '6251',
         'sch_a', 'sch_b', 'sch_c_1', 'sch_c_2',
         'sch_d_1']

# for obj in bucket.objects.filter(Prefix=f'{prefix}/'):
#     parts = obj.key.split('/')
#     if len(parts) > 2 and parts[0] == 'datasets':
#         dataset_name = parts[1]
#         if dataset_name not in dataset_names:
#             dataset_names.append(dataset_name)

print("Datasets found:", dataset_names)

# Local directory to store data
local_data_dir = 'data'
os.makedirs(local_data_dir, exist_ok=True)

texts = []
labels = []

download_all = False  # Set this to False since you don't want to download again
print("Checking OCR output files...")

for dataset_name in dataset_names:
    ocr_output_prefix = f'{prefix}/{dataset_name}/ocr_output/'
    for obj in bucket.objects.filter(Prefix=ocr_output_prefix):
        if obj.key.endswith('.json'):
            local_file_path = os.path.join(local_data_dir, os.path.basename(obj.key))
            
            # Check if the file already exists locally
            if os.path.exists(local_file_path):
                print(f"File already exists, skipping download: {local_file_path}")
            else:
                print(f"Downloading: {obj.key}")
                bucket.download_file(obj.key, local_file_path)
                
            # Read the JSON file (whether it was downloaded or already exists)
            print(f"Reading: {local_file_path}")
            with open(local_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                words = data.get('Words', [])
                # Combine words into a single string
                text = ' '.join([word['Text'] for word in words])
                texts.append(text)
                labels.append(dataset_name)


print("Number of documents:", len(texts))
# Create label encoding
label_set = sorted(set(labels))
label_to_idx = {label: idx for idx, label in enumerate(label_set)}
idx_to_label = {idx: label for label, idx in label_to_idx.items()}

print("Label mapping:", label_to_idx)
# Save label mapping for later use
with open('label_mapping.json', 'w') as f:
    json.dump(idx_to_label, f)

print("Converting labels to indices...")
# Convert labels to indices
label_indices = [label_to_idx[label] for label in labels]
print("Label indices:", label_indices)

print("Splitting data into training and validation sets...")
# Split Data into Training and Validation Sets
X_train, X_val, y_train, y_val = train_test_split(
    texts, label_indices, test_size=0.2, random_state=42
)

print("Training samples:", len(X_train))
# Prepare Data for BlazingText
print("Preparing data for BlazingText...")
def prepare_blazingtext_data(texts, labels):
    data = []
    for text, label in zip(texts, labels):
        label_str = f'__label__{label}'
        data.append(f'{label_str} {text}')
    return data

train_data = prepare_blazingtext_data(X_train, y_train)
val_data = prepare_blazingtext_data(X_val, y_val)

print("Training data sample:", train_data[0])
# Save and Upload Data to S3
# Save data locally
print("Saving data locally...")
train_data_file = os.path.join(local_data_dir, 'train.txt')
val_data_file = os.path.join(local_data_dir, 'validation.txt')

print("Saving training data...")
with open(train_data_file, 'w', encoding='utf-8') as f:  # Specify UTF-8 encoding
    for line in train_data:
        f.write(f'{line}\n')

with open(val_data_file, 'w', encoding='utf-8') as f:  # Specify UTF-8 encoding
    for line in val_data:
        f.write(f'{line}\n')

print("Data saved successfully.")

print("Uploading data to S3...")
# Upload data to S3
s3_train_prefix = 'blazingtext_data/train'
s3_val_prefix = 'blazingtext_data/validation'

s3_train_path = sagemaker_session.upload_data(
    path=train_data_file, bucket=bucket_name, key_prefix=s3_train_prefix
)
s3_val_path = sagemaker_session.upload_data(
    path=val_data_file, bucket=bucket_name, key_prefix=s3_val_prefix
)

print("Training data uploaded to:", s3_train_path)
# Set Up the BlazingText Estimator
from sagemaker import image_uris

region_name = boto3.Session().region_name
container = image_uris.retrieve('blazingtext', region_name)

print("Using container:", container)
print("Setting up estimator...")
bt_estimator = sagemaker.estimator.Estimator(
    image_uri=container,
    role=role,
    instance_count=1,
    instance_type='ml.m5.large',
    volume_size=5,
    max_run=360000,
    input_mode='File',
    output_path=f's3://{bucket_name}/blazingtext_output',
    sagemaker_session=sagemaker_session
)

print("Setting hyperparameters...")
bt_estimator.set_hyperparameters(
    mode='supervised',
    epochs=5,
    min_count=2,
    learning_rate=0.05,
    vector_dim=100,
    early_stopping=True,
    patience=4,
    min_epochs=5,
    word_ngrams=2
)

print("Data Channels:", s3_train_path, s3_val_path)
# Define Data Channels and Start Training
train_data_channel = sagemaker.inputs.TrainingInput(
    s3_train_path, distribution='FullyReplicated', content_type='text/plain'
)
val_data_channel = sagemaker.inputs.TrainingInput(
    s3_val_path, distribution='FullyReplicated', content_type='text/plain'
)
print("Data Channels:", train_data_channel, val_data_channel)
data_channels = {'train': train_data_channel, 'validation': val_data_channel}

print("Starting training job...")
# Start the training job
bt_estimator.fit(inputs=data_channels)
