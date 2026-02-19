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
            
            # Добавляем семантический пост-процессинг
            predictions = self._semantic_post_processing(predictions, preprocessed_text)
            
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
    
    def _semantic_post_processing(self, predictions: List[Dict[str, str]], original_text: str) -> List[Dict[str, str]]:

        result = predictions.copy()
        
        year_indices = []
        well_name_indices = []
        
        for i, pred in enumerate(result):
            if pred["tag"] == "B-YEAR" or pred["tag"] == "I-YEAR":
                year_indices.append(i)
            if pred["tag"] == "B-WELL_NAME" or pred["tag"] == "I-WELL_NAME":
                well_name_indices.append(i)
        
        # Правило 1: Если после YEAR идет слово "года" с тегом WELL_NAME, исправляем его
        for year_idx in year_indices:
            if year_idx + 1 < len(result):
                next_token = result[year_idx + 1]
                next_token_lower = next_token["token"].lower()
                
                if next_token_lower in {"года", "год", "г."} and next_token["tag"] in {"B-WELL_NAME", "I-WELL_NAME"}:
                    print(f"Fixing: '{next_token['token']}' from {next_token['tag']} to O (after year)")
                    result[year_idx + 1]["tag"] = "O"
        
        # Правило 2: Если слово "пятого" (или другое числительное) идет после YEAR и имеет тег WELL_NAME, исправляем
        date_words = {"первого", "второго", "третьего", "четвертого", "пятого", 
                      "шестого", "седьмого", "восьмого", "девятого", "десятого",
                      "одиннадцатого", "двенадцатого", "двадцатого", "тридцатого"}
        
        for year_idx in year_indices:
            if year_idx + 1 < len(result):
                next_token = result[year_idx + 1]
                next_token_lower = next_token["token"].lower()
                
                if next_token_lower in date_words and next_token["tag"] in {"B-WELL_NAME", "I-WELL_NAME"}:
                    print(f"Fixing: '{next_token['token']}' from {next_token['tag']} to O (date word after year)")
                    result[year_idx + 1]["tag"] = "O"
        
        # Правило 3: Если слово "года" идет после WELL_NAME, но перед ним есть YEAR, исправляем
        for well_idx in well_name_indices:
            if well_idx > 0:
                prev_token = result[well_idx - 1]
                current_token = result[well_idx]
                current_token_lower = current_token["token"].lower()
                
                if current_token_lower in {"года", "год", "г."} and prev_token["tag"] in {"B-YEAR", "I-YEAR"}:
                    print(f"Fixing: '{current_token['token']}' from {current_token['tag']} to O (after year)")
                    result[well_idx]["tag"] = "O"
        
        # Правило 4: Если WELL_NAME содержит только слова, связанные с датами, исправляем
        date_related_words = date_words.union({"года", "год", "г.", "лет", "месяц", "месяца"})
        
        for i, pred in enumerate(result):
            if pred["tag"] in {"B-WELL_NAME", "I-WELL_NAME"}:
                token_lower = pred["token"].lower()
                if token_lower in date_related_words:
                    nearby_has_date = False
                    for j in range(max(0, i-3), min(len(result), i+4)):
                        if j != i and result[j]["tag"] in {"B-YEAR", "I-YEAR", "B-PERIOD", "I-PERIOD"}:
                            nearby_has_date = True
                            break
                    
                    if nearby_has_date:
                        print(f"Fixing: '{pred['token']}' from {pred['tag']} to O (date word in date context)")
                        result[i]["tag"] = "O"
        
        return result
    
    def is_model_loaded(self) -> bool:
        return self.ner_model is not None