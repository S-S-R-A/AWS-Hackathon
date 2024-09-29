from textract_ocr_better import get_kv_map, get_kv_relationship, text_kvs
from textract_ocr_line import get_line_ocr_data
from bedrock_chatbot import user_prompting_bedrock
from polly import get_polly_mp3_narration
from translate import translate_from_english, translate_to_english
from botocore.exceptions import NoCredentialsError, ClientError

import boto3
import os
import json

def download_single_file(bucket_name, prefix, local_dir, desired_filename):
    """
    Downloads a single file from a specified S3 prefix and saves it with a desired filename.

    :param bucket_name: Name of the S3 bucket.
    :param prefix: S3 prefix (folder path) to search for the file.
    :param local_dir: Local directory to save the downloaded file.
    :param desired_filename: The filename to save the downloaded file as.
    """
    s3 = boto3.client('s3')
    
    try:
        # List objects within the specified prefix
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        
        if 'Contents' in response and len(response['Contents']) > 0:
            # Iterate through the objects to find the first non-directory file
            for obj in response['Contents']:
                file_key = obj['Key']
                if not file_key.endswith('/'):
                    # Define the local path with the desired filename
                    local_path = os.path.join(local_dir, desired_filename)
                    
                    # Ensure the local directory exists
                    os.makedirs(local_dir, exist_ok=True)
                    
                    # Download the file
                    s3.download_file(bucket_name, file_key, local_path)
                    print(f"Downloaded {file_key} to {local_path}")
                    return  # Exit after downloading the first file
            else:
                print(f"No file found in {prefix} (only directories present).")
        else:
            print(f"No files found in {prefix}")
    except NoCredentialsError:
        print("Credentials not available. Please configure your AWS credentials.")
    except ClientError as e:
        print(f"Client error: {e}")

def clear_input_folder(s3_client, bucket, folder):
    """
    Deletes all objects within the specified folder in the S3 bucket.

    Args:
        s3_client (boto3.client): The Boto3 S3 client.
        bucket (str): The name of the S3 bucket.
        folder (str): The folder path within the bucket to clear (e.g., 'input/raw_file/').

    Returns:
        None
    """
    try:
        # List all objects within the specified folder
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=folder)

        # Check if the folder contains any objects
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                # Skip if the key is the folder itself
                if key.endswith('/'):
                    continue
                # Delete the object
                s3_client.delete_object(Bucket=bucket, Key=key)
                print(f"Deleted {key} from {bucket}/{folder}")
        else:
            print(f"No objects found in {bucket}/{folder} to delete.")

        print(f"Cleared input folder '{folder}' successfully.")

    except Exception as e:
        print(f"Error clearing input folder '{folder}': {e}")
        raise e
    
def main():
    s3 = boto3.client("s3")

    # get form type 
    s3_bucket_name_input_photo = 'w2-datasets'
    object_prefix_input_photo = 'input/raw_file'
    file_key = s3.list_objects_v2(Bucket=s3_bucket_name_input_photo, Prefix=object_prefix_input_photo)['Contents'][0]['Key']
    input_file_name = file_key[len(object_prefix_input_photo) + 1:]
    print(input_file_name)
    s3.download_file(s3_bucket_name_input_photo, file_key, input_file_name)

    # get form type 
    s3_bucket_name_sagemaker = 'w2-datasets'
    object_prefix_sagemaker = 'output/result/result.json'

    form_type_predicted = ''
    form_type_prediction_confidence = -1
    s3.download_file(s3_bucket_name_sagemaker, object_prefix_sagemaker, 'form_type.json')
    with open('form_type.json', 'r') as file:
        data = json.load(file)
        form_type_predicted = data.get("predicted_label")
        form_type_prediction_confidence = data.get("confidence")

    ocr_data_payload = ''
    if form_type_predicted == 'w2': 
        key_map, value_map, block_map = get_kv_map(input_file_name)

        # Get Key Value relationship
        kvs = get_kv_relationship(key_map, value_map, block_map)
        print("\n\n== FOUND KEY : VALUE pairs ===\n")
        # print_kvs(kvs)    
        ocr_data_payload = text_kvs(kvs)
    else:
        ocr_data_payload = get_line_ocr_data(input_file_name)

    # get user's question transcription and language
    s3_bucket_name_transcribe = 'polly-wav'
    object_prefix_transcribe = 'TranscriptionJob.json'
    
    folder_to_filename = {
    'input/audio/': 'TranscriptionJob.json',
    'input/lang/': 'language.json'
    }
    local_base_dir = './aws_textract_project/'

    user_question = ''
    user_language = 'en'

    response = s3.list_objects_v2(Bucket=s3_bucket_name_transcribe)

    for folder, desired_filename in folder_to_filename.items():
        # Define the local folder path (e.g., './local-directory/audio/' and './local-directory/lang/')
        local_folder = os.path.join(local_base_dir, folder.replace('input/', '').rstrip('/'))
        
        # Call the download function with the desired filename
        download_single_file(s3_bucket_name_transcribe, folder, local_folder, desired_filename)

    with open('TranscriptionJob.json', 'r') as file:
        data = json.load(file)
        user_question = data.get("results").get("transcripts")[0].get("transcript")
        print(user_question)
    object_prefix_language = 'language.json'
    with open('language.json', 'r') as file:
        data = json.load(file)
        user_language = data.get("LanguageCode")[:2]
        print(user_language)
    
        response = user_prompting_bedrock(translate_to_english(user_question, user_language), ocr_data_payload, form_type_predicted, form_type_prediction_confidence)
        response = translate_from_english(response, user_language)
        print(f"Output text: {response}")
        get_polly_mp3_narration(response, user_language)

    s3_bucket_name_output = 'w2-datasets'
    object_prefix_output = 'output/mp3/translated_output.mp3'
    s3.upload_file('translated_output.mp3', s3_bucket_name_output, object_prefix_output)
    

    try:
        clear_input_folder(s3, s3_bucket_name_transcribe, 'input/raw_file/')
        clear_input_folder(s3, s3_bucket_name_transcribe, 'input/audio/')
        clear_input_folder(s3, s3_bucket_name_transcribe, 'input/lang/')
        print("Cleared input folders after processing.")
    except Exception as e:
        print(f"Error clearing input folders: {e}")


    mp3_url = "https://{s3_bucket_name_output}.s3.amazonaws.com/{object_prefix_output}"
    return mp3_url

    # # Start searching a key value
    # while input('\n Do you want to search a value for a key? (enter "n" for exit) ') != 'n':
    #     search_key = input('\n Enter a search key:')
    #     print('The value is:', search_value(kvs, search_key))

    

if __name__ == "__main__":
    # file_name = '../WhatsApp Image 2024-09-16 at 16.36.51_27ca8f15.jpg'
    main()