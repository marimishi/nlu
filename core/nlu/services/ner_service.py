from typing import List, Dict
from core.nlu.models.ner_model import NERModel
from core.nlu.parsers.number_parser import number_parser


class NERService:
    def __init__(self, model_path: str = None):
        self.ner_model = None
        try:
            self.ner_model = NERModel(model_path)
        except Exception as e:
            print(f"Failed to load NER model: {e}")
    
    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        preprocessed_text = number_parser.convert_text_numbers_to_digits(text)
        
        print(f"Original text: {text}")
        print(f"Preprocessed text: {preprocessed_text}")
        
        if self.ner_model:
            predictions = self.ner_model.predict(preprocessed_text)
            
            predictions = self._post_process_predictions(predictions)
            
            return predictions
        else:
            return [{"token": word, "tag": "O"} for word in preprocessed_text.split()]
    
    def _post_process_predictions(self, predictions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        result = []
        i = 0
        
        while i < len(predictions):
            token = predictions[i]["token"]
            tag = predictions[i]["tag"]
            
            if '/' in token and i + 1 < len(predictions) and predictions[i + 1]["token"].isdigit():
                combined_token = token + predictions[i + 1]["token"]
                result.append({"token": combined_token, "tag": tag})
                i += 2
            else:
                result.append({"token": token, "tag": tag})
                i += 1
        
        return result
    
    def is_model_loaded(self) -> bool:
        return self.ner_model is not None