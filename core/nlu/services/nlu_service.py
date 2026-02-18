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
            preprocessed_text = number_parser.convert_text_numbers_to_digits(text)
            ner_results = self.ner_service.extract_entities(preprocessed_text)
            return processor.process_command(text, ner_results)
        except Exception as e:
            print(f"Error in NLU processing: {e}")
            return processor.rule_based_processor(text)
    
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