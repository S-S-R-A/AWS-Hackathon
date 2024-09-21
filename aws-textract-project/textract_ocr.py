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


# Initializes the Textract Client with the correct region
textract = boto3.client('textract', region_name='us-east-1')
s3 = boto3.client('s3')

# S3 Bucket and file
s3_bucket_name = 'w2-datasets'
document_name = 'dataset1/W2_XL_input_clean_1000.jpg'
s3_object_name = 'ML' + document_name

test = 'dataset1/W2_XL_input_clean_1000.jpg'


test_response = textract.analyze_document(
    Document={'S3Object': {'Bucket': s3_bucket_name, 'Name': document_name}},
    FeatureTypes=['FORMS', 'TABLES']
)

# Create a list to hold the word and bounding box data
output_data = generateMLJSON(test_response, document_name)

output_filepath = 'out/' + os.path.splitext(document_name)[0] + '.json'

# Write the list of dictionaries to a JSON file
with open(output_filepath, 'w') as file:
    json.dump(output_data, file, indent=4)

# Upload the JSON file to S3
s3.upload_file(output_filepath, s3_bucket_name, s3_object_name)


"""
cell_keys, cell_values, cell_blocks = genBlockMap(test_response['Blocks'])

cells_text = []
for block in test_response['Blocks']:
    cell_arr = []
    if (block['BlockType'] == 'CELL'):
        for relat in block.get('Relationships', []):
            for id in relat['Ids']:
                while cell_blocks[id]['BlockType'] != 'WORD' or cell_blocks[id]['BlockType'] != 'LINE':
                    cell_blocks[id].get('Relationships', [])
                cell_arr.append()
        cells_text.append(cell_arr)
print(cells_text)      

numTypes(test_response)

array = genMap(test_response)

# print(extract_key_value_pairs(test_response))

# print('\n\nTables')
# for block in test_response['Blocks']:
#     if (block['BlockType'] == 'TABLE'):
#         print(block)
# # print('\n\nCells')
# # for block in test_response['Blocks']:
# #     if (block['BlockType'] == 'CELL'):
# #         print(block)
# print('\n\nMerged_cell')
# for block in test_response['Blocks']:
#     if (block['BlockType'] == 'MERGED_CELL'):
#         print(block)

"""