from textract_ocr_better import get_kv_map, get_kv_relationship, text_kvs
from textract_ocr_line import get_line_ocr_data
from bedrock_chatbot import user_prompting_bedrock
from polly import get_polly_mp3_narration
from translate import translate_from_english, translate_to_english

import boto3
import json

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

    user_question = ''
    user_language = 'en'
    s3.download_file(s3_bucket_name_transcribe, object_prefix_transcribe, 'user_question_transcription.json')
    with open('user_question_transcription.json', 'r') as file:
        data = json.load(file)
        user_question = data.get("results").get("transcripts")[0].get("transcript")
        print(user_question)
    object_prefix_language = 'language.json'
    s3.download_file(s3_bucket_name_transcribe, object_prefix_language, 'user_language.json')
    with open('user_language.json', 'r') as file:
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
    
    mp3_url = f"https://{s3_bucket_name_output}.s3.amazonaws.com/{object_prefix_output}"
    return mp3_url

    # # Start searching a key value
    # while input('\n Do you want to search a value for a key? (enter "n" for exit) ') != 'n':
    #     search_key = input('\n Enter a search key:')
    #     print('The value is:', search_value(kvs, search_key))

if __name__ == "__main__":
    # file_name = '../WhatsApp Image 2024-09-16 at 16.36.51_27ca8f15.jpg'
    main()