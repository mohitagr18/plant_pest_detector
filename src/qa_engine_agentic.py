# src/qa_engine_agentic.py
# Mobile-optimized agentic engine with streamlined flow

import os
import google.generativeai as genai
from typing import Dict, List

# ============================================================================
# CONFIGURATION - Update these values in one place
# ============================================================================

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = 'gemini-2.5-flash'

# Configure Gemini once at module load
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    raise ValueError("GOOGLE_API_KEY environment variable not set")


# ============================================================================
# PYTHON FUNCTION IMPLEMENTATIONS (Called by Gemini)
# ============================================================================

def get_weather(zipcode: str) -> dict:
    """Get weather data for zip code"""
    print(f"   🔧 Tool Called: get_weather(zipcode={zipcode})")
    from src.location_service import LocationService
    location_service = LocationService()
    result = location_service.get_weather_data(zipcode)
    print(f"   ✓ Weather data retrieved")
    return result


def get_soil_type(zipcode: str) -> dict:
    """Get soil data for zip code"""
    print(f"   🔧 Tool Called: get_soil_type(zipcode={zipcode})")
    from src.location_service import LocationService
    location_service = LocationService()
    result = location_service.get_soil_data(zipcode)
    print(f"   ✓ Soil data retrieved")
    return result


def search_amazon_products(query: str, max_results: int = 3) -> List[Dict]:
    """Search Amazon products via Serper"""
    print(f"   🔧 Tool Called: search_amazon_products(query='{query}')")
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_server'))
    from agri_tools import SerperProductSearch
    
    client = SerperProductSearch()
    result = client.search_products(query, max_results)
    print(f"   ✓ Found {len(result)} products")
    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_weather_display(weather_data: dict) -> str:
    """Format weather data with emojis for display"""
    if "error" in weather_data:
        return "⚠️ Weather data unavailable"
    
    location = weather_data.get("location", {})
    current = weather_data.get("current", {})
    forecast = weather_data.get("forecast_3day", [])
    
    display = f"""**Current Weather:**
- 📍 Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}
- 🌡️ Temperature: {current.get('temperature', 'N/A')}°{current.get('temperature_unit', 'F')}
- ☁️ Conditions: {current.get('short_forecast', 'N/A')}
- 💨 Wind: {current.get('wind_speed', 'N/A')} {current.get('wind_direction', 'N/A')}

**3-Day Forecast:**
"""
    
    for period in forecast[:6]:
        display += f"• {period.get('name', 'N/A')}: {period.get('temperature', 'N/A')}° - {period.get('short_forecast', 'N/A')}\n"
    
    return display


def format_soil_display(soil_data: dict) -> str:
    """Format soil data with emojis for display"""
    if "error" in soil_data:
        return "⚠️ Soil data unavailable"
    
    soil_props = soil_data.get("soil_properties", {})
    
    display = f"""**Your Soil Type:**
- 🪨 Name: {soil_props.get('soil_name', 'Unknown')}
- 📊 Texture: {soil_props.get('soil_texture', 'Unknown')}
- 💧 Drainage: {soil_props.get('drainage_class', 'Unknown')}
"""
    
    sand = soil_props.get('sand_percent', 'Not available')
    clay = soil_props.get('clay_percent', 'Not available')
    silt = soil_props.get('silt_percent', 'Not available')
    ph = soil_props.get('ph', 'Not available')
    organic = soil_props.get('organic_matter_percent', 'Not available')
    
    if sand != "Not available":
        display += f"- 🏖️ Sand: {sand}%\n"
    if clay != "Not available":
        display += f"- 🧱 Clay: {clay}%\n"
    if silt != "Not available":
        display += f"- 🌾 Silt: {silt}%\n"
    if ph != "Not available":
        display += f"- 🧪 pH: {ph}\n"
    if organic != "Not available":
        display += f"- 🌿 Organic Matter: {organic}%\n"
    
    return display


def get_weather_data(context: dict) -> dict:
    """Retrieve weather data for context"""
    from src.location_service import LocationService
    location_service = LocationService()
    return location_service.get_weather_data(context['zipcode'])


def get_soil_data(context: dict) -> dict:
    """Retrieve soil data for context"""
    from src.location_service import LocationService
    location_service = LocationService()
    return location_service.get_soil_data(context['zipcode'])


# ============================================================================
# AGENTIC SESSION
# ============================================================================

def create_agentic_session(pest_or_disease: str, severity: str, plant_type: str,
                          infestation_level: str, zipcode: str):
    """Create agentic chat session with Gemini and tools"""
    
    tools = [get_weather, get_soil_type, search_amazon_products]
    model = genai.GenerativeModel(GEMINI_MODEL, tools=tools)
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    context = {
        'pest_or_disease': pest_or_disease,
        'severity': severity,
        'plant_type': plant_type,
        'infestation_level': infestation_level,
        'zipcode': zipcode,
        'chat': chat,
        'model': model
    }
    
    return context


def generate_brief_assessment(pest_or_disease: str, severity: str, plant_type: str) -> str:
    """Generate 1-2 line brief risk assessment without calling tools"""
    
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    prompt = f"""Provide a VERY BRIEF 1-2 sentence risk assessment for:
Pest/Disease: {pest_or_disease}
Severity: {severity}
Plant: {plant_type}

Format: One sentence about the key risk this poses to the plant. Keep it under 25 words.
Example: "Voracious feeders capable of defoliating plants within days, significantly impacting yield."

Be concise and urgent."""
    
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_treatment_recommendations(context: dict) -> str:
    """Generate treatment recommendations with products - TWO STEP APPROACH"""
    
    chat = context['chat']
    
    print(f"\n🤖 Gemini Agent: Generating personalized treatment plan...")
    
    # STEP 1: Get treatment advice ONLY (no products yet)
    treatment_prompt = f"""You are an agricultural expert.

**Context:**
- Pest/Disease: {context['pest_or_disease']}
- Plant: {context['plant_type']}
- Infestation Level: {context['infestation_level']} (CRITICAL: Use this exact level)
- Location: Zip code {context['zipcode']}

**Task:**
1. Call get_weather("{context['zipcode']}") and get_soil_type("{context['zipcode']}")
2. Write ONLY treatment advice (no products yet)

Write 1-2 short paragraphs:
- Paragraph 1: Treatment approach for {context['infestation_level']} infestation
- Paragraph 2: Application method based on soil and weather

Do NOT include products. Just write the brief treatment advice."""
    
    treatment_text = chat.send_message(treatment_prompt).text
    
    # STEP 2: Get products separately
    product_prompt = f"""Based on the treatment advice you just gave for {context['pest_or_disease']} on {context['plant_type']}, find products.

Call search_amazon_products() 2-3 times with specific organic/natural product queries.

Format ONLY as:

### 🛒 Recommended Products on Amazon

**1. [Product Name](url)**

**2. [Product Name](url)**

**3. [Product Name](url)**"""
    
    products_text = chat.send_message(product_prompt).text
    
    # Combine both
    return f"""**Treatment Recommendations:**

{treatment_text}

──────────────────────────────────────────────────────────────────────

{products_text}"""



def answer_menu_option(context: dict, option: int) -> str:
    """Answer based on menu selection (options 2-5 only)"""
    
    chat = context['chat']
    
    print(f"\n🤖 Gemini Agent: Processing option {option}...")
    
    if option == 2:  # Soil Impact
        soil_data = get_soil_data(context)
        soil_display = format_soil_display(soil_data)
        
        prompt = f"""The user can see their soil information above.

Provide analysis in 2 SHORT paragraphs:

Paragraph 1: What this soil type means for {context['plant_type']} cultivation

Paragraph 2: How soil affects treatment for {context['pest_or_disease']} (application adjustments, pH impact)

Keep it concise - exactly 2 paragraphs."""
        
        response = chat.send_message(prompt)
        return f"{soil_display}\n\n{response.text}"
    
    elif option == 3:  # Weather Timing
        weather_data = get_weather_data(context)
        weather_display = format_weather_display(weather_data)
        
        prompt = f"""The user can see their weather information above.

Provide timing guidance in 2 short paragraphs:

Paragraph 1: Best application window in next 3 days for treating {context['pest_or_disease']}

Paragraph 2: Why timing matters (rain, temperature, wind effects)

Keep it BRIEF - exactly 2 paragraphs."""
        
        response = chat.send_message(prompt)
        return f"{weather_display}\n\n{response.text}"
    
    elif option == 4:  # Monitoring
        prompt = f"""Provide monitoring and prevention advice for {context['pest_or_disease']} on {context['plant_type']}.

Include:
1. How often to check plants
2. Signs of treatment success/failure
3. Prevention tips

Keep it to 2 paragraphs."""
        
        response = chat.send_message(prompt)
        return response.text
    
    elif option == 5:  # Detailed Report
        print("\n⏳ Generating comprehensive report...")
        
        # Get weather and soil displays
        weather_data = get_weather_data(context)
        soil_data = get_soil_data(context)
        weather_display = format_weather_display(weather_data)
        soil_display = format_soil_display(soil_data)
        
        # Generate treatment recommendations with products
        treatment = generate_treatment_recommendations(context)
        
        # Get soil and weather analysis
        soil_prompt = f"""Provide 2 paragraphs about how soil conditions affect treatment for {context['pest_or_disease']} on {context['plant_type']}."""
        soil_analysis = chat.send_message(soil_prompt).text
        
        weather_prompt = f"""Provide 2 paragraphs about best treatment timing based on the weather forecast."""
        weather_analysis = chat.send_message(weather_prompt).text
        
        # Get monitoring advice
        monitoring = answer_menu_option(context, 4)
        
        report = f"""
{'═' * 70}
                    COMPREHENSIVE TREATMENT REPORT
{'═' * 70}

## 1️⃣ TREATMENT RECOMMENDATIONS

{treatment}

{'─' * 70}

## 2️⃣ SOIL IMPACT ANALYSIS

{soil_display}

{soil_analysis}

{'─' * 70}

## 3️⃣ WEATHER-BASED TIMING

{weather_display}

{weather_analysis}

{'─' * 70}

## 4️⃣ MONITORING & PREVENTION

{monitoring}

{'═' * 70}
"""
        return report
    
    else:
        return "Invalid option"


def ask_custom_question(context: dict, question: str) -> str:
    """Ask custom question - Gemini can call tools if needed"""
    
    print(f"\n🤖 Gemini Agent: Answering your question...")
    
    chat = context['chat']
    response = chat.send_message(question)
    return response.text


def get_menu_options() -> list:
    """Return menu options (Treatment Recommendations removed since already shown)"""
    return [
        "1️⃣ Detailed Soil Impact",
        "2️⃣ Weather-Based Timing",
        "3️⃣ Monitoring & Prevention",
        "4️⃣ Detailed Report (All recommendations)",
        "5️⃣ Ask Custom Question"
    ]
