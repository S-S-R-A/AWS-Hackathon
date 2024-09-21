import boto3
import json
import os

# Prints number of each block type that occurs in each test_response
def numTypes(test_response):
    block_type_counts = {}

    # Iterate through the blocks and count occurrences of each block type
    for block in test_response['Blocks']:
        block_type = block['BlockType']
        if block_type in block_type_counts:
            block_type_counts[block_type] += 1
        else:
            block_type_counts[block_type] = 1

    # Print the counts of each unique block type
    print("Block Type Counts:")
    for block_type, count in block_type_counts.items():
        print(f"{block_type}: {count}")

# Generates a map of all Key Value pairs from all KEY_VALUE_SET block types
def genMap(test_response):
    array = []
    for block in test_response['Blocks']:
        if block['BlockType'] == 'KEY_VALUE_SET': 
            key_value = {}   
            for relationship in block.get('Relationships', []):
                if relationship['Type'] == 'VALUE':
                    key_value['VALUE'] = relationship['Ids']
                elif relationship['Type'] == 'CHILD':
                    key_value['CHILD'] = relationship['Ids']
                array.append(key_value)
    return array

# Generate a hash map that can be used to retrieve any block given an id
def genBlockMap(blocks):
    key_map = {}
    value_map = {}
    block_map = {}

    # Create a map of blocks using block IDs
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        
        # Store KEY and VALUE blocks in separate dictionaries
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            elif 'VALUE' in block['EntityTypes']:
                value_map[block_id] = block
    return key_map, value_map, block_map
    

def get_text_for_block(block, block_map):
    text = ""
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = block_map[child_id]
                    if child_block['BlockType'] == 'WORD':
                        text += child_block['Text'] + " "
    return text.strip()

def extract_key_value_pairs(test_response):
    blocks = test_response['Blocks']
    
    key_map, value_map, block_map = genBlockMap(blocks)

    key_value_pairs = {}
    
    # Extract key-value pairs
    for key_block in key_map.values():
        key_text = get_text_for_block(key_block, block_map)
        
        # Find the VALUE block related to the KEY block
        if 'Relationships' in key_block:
            for relationship in key_block['Relationships']:
                if relationship['Type'] == 'VALUE':
                    for value_id in relationship['Ids']:
                        value_block = value_map[value_id]
                        value_text = get_text_for_block(value_block, block_map)
                        key_value_pairs[key_text] = value_text
    return key_value_pairs

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

def list_all_objects(s3_client, bucket_name):
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket_name)
    all_objects = []
    for page in page_iterator:
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
    return all_objects

def process_file(document_name, s3_bucket_name, textract_client, s3_client):
    # Skip if the object is a directory (ends with '/')
    if document_name.endswith('/'):
        return

    # Skip if the object is not an image (adjust extensions as needed)
    if not document_name.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
        return

    print(f"Processing file: {document_name}")

    # Generate the s3_object_name and output_filepath
    base_name = os.path.splitext(os.path.basename(document_name))[0]
    s3_object_name = f'output/ML{base_name}.json'
    output_filepath = f'aws-textract-project/out/ML{base_name}.json'

    # Call Textract to analyze the document
    test_response = textract_client.analyze_document(
        Document={'S3Object': {'Bucket': s3_bucket_name, 'Name': document_name}},
        FeatureTypes=['FORMS', 'TABLES']
    )

    # Abhi does cell stuff here
    # cell_keys, cell_values, cell_blocks = genBlockMap(test_response['Blocks'])

    # cells_text = []
    # for block in test_response['Blocks']:
    #     if (block['BlockType'] == 'CELL'):
    #         cell_arr = []
    #         for relat in block.get('Relationships', []):
    #             for id in relat['Ids']:
    #                 id_string = id
    #                 found = True
    #                 while found and (cell_blocks[id_string]['BlockType'] != 'WORD' and cell_blocks[id_string]['BlockType'] != 'LINE'):
    #                     print(cell_blocks[id_string]['BlockType'])
    #                     inside_relats = cell_blocks[id_string].get('Relationships', [])
    #                     if (len(inside_relats) > 0):
    #                         id_string = inside_relats[0]['Ids'][0]
    #                     else:
    #                         found = False
    #                         break
    #                 if found: 
    #                     cell_arr.append(cell_blocks[id]['Text'])
    #         cells_text.append(cell_arr)
    # print(cells_text)    

    # Now Abhi does query stuff for W-2
    















































    # # Generate the output data
    # output_data = generateMLJSON(test_response, document_name)

    # # Ensure the output directory exists
    # os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    # # Write the output data to a JSON file
    # with open(output_filepath, 'w') as file:
    #     json.dump(output_data, file, indent=4)

    # # Upload the JSON file back to S3
    # s3_client.upload_file(output_filepath, s3_bucket_name, s3_object_name)

    # # Delete the local JSON file to save space
    # try:
    #     os.remove(output_filepath)
    # except OSError as e:
    #     print(f"Error deleting file {output_filepath}: {e}")

def main():
    # Initialize the Textract and S3 clients
    textract = boto3.client('textract', region_name='us-east-1')
    s3 = boto3.client('s3')

    # S3 Bucket
    s3_bucket_name = 'w2-datasets'

    # Specify the document name if processing a single file
    # Set to None to process all files in the bucket
    document_name = 'dataset1/W2_XL_input_clean_1000.pdf'
    # document_name = None  # Replace with 'your-file-path.jpg' to process a single file

    if document_name:
        # Process a single file
        process_file(document_name, s3_bucket_name, textract, s3)
    else:
        # List all objects in the bucket
        all_objects = list_all_objects(s3, s3_bucket_name)

        # Process each object
        for obj in all_objects:
            document_name = obj['Key']
            process_file(document_name, s3_bucket_name, textract, s3)

if __name__ == "__main__":
    main()
  

# numTypes(test_response)

# array = genMap(test_response)

# # print(extract_key_value_pairs(test_response))

# # print('\n\nTables')
# # for block in test_response['Blocks']:
# #     if (block['BlockType'] == 'TABLE'):
# #         print(block)
# # # print('\n\nCells')
# # # for block in test_response['Blocks']:
# # #     if (block['BlockType'] == 'CELL'):
# # #         print(block)
# # print('\n\nMerged_cell')
# # for block in test_response['Blocks']:
# #     if (block['BlockType'] == 'MERGED_CELL'):
# #         print(block)

