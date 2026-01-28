import torch
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification
)
from typing import List, Dict, Any

from config.command_config import id2ner
from config.model_config import ModelConfig


class NERModel:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or ModelConfig.MODEL_PATH
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForTokenClassification.from_pretrained(
            self.model_path,
            num_labels=len(id2ner)
        )
        self.model.eval()
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        
        self.data_collator = DataCollatorForTokenClassification(self.tokenizer)
        
        print(f"Model loaded on {self.device}")
    
    def predict(self, text: str) -> List[Dict[str, str]]:
        words = text.split()
        
        tokenized = self.tokenizer(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )
        
        inputs = {
            'input_ids': tokenized['input_ids'].to(self.device),
            'attention_mask': tokenized['attention_mask'].to(self.device)
        }
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        predictions = torch.argmax(outputs.logits, dim=2)[0].tolist()
        word_ids = tokenized.word_ids()
        
        result = []
        current_word_id = None
        
        for i, word_id in enumerate(word_ids):
            if word_id is None:
                continue
            
            if word_id != current_word_id:
                current_word_id = word_id
                if word_id < len(words):
                    result.append({
                        "token": words[word_id],
                        "tag": id2ner[predictions[i]]
                    })
        
        return result
    
    def save_model(self, path: str = None):
        save_path = path or self.model_path
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        print(f"Model saved to {save_path}")