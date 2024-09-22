import boto3
import sys
import re
import json
from collections import defaultdict


def get_kv_map(file_name):
    with open(file_name, 'rb') as file:
        img_test = file.read()
        bytes_test = bytearray(img_test)
        print('Image loaded', file_name)

    # process using image bytes
    textract = boto3.client('textract', region_name='us-east-1')
    
    response = textract.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['FORMS'])

    # Get the text blocks
    blocks = response['Blocks']

    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map


def get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key].append(val)
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '

    return text


def print_kvs(kvs):
    for key, value in kvs.items():
        print(key, ":", value)

def text_kvs(kvs):
    lines = ''
    for key, value in kvs.items():
        lines += f"{key} : {value}\n"
    return lines


def search_value(kvs, search_key):
    for key, value in kvs.items():
        if re.search(search_key, key, re.IGNORECASE):
            return value


def main(file_name):
    key_map, value_map, block_map = get_kv_map(file_name)

    # Get Key Value relationship
    kvs = get_kv_relationship(key_map, value_map, block_map)
    print("\n\n== FOUND KEY : VALUE pairs ===\n")
    # print_kvs(kvs)    

    model_id = 'mistral.mixtral-8x7b-instruct-v0:1'
    while True:
        user_prompting_bedrock(input('\n Ask a Question: '), model_id, kvs)

    # # Start searching a key value
    # while input('\n Do you want to search a value for a key? (enter "n" for exit) ') != 'n':
    #     search_key = input('\n Enter a search key:')
    #     print('The value is:', search_value(kvs, search_key))

def user_prompting_bedrock(user_question, model_id, kvs):
    response_body = generate_bedrock_response_text(model_id, kvs, user_question)
    print(f"Output text: {response_body['text']}")

def generate_bedrock_response_text(model_id, kvs, user_question):
    bedrock = boto3.client(service_name='bedrock-runtime')

    accept = "application/json"
    content_type = "application/json"

    prompt = 'Instructions: Be specific but casual in your answer. Answer only from the provided data exactly if the question is about the contents of the form. If the question is more contextual, you are allowed to base your answer off of your knowledge base (use your best judgement to determine if this is a form or context question). Do not make baseless assumptions. Ask yourself if your first response is the correct answer, with text and contextual evidence, and then only answer if it is correct (if it is not, rewrite your answer). It is better to admit you do not know something and reprompt the user than to make it up or falsely answer. In your response, be succinct and answer specifically what the user wants (ie do not give the employers name AND address when the user is just asking for the address). Cite where you sourced your answer from in the input file/text'
    prompt += 'data:\n' + text_kvs(kvs)
    prompt += '\n Answer this User Question: ' + user_question + 'And cite where you got it from in the text'

    conversation = [
        {
            "role": "user",
            "content": [{"text": prompt}],
        }
    ]

    response = bedrock.converse(
        modelId=model_id,
        messages=conversation,
        inferenceConfig={"maxTokens": 512, "temperature": 0.2, "topP": 0.9},
    )
    response_body = response["output"]["message"]["content"][0]

    return response_body


if __name__ == "__main__":
    file_name = '../W2_XL_input_clean_1000.jpg'
    main(file_name)
