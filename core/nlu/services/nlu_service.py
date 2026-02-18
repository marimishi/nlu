from typing import Dict, Any

from core.nlu.services.ner_service import NERService
from core.nlu.parsers.entity_parser import EntityParser
from core.nlu.parsers.number_parser import number_parser
from core.command.processor import CommandProcessor


class NLUService:
    def __init__(self):
        self.ner_service = NERService()
        self.entity_parser = EntityParser()
        print(f"NLU Service initialized, NER model loaded: {self.ner_service.is_model_loaded()}")
    
    def process_text(self, text: str, processor: CommandProcessor) -> Dict[str, Any]:
        try:
            print(f"\n=== NLU Processing ===")
            print(f"Input text: {text}")
            
            preprocessed_text = number_parser.convert_text_numbers_to_digits(text)
            print(f"After number preprocessing: {preprocessed_text}")
            
            ner_results = self.ner_service.extract_entities(preprocessed_text)
            print(f"NER results: {ner_results}")
            
            # Дополнительная отладка для WELL_NAME
            well_name_tokens = [t for t in ner_results if "WELL_NAME" in t["tag"]]
            if well_name_tokens:
                print(f"WELL_NAME tokens found: {well_name_tokens}")
            
            result = processor.process_command(text, ner_results)
            
            # Проверяем финальный результат
            if result.get("parameters") and result["parameters"].get("wellName") == "года":
                print("WARNING: wellName is 'года' - likely incorrect!")
            
            return result
            
        except Exception as e:
            print(f"Error in NLU processing: {e}")
            result = processor.rule_based_processor(text)
            return result
    
    def extract_tokens(self, text: str) -> Dict[str, Any]:
        preprocessed_text = number_parser.convert_text_numbers_to_digits(text)
        ner_results = self.ner_service.extract_entities(preprocessed_text)
        
        simple_tokens = [
            {"token": word, "tag": "O"} 
            for word in text.split()
        ]
        
        return {
            "ner_tokens": ner_results,
            "simple_tokens": simple_tokens,
            "message": text,
            "word_count": len(text.split()),
            "method": "ner_model" if self.ner_service.is_model_loaded() else "simple_split"
        }
    
    @property
    def ner_model(self):
        return self.ner_service.ner_model