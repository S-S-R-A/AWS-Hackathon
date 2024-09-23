import boto3
import sagemaker
from sagemaker import get_execution_role
import argparse
import json

# Parse command-line arguments
print("Parsing command-line arguments...")  
parser = argparse.ArgumentParser()
parser.add_argument('--region', type=str, default='us-east-1', help='AWS region')
args = parser.parse_args()

region_name = args.region
sagemaker_session = sagemaker.Session()
role = 'arn:aws:iam::715841371006:role/SageMakerExecutionRole'

# Find the latest training job
print("Finding the latest training job...")
client = boto3.client('sagemaker', region_name=region_name)
response = client.list_training_jobs(
    SortBy='CreationTime',
    SortOrder='Descending',
    MaxResults=1
)
training_job_name = response['TrainingJobSummaries'][0]['TrainingJobName']
print(f'Using training job: {training_job_name}')

# Attach to the estimator
print("Attaching to the estimator...")
bt_estimator = sagemaker.estimator.Estimator.attach(training_job_name)

# Deploy the model to an endpoint
print("Deploying the model to an endpoint...")
bt_predictor = bt_estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    serializer=sagemaker.serializers.JSONSerializer(),
    deserializer=sagemaker.deserializers.JSONDeserializer(),
)

# Save the endpoint name to a file for use in prediction
print("Saving the endpoint name to a file...")
endpoint_name = bt_predictor.endpoint_name
with open('endpoint_name.txt', 'w') as f:
    f.write(endpoint_name)


print(f'Model deployed at endpoint: {endpoint_name}')
