from textract_ocr_better import get_kv_map, get_kv_relationship, text_kvs
from bedrock_chatbot import user_prompting_bedrock
from polly import get_polly_mp3_narration

def main(file_name):
    key_map, value_map, block_map = get_kv_map(file_name)

    # Get Key Value relationship
    kvs = get_kv_relationship(key_map, value_map, block_map)
    print("\n\n== FOUND KEY : VALUE pairs ===\n")
    # print_kvs(kvs)    

    while True:
        response = user_prompting_bedrock(input('\n Ask a Question: '), text_kvs(kvs))
        print(f"Output text: {response}")
        get_polly_mp3_narration(response)

    # # Start searching a key value
    # while input('\n Do you want to search a value for a key? (enter "n" for exit) ') != 'n':
    #     search_key = input('\n Enter a search key:')
    #     print('The value is:', search_value(kvs, search_key))

if __name__ == "__main__":
    file_name = '../W2_XL_input_clean_1000.jpg'
    main(file_name)