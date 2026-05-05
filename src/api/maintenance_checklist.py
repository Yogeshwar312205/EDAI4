"""
Dynamic Maintenance Checklist Generator
Generates equipment-specific maintenance checklists using Gemini AI
"""

import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import google.generativeai as genai

logger = logging.getLogger(__name__)


# ============================================
# Request/Response Models
# ============================================

class MaintenanceChecklistRequest(BaseModel):
    """Request model for maintenance checklist generation"""
    equipment_type: str = Field(..., description="Type of equipment (e.g., 'Centrifugal Pump', 'Control Valve')")
    equipment_tag: str = Field(..., description="Equipment tag/ID (e.g., 'P-101', 'FCV-205')")
    equipment_description: str = Field(default="", description="Additional equipment details")


class MaintenanceTask(BaseModel):
    """Single maintenance task"""
    step: int = Field(..., description="Step number")
    task: str = Field(..., description="Task description")
    frequency: str = Field(..., description="Recommended frequency (e.g., 'Daily', 'Weekly', 'Monthly')")
    safety_notes: str = Field(default="", description="Safety considerations")


class MaintenanceChecklistResponse(BaseModel):
    """Response model for maintenance checklist"""
    equipment_type: str = Field(..., description="Equipment type")
    equipment_tag: str = Field(..., description="Equipment tag")
    checklist_title: str = Field(..., description="Checklist title")
    tasks: List[MaintenanceTask] = Field(..., description="List of maintenance tasks")
    safety_warnings: List[str] = Field(default_factory=list, description="General safety warnings")
    estimated_time: str = Field(default="", description="Estimated time to complete")


# ============================================
# Maintenance Checklist Generator
# ============================================

class MaintenanceChecklistGenerator:
    """
    Dynamic Maintenance Checklist Generator using Gemini AI
    """
    
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        """
        Initialize Maintenance Checklist Generator
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use (default: gemini-2.5-flash, was gemini-1.5-flash but deprecated)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        # Remove 'models/' prefix if present (OLD API adds it automatically)
        self.model_name = model.replace("models/", "")
        
        # Configure and initialize model (OLD API - deprecated but still works)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info(f"Maintenance Checklist Generator initialized with model: {self.model_name}")
    
    
    def generate_checklist(
        self,
        equipment_type: str,
        equipment_tag: str,
        equipment_description: str = ""
    ) -> MaintenanceChecklistResponse:
        """
        Generate maintenance checklist for equipment
        
        Args:
            equipment_type: Type of equipment
            equipment_tag: Equipment tag/ID
            equipment_description: Additional details
            
        Returns:
            MaintenanceChecklistResponse with tasks
        """
        
        # Build prompt
        prompt = self._build_prompt(equipment_type, equipment_tag, equipment_description)
        
        try:
            logger.info(f"Generating maintenance checklist for: {equipment_type} ({equipment_tag})")
            
            # Call Gemini
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            logger.info(f"Gemini response received: {len(result_text)} characters")
            
            # Parse JSON response
            import json
            import re
            
            # Try to find JSON in markdown code block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                # Try to find JSON without code block
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
            
            result_dict = json.loads(result_text)
            
            return MaintenanceChecklistResponse(**result_dict)
            
        except Exception as e:
            logger.error(f"Maintenance checklist generation failed: {e}")
            # Return fallback response
            return self._generate_fallback_checklist(equipment_type, equipment_tag)
    
    
    def _build_prompt(
        self,
        equipment_type: str,
        equipment_tag: str,
        equipment_description: str
    ) -> str:
        """Build prompt for maintenance checklist generation"""
        
        prompt = f"""You are a Senior Maintenance Engineer with 25+ years of experience in industrial equipment maintenance, specializing in process plants, refineries, and chemical facilities.

Your expertise includes:
- Preventative maintenance (PM) programs
- Predictive maintenance strategies
- Equipment reliability and asset management
- Safety procedures and LOTO (Lockout/Tagout)
- Industry standards (API, ASME, ISA, NFPA)

EQUIPMENT INFORMATION:
Type: {equipment_type}
Tag: {equipment_tag}
Description: {equipment_description or "Standard industrial equipment"}

TASK:
Generate a comprehensive preventative maintenance checklist for this equipment. The checklist should be:
1. Specific to the equipment type
2. Based on industry best practices and standards
3. Practical and actionable
4. Safety-focused
5. Include recommended frequencies

CHECKLIST REQUIREMENTS:
- 5-10 maintenance tasks
- Each task should have: step number, description, frequency, safety notes
- Include general safety warnings
- Estimate total time required
- Follow industry standards (API, ASME, ISA as applicable)

RESPONSE FORMAT (JSON):
{{
  "equipment_type": "{equipment_type}",
  "equipment_tag": "{equipment_tag}",
  "checklist_title": "Preventative Maintenance Checklist - {equipment_type}",
  "tasks": [
    {{
      "step": 1,
      "task": "Inspect pump casing for leaks, cracks, or corrosion",
      "frequency": "Weekly",
      "safety_notes": "Ensure pump is de-energized and isolated before inspection"
    }},
    {{
      "step": 2,
      "task": "Check bearing temperature and vibration levels",
      "frequency": "Daily",
      "safety_notes": "Use non-contact thermometer and vibration meter"
    }}
  ],
  "safety_warnings": [
    "Always follow LOTO procedures before maintenance",
    "Wear appropriate PPE (safety glasses, gloves, hearing protection)",
    "Verify zero energy state before starting work"
  ],
  "estimated_time": "45-60 minutes"
}}

Provide your response as a JSON object with this exact structure. Be specific and practical."""
        
        return prompt
    
    
    def _generate_fallback_checklist(
        self,
        equipment_type: str,
        equipment_tag: str
    ) -> MaintenanceChecklistResponse:
        """Generate generic fallback checklist when AI fails"""
        
        logger.warning("Using fallback maintenance checklist (AI unavailable)")
        
        # Generic tasks applicable to most equipment
        generic_tasks = [
            MaintenanceTask(
                step=1,
                task="Visual inspection for leaks, damage, or abnormal conditions",
                frequency="Daily",
                safety_notes="Observe from safe distance, do not touch hot surfaces"
            ),
            MaintenanceTask(
                step=2,
                task="Check for unusual noises, vibrations, or odors",
                frequency="Daily",
                safety_notes="Use hearing protection in high-noise areas"
            ),
            MaintenanceTask(
                step=3,
                task="Verify all gauges and indicators are reading normally",
                frequency="Daily",
                safety_notes="Do not adjust settings without authorization"
            ),
            MaintenanceTask(
                step=4,
                task="Inspect mounting bolts and connections for tightness",
                frequency="Weekly",
                safety_notes="Ensure equipment is de-energized before touching"
            ),
            MaintenanceTask(
                step=5,
                task="Clean equipment exterior and remove debris",
                frequency="Weekly",
                safety_notes="Use appropriate cleaning materials, avoid water on electrical components"
            ),
            MaintenanceTask(
                step=6,
                task="Lubricate moving parts per manufacturer specifications",
                frequency="Monthly",
                safety_notes="Use correct lubricant type and quantity"
            ),
            MaintenanceTask(
                step=7,
                task="Test safety devices and alarms",
                frequency="Monthly",
                safety_notes="Follow test procedures, notify operations before testing"
            ),
        ]
        
        return MaintenanceChecklistResponse(
            equipment_type=equipment_type,
            equipment_tag=equipment_tag,
            checklist_title=f"Generic Preventative Maintenance Checklist - {equipment_type}",
            tasks=generic_tasks,
            safety_warnings=[
                "Always follow Lockout/Tagout (LOTO) procedures before maintenance",
                "Wear appropriate Personal Protective Equipment (PPE)",
                "Verify zero energy state before starting work",
                "Obtain proper work permits and authorizations",
                "Never bypass safety devices or interlocks"
            ],
            estimated_time="30-45 minutes"
        )


# ============================================
# Singleton Instance
# ============================================

_generator_instance = None

def get_maintenance_generator() -> MaintenanceChecklistGenerator:
    """Get or create maintenance checklist generator singleton instance"""
    global _generator_instance
    
    if _generator_instance is None:
        try:
            _generator_instance = MaintenanceChecklistGenerator()
            logger.info("Maintenance Checklist Generator instance created")
        except Exception as e:
            logger.error(f"Failed to create Maintenance Checklist Generator: {e}")
            raise
    
    return _generator_instance
