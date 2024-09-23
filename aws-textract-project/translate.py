import boto3

translate = boto3.client('translate')


def translate_to_english(text, source_language):
   
    if source_language == "en":
        return text 
    response = translate.translate_text(
        Text=text,
        SourceLanguageCode=source_language,
        TargetLanguageCode="en"
    )
    return response['TranslatedText']

def translate_from_english(text, target_language):
    
    if target_language == "en":
        return text 
    response = translate.translate_text(
        Text=text,
        SourceLanguageCode="en",
        TargetLanguageCode=target_language
    )
    return response['TranslatedText']