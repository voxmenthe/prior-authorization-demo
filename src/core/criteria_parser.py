from enum import Enum
from typing import Dict, List, Optional, Union
import re
import json

class CriterionType(Enum):
    REQUIRED = "required"      # Must be true
    EXCLUSIONARY = "exclusionary"  # Must be false
    DOCUMENTATION = "documentation"  # Must be provided
    THRESHOLD = "threshold"    # Must meet numeric criteria

class LogicalOperator(Enum):
    AND = "and"
    OR = "or"

class CriteriaParser:
    """Parser for structured criteria with AND/OR relationships"""
    
    def __init__(self):
        # Patterns to identify different criterion types
        self.exclusionary_patterns = [
            r"must not",
            r"no history of",
            r"absence of", 
            r"without",
            r"contraindicated",
            r"prohibited",
            r"should not have",
            r"cannot have"
        ]
        
        self.documentation_patterns = [
            r"documentation",
            r"must provide",
            r"submit",
            r"records",
            r"evidence",
            r"proof",
            r"report"
        ]
        
        self.threshold_patterns = [
            r"≥|>=|greater than or equal",
            r"≤|<=|less than or equal", 
            r">|greater than",
            r"<|less than",
            r"between",
            r"at least",
            r"minimum of",
            r"maximum of",
            r"\d+\s*(years?\s*or\s*older|years?\s*of\s*age)",
            r"age.*\d+",
            r"\d+\s*years"
        ]
    
    def parse_criteria_text(self, text: str) -> Dict:
        """Parse free-form criteria text into structured format"""
        
        # Split text into individual criteria
        criteria_items = self._split_criteria(text)
        
        parsed_criteria = {
            "criteria_list": [],
            "logical_structure": "AND",  # Default to AND logic
            "exclusionary_criteria": [],
            "required_criteria": [],
            "documentation_criteria": [],
            "threshold_criteria": []
        }
        
        for i, item in enumerate(criteria_items):
            criterion = self._parse_single_criterion(item, f"criterion_{i+1}")
            parsed_criteria["criteria_list"].append(criterion)
            
            # Categorize by type
            if criterion["type"] == "EXCLUSIONARY":
                parsed_criteria["exclusionary_criteria"].append(criterion["id"])
            elif criterion["type"] == "DOCUMENTATION":
                parsed_criteria["documentation_criteria"].append(criterion["id"])
            elif criterion["type"] == "THRESHOLD":
                parsed_criteria["threshold_criteria"].append(criterion["id"])
            else:
                parsed_criteria["required_criteria"].append(criterion["id"])
        
        return parsed_criteria
    
    def _split_criteria(self, text: str) -> List[str]:
        """Split criteria text into individual items"""
        # First try numbered lists
        numbered_pattern = r'\n?\s*\d+\.\s*'
        numbered_items = re.split(numbered_pattern, text)
        
        if len(numbered_items) > 2:  # Found numbered items
            # Remove empty first item if present
            if numbered_items[0].strip() == '':
                numbered_items = numbered_items[1:]
            return [item.strip() for item in numbered_items if item.strip() and len(item.strip()) > 5]
        
        # Try other splitting patterns
        split_patterns = [
            r'\n[a-zA-Z]\.',  # Lettered lists
            r'\n•',  # Bullet points
            r'\n-',  # Dashes
            r'\nAND',  # Explicit AND
            r'\nOR',   # Explicit OR
        ]
        
        items = [text]
        for pattern in split_patterns:
            new_items = []
            for item in items:
                split_result = re.split(pattern, item)
                if len(split_result) > 1:
                    new_items.extend(split_result)
                else:
                    new_items.append(item)
            items = new_items
        
        # Clean up items
        cleaned_items = []
        for item in items:
            item = item.strip()
            if item and len(item) > 10:  # Filter out very short fragments
                cleaned_items.append(item)
        
        # If no good splits found, return the whole text as single criterion
        return cleaned_items if cleaned_items else [text.strip()]
    
    def _parse_single_criterion(self, text: str, criterion_id: str) -> Dict:
        """Parse a single criterion into structured format"""
        
        criterion = {
            "id": criterion_id,
            "original_text": text,
            "type": self._determine_criterion_type(text),
            "description": self._extract_description(text),
            "conditions": self._extract_conditions(text),
            "thresholds": self._extract_thresholds(text),
            "exceptions": self._extract_exceptions(text)
        }
        
        return criterion
    
    def _determine_criterion_type(self, text: str) -> str:
        """Determine the type of criterion based on text patterns"""
        text_lower = text.lower()
        
        # Check for exclusionary patterns
        for pattern in self.exclusionary_patterns:
            if re.search(pattern, text_lower):
                return "EXCLUSIONARY"
        
        # Check for documentation patterns
        for pattern in self.documentation_patterns:
            if re.search(pattern, text_lower):
                return "DOCUMENTATION"
        
        # Check for threshold patterns
        for pattern in self.threshold_patterns:
            if re.search(pattern, text_lower):
                return "THRESHOLD"
        
        # Default to required
        return "REQUIRED"
    
    def _extract_description(self, text: str) -> str:
        """Extract a clean description from the criterion text"""
        # Remove common prefixes and clean up
        cleaned = re.sub(r'^(Patient must|Must|Requirement:|Criteria:)', '', text, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        return cleaned if cleaned else text
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract specific conditions from the text"""
        conditions = []
        
        # Look for specific medical conditions
        condition_patterns = [
            r'Type \d+ diabetes',
            r'diabetes mellitus',
            r'hypertension',
            r'heart failure',
            r'cardiovascular disease',
            r'kidney disease',
            r'pancreatitis',
            r'cancer',
            r'pregnancy'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditions.extend(matches)
        
        return list(set(conditions))  # Remove duplicates
    
    def _extract_thresholds(self, text: str) -> Dict:
        """Extract numeric thresholds from the text"""
        thresholds = {}
        
        # Age thresholds
        age_match = re.search(r'age.*?(\d+)', text, re.IGNORECASE)
        if age_match:
            thresholds['age'] = int(age_match.group(1))
        
        # HbA1c thresholds
        hba1c_match = re.search(r'hba1c.*?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if hba1c_match:
            thresholds['hba1c'] = float(hba1c_match.group(1))
        
        # BMI thresholds
        bmi_match = re.search(r'bmi.*?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if bmi_match:
            thresholds['bmi'] = float(bmi_match.group(1))
        
        return thresholds
    
    def _extract_exceptions(self, text: str) -> List[str]:
        """Extract exceptions or contraindications"""
        exceptions = []
        
        # Look for exception patterns
        exception_patterns = [
            r'except(?:ion)?:?\s*(.+?)(?:\n|$)',
            r'unless:?\s*(.+?)(?:\n|$)',
            r'contraindicated in:?\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in exception_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            exceptions.extend(matches)
        
        return [exc.strip() for exc in exceptions if exc.strip()]
    
    def enhance_criteria_relationships(self, parsed_criteria: Dict) -> Dict:
        """Enhance parsed criteria with logical relationships"""
        
        # Analyze relationships between criteria
        criteria_list = parsed_criteria.get("criteria_list", [])
        
        # Group related criteria
        groups = self._group_related_criteria(criteria_list)
        
        # Determine optimal evaluation order
        evaluation_order = self._determine_evaluation_order(criteria_list)
        
        enhanced_criteria = parsed_criteria.copy()
        enhanced_criteria.update({
            "criteria_groups": groups,
            "evaluation_order": evaluation_order,
            "dependency_map": self._build_dependency_map(criteria_list)
        })
        
        return enhanced_criteria
    
    def _group_related_criteria(self, criteria_list: List[Dict]) -> Dict:
        """Group related criteria together"""
        groups = {
            "eligibility": [],
            "contraindications": [],
            "documentation": [],
            "clinical_parameters": []
        }
        
        for criterion in criteria_list:
            criterion_type = criterion.get("type", "REQUIRED")
            if criterion_type == "EXCLUSIONARY":
                groups["contraindications"].append(criterion["id"])
            elif criterion_type == "DOCUMENTATION":
                groups["documentation"].append(criterion["id"])
            elif criterion_type == "THRESHOLD":
                groups["clinical_parameters"].append(criterion["id"])
            else:
                groups["eligibility"].append(criterion["id"])
        
        return groups
    
    def _determine_evaluation_order(self, criteria_list: List[Dict]) -> List[str]:
        """Determine optimal order for evaluating criteria"""
        # Prioritize exclusionary criteria first (fail-fast)
        exclusionary = [c["id"] for c in criteria_list if c.get("type") == "EXCLUSIONARY"]
        
        # Then required criteria
        required = [c["id"] for c in criteria_list if c.get("type") == "REQUIRED"]
        
        # Then threshold criteria
        threshold = [c["id"] for c in criteria_list if c.get("type") == "THRESHOLD"]
        
        # Finally documentation
        documentation = [c["id"] for c in criteria_list if c.get("type") == "DOCUMENTATION"]
        
        # Add any criteria without type to required
        untyped = [c["id"] for c in criteria_list if c.get("type") is None]
        
        return exclusionary + required + untyped + threshold + documentation
    
    def _build_dependency_map(self, criteria_list: List[Dict]) -> Dict:
        """Build a map of dependencies between criteria"""
        dependency_map = {}
        
        for criterion in criteria_list:
            criterion_id = criterion["id"]
            dependencies = []
            
            # Look for references to other criteria in the text
            for other_criterion in criteria_list:
                if other_criterion["id"] != criterion_id:
                    # Simple text-based dependency detection
                    criterion_text = criterion.get("original_text", criterion.get("description", "")).lower()
                    other_conditions = other_criterion.get("conditions", [])
                    other_text = other_criterion.get("original_text", other_criterion.get("description", "")).lower()
                    
                    # Check if any conditions from other criterion appear in this criterion's text
                    if other_conditions and any(condition.lower() in criterion_text for condition in other_conditions):
                        dependencies.append(other_criterion["id"])
                    # Or check if the other criterion's text appears in this criterion
                    elif other_text and len(other_text) > 5 and other_text in criterion_text:
                        dependencies.append(other_criterion["id"])
            
            dependency_map[criterion_id] = dependencies
        
        return dependency_map