# src/plant_pest_detector.py

import os
import google.generativeai as genai
from io import BytesIO
from PIL import Image


class PlantPestDetector:
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def identify(self, image_bytes):
        """
        Quick identification: Returns only essential info for initial detection
        Returns: (pest_or_disease, severity, plant_type, plant_confidence, subject_type)
        """
        # Open image with PIL
        image = Image.open(BytesIO(image_bytes))
        
        # Single prompt for quick identification
        prompt = """You are an agricultural AI expert. Analyze this image quickly and provide ONLY essential information.

Respond in EXACTLY this format (one item per line):

DETECTED: [Name of pest, disease, or health issue - be specific]
SEVERITY: [Mild/Moderate/Severe]
PLANT: [Specific plant or crop type if visible, or "Unknown" if not identifiable]
TYPE: [pest/disease/healthy]

Keep it brief - detailed analysis comes later."""
        
        try:
            # Generate quick identification
            response = self.model.generate_content([prompt, image])
            result = response.text.strip()
            
            # Parse response
            pest_or_disease = self._extract_value(result, "DETECTED")
            severity = self._extract_value(result, "SEVERITY")
            plant_type = self._extract_value(result, "PLANT")
            subject_type = self._extract_value(result, "TYPE")
            
            # Determine plant confidence
            plant_confidence = "high"
            plant_lower = plant_type.lower()
            if "unknown" in plant_lower or "not clear" in plant_lower or plant_type == "":
                plant_confidence = "low"
                plant_type = "Unknown"
            elif "possibly" in plant_lower or "might" in plant_lower:
                plant_confidence = "low"
            
            return pest_or_disease, severity, plant_type, plant_confidence, subject_type
            
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            return "Error", "Unknown", "Unknown", "low", "error"
    
    def _extract_value(self, text, key):
        """Extract value from KEY: VALUE format"""
        for line in text.splitlines():
            if line.strip().upper().startswith(f"{key}:"):
                value = line.split(":", 1)[1].strip()
                return value if value else "Unknown"
        return "Unknown"
