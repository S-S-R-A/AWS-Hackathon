import boto3

# Uses the Minstral mistral.mixtral-8x7b-instruct-v0:1 model on AWS Bedrock to generate answers to prompts as a chatbot
# Prompts are engineered to be accurate to the text of the form, while still allowing for general-knowledge contextual searches

def user_prompting_bedrock(user_question, kvs_string, predicted_form_type, form_type_confidence) -> str:
    model_id = 'mistral.mixtral-8x7b-instruct-v0:1'
    response_body = generate_bedrock_response_text(model_id, kvs_string, user_question, predicted_form_type, form_type_confidence)
    return response_body['text']

def generate_bedrock_response_text(model_id, kvs_string, user_question, predicted_form_type, form_type_confidence):
    bedrock = boto3.client(service_name='bedrock-runtime')

    accept = "application/json"
    content_type = "application/json"

    prompt = 'Instructions: Be specific but casual in your answer. Answer only from the provided data exactly if the question is about the contents of the form. If the question is more contextual, you are allowed to base your answer off of your knowledge base (use your best judgement to determine if this is a form or context question). Do not make baseless assumptions. Ask yourself if your first response is the correct answer, with text and contextual evidence, and then only answer if it is correct (if it is not, rewrite your answer). It is better to admit you do not know something and reprompt the user than to make it up or falsely answer. In your response, be succinct and answer specifically what the user wants (ie do not give the employers name AND address when the user is just asking for the address). Cite where you sourced your answer from in the input file/text'
    prompt = f"The form type is predicted to be {predicted_form_type} with a confidence of {form_type_confidence}" + "\n"
    prompt += 'data:\n' + kvs_string
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