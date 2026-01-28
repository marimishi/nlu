from typing import Dict, Any

from core.registry.knowledge_base import KnowledgeBase


class RegistryService:
    def __init__(self):
        self.knowledge_base = KnowledgeBase()
    
    def find_module_by_target(self, target_text: str) -> str:
        return self.knowledge_base.find_module_by_synonym(target_text)
    
    def find_module_in_text(self, text: str) -> str:
        return self.knowledge_base.find_module_in_text(text)
    
    def get_module_registry(self, module_id: str) -> Dict[str, Any]:
        return self.knowledge_base.get_module_info(module_id)
    
    def get_command_template(self, module_id: str) -> Dict[str, Any]:
        module_info = self.get_module_registry(module_id)
        if module_info:
            return {
                "intent": module_info.get("intent", "UNKNOWN"),
                "target": module_info.get("target", ""),
                "slots": module_info.get("slots", {})
            }
        return {}