import boto3

def get_line_ocr_data(input_file_name):
    with open(input_file_name, 'rb') as file:
        img_test = file.read()
        bytes_test = bytearray(img_test)
    textract = boto3.client('textract', region_name='us-east-1')
    response = textract.detect_document_text(Document={'Bytes': bytes_test})
    text = ''
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            text += block['Text']
    return text