from typing import Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NLUCommand:
    connection_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=lambda: {
        "wellId": "",
        "wellField": "",
        "wellName": "",
        "period": {
            "start": "",
            "end": ""
        },
        "moduleName": "",
        "moduleID": ""
    })
    command: str = "UNKNOWN"
    debug_info: Dict[str, Any] = field(default_factory=lambda: {
        "raw_tokens": [],
        "entities_found": [],
        "text_processed": "",
        "method": "",
        "timestamp": ""
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "connectionId": self.connection_id,
            "parameters": self.parameters,
            "command": self.command,
            "debug": self.debug_info
        }
    
    @classmethod
    def create_from_analysis(cls, text: str, entities: Dict[str, Any], 
                           method: str = "ner") -> 'NLUCommand':
        command = cls()
        command.debug_info["text_processed"] = text
        command.debug_info["method"] = method
        command.debug_info["timestamp"] = datetime.now().isoformat()
        
        return command