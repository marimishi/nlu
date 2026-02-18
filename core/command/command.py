from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NLUCommand:
    connection_id: str = ""
    parameters: Optional[Dict[str, Any]] = None
    command: str = "UNKNOWN"
    module_name: str = ""
    module_id: str = ""
    module_title: str = ""
    debug_info: Dict[str, Any] = field(default_factory=lambda: {
        "raw_tokens": [],
        "entities_found": [],
        "text_processed": "",
        "method": "",
        "timestamp": ""
    })

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "connectionId": self.connection_id,
            "command": self.command,
            "moduleName": self.module_name,
            "moduleId": self.module_id,
            "moduleTitle": self.module_title,
            "debug": self.debug_info
        }
        if self.parameters is not None:
            result["parameters"] = self.parameters
        return result
    
    @classmethod
    def create_from_analysis(cls, text: str, entities: Dict[str, Any], 
                           method: str = "ner") -> 'NLUCommand':
        command = cls()
        command.debug_info["text_processed"] = text
        command.debug_info["method"] = method
        command.debug_info["timestamp"] = datetime.now().isoformat()
        
        return command