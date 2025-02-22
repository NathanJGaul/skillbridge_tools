"""Schema definitions for Skillbridge opportunities."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Type, Any, ClassVar
from pydantic import BaseModel, Field, create_model

@dataclass
class SkillbridgeField:
    """Represents a field in the Skillbridge schema"""
    name: str
    type: Type
    description: str
    column_index: Optional[int] = None

class SkillbridgeSchema:
    """Central schema definition for Skillbridge opportunities"""
    fields: ClassVar[Dict[str, SkillbridgeField]] = {
        "id": SkillbridgeField("id", int, "Database ID"),
        "partner_program_agency": SkillbridgeField("partner_program_agency", str, "Partner/Program/Agency", 1),
        "service": SkillbridgeField("service", str, "Service", 2),
        "city": SkillbridgeField("city", str, "City", 3),
        "state": SkillbridgeField("state", str, "State", 4),
        "duration_of_training": SkillbridgeField("duration_of_training", str, "Duration of Training", 5),
        "employer_poc": SkillbridgeField("employer_poc", str, "Employer POC", 6),
        "poc_email": SkillbridgeField("poc_email", str, "POC Email", 7),
        "cost": SkillbridgeField("cost", str, "Cost", 8),
        "closest_installation": SkillbridgeField("closest_installation", str, "Closest Installation", 9),
        "opportunity_locations_by_state": SkillbridgeField("opportunity_locations_by_state", str, "Opportunity Locations by State", 10),
        "delivery_method": SkillbridgeField("delivery_method", str, "Delivery Method", 11),
        "target_mocs": SkillbridgeField("target_mocs", str, "Target MOCs", 12),
        "other_eligibility_factors": SkillbridgeField("other_eligibility_factors", str, "Other Eligibility Factors", 13),
        "other_prerequisite": SkillbridgeField("other_prerequisite", str, "Other/Prerequisite", 14),
        "jobs_description": SkillbridgeField("jobs_description", str, "Jobs Description", 15),
        "summary_description": SkillbridgeField("summary_description", str, "Summary Description", 16),
        "job_family": SkillbridgeField("job_family", str, "Job Family", 17),
        "mou_organization": SkillbridgeField("mou_organization", str, "MOU Organization", 18),
        "latitude": SkillbridgeField("latitude", float, "Latitude"),
        "longitude": SkillbridgeField("longitude", float, "Longitude"),
    }

    @classmethod
    def get_pydantic_model(cls) -> Type[BaseModel]:
        """Generates a Pydantic model from the schema"""
        field_definitions = {
            field.name: (Optional[field.type], Field(None, description=field.description))
            for field in cls.fields.values()
        }
        return create_model('SkillbridgeOpportunity', **field_definitions)

    @classmethod
    def get_db_columns(cls) -> List[str]:
        """Gets database column names from the schema"""
        return [field.name for field in cls.fields.values() if field.name != 'id']

    @classmethod
    def get_db_values(cls, data: Dict[str, Any]) -> tuple:
        """Gets database values in the correct order from data"""
        return tuple(data.get(field) for field in cls.get_db_columns())

    @classmethod
    def generate_identifier(cls, data: Dict[str, Any]) -> str:
        """Generates a unique identifier for an opportunity based on key fields"""
        key_fields = ['partner_program_agency', 'city', 'state']
        values = [str(data.get(field, '')).strip().lower() for field in key_fields]
        return '|'.join(values)

    @classmethod
    def has_changes(cls, new_data: Dict[str, Any], existing_data: Dict[str, Any]) -> bool:
        """Compares new data with existing data to detect changes"""
        fields_to_compare = [field for field in cls.get_db_columns() 
                           if field not in ['partner_program_agency', 'city', 'state']]
        
        for field in fields_to_compare:
            new_value = str(new_data.get(field, '')).strip()
            existing_value = str(existing_data.get(field, '')).strip()
            if new_value != existing_value:
                return True
        return False

# Create the Pydantic model from the schema
SkillbridgeOpportunity = SkillbridgeSchema.get_pydantic_model()
