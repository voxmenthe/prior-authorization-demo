import json
from src.core.llm_client import LlmClient
from src.core.schemas import ParsedCriteria
from src.core.exceptions import CriteriaParsingError

class CriteriaParserAgent:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.llm = LlmClient(verbose=verbose)
        if verbose:
            print("🧩 CriteriaParserAgent initialized")
        
    def parse(self, ocr_text: str) -> dict:
        if self.verbose:
            print(f"\n📋 Parsing criteria document ({len(ocr_text)} chars)")
        
        # Extract key sections
        sections = self._extract_sections(ocr_text)
        
        if self.verbose:
            print(f"   Found sections: {list(sections.keys())}")
        
        # Parse each section with specialized prompts
        parsed_sections = {}
        for section_name, section_text in sections.items():
            if self.verbose:
                print(f"   Processing {section_name} section...")
            
            if section_name == "CRITERIA":
                parsed_sections[section_name] = self._parse_criteria_section(section_text)
                if self.verbose and parsed_sections[section_name]:
                    criteria_count = len(parsed_sections[section_name].get('criteria', []))
                    print(f"   ✅ Extracted {criteria_count} criteria")
            elif section_name == "INDICATIONS":
                parsed_sections[section_name] = self._parse_indications(section_text)
            # ... other sections
            
        return parsed_sections
    
    def _extract_sections(self, ocr_text: str) -> dict:
        # Placeholder for section extraction logic
        return {"CRITERIA": ocr_text} # Simplified for now

    def _parse_indications(self, section_text: str) -> dict:
        # Placeholder for indications parsing logic
        return {}

    def _parse_criteria_section(self, text: str) -> dict:
        prompt = f"""
        You are a medical criteria parser. Extract all approval criteria from the following text.
        For each criterion, identify:
        1. The main condition being checked
        2. Whether it's required (ALL) or optional (ANY)
        3. Sub-conditions and their relationships
        4. Specific thresholds, values, or requirements
        5. Exceptions or contraindications

        Text: {text}

        Return a structured JSON that adheres to the provided schema.
        """
        
        try:
            parsed_response = self.llm.generate_structured_json(
                prompt=prompt,
                response_schema=ParsedCriteria
            )
            # The response is already a Pydantic object, convert to dict if needed
            return parsed_response.model_dump()
        except Exception as e:
            raise CriteriaParsingError(f"Failed to parse criteria section: {str(e)}") from e