import boto3

translate = boto3.client('translate')


def translate_to_english(text, selected_language):
   
    if selected_language == "en":
        return text 
    response = translate.translate_text(
        Text=text,
        SourceLanguageCode=selected_language,
        TargetLanguageCode="en"
    )
    return response['TranslatedText']

def translate_from_english(text, selected_language):
    
    if selected_language == "en":
        return text 
    
    response = translate.translate_text(
        Text=text,
        SourceLanguageCode="en",
        TargetLanguageCode=selected_language
    )
    return response['TranslatedText']