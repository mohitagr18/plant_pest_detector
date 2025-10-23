# test_agentic_flow.py

import sys
import os
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from plant_pest_detector import PlantPestDetector
from qa_engine_agentic import (
    create_agentic_session,
    generate_brief_assessment,
    generate_treatment_recommendations,
    answer_menu_option,
    ask_custom_question,
    get_menu_options
)

def test_agentic_flow(image_path):
    """Mobile-optimized agentic flow"""
    
    print("\n" + "=" * 70)
    print("AGENTIC AGRICULTURAL ASSISTANT")
    print("=" * 70)
    
    detector = PlantPestDetector()
    
    # STEP 1: Image detection
    print(f"\n📸 Analyzing image...")
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image not found")
        return
    
    image = Image.open(image_path)
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    
    pest, severity, plant, confidence, subject_type = detector.identify(image_bytes)
    
    # Show detection results + brief assessment
    print(f"\n✓ Detection Results:")
    print(f"   Issue: {pest}")
    print(f"   Severity: {severity}")
    print(f"   Plant: {plant if plant != 'Unknown' else 'Not identified'}")
    
    # Generate brief risk assessment
    brief_assessment = generate_brief_assessment(pest, severity, plant)
    print(f"\n⚠️  {brief_assessment}")
    
    # STEP 2: Prompt for details (brief and mobile-friendly)
    print(f"\n{'─' * 70}")
    print("📝 Get Personalized Treatment Plan")
    print(f"{'─' * 70}")
    print("\nI can generate detailed treatment and product recommendations")
    print("based on your soil and weather data if you share:")
    print("plant type, zip code, infestation level")
    print("\nExample: tomato, 92336, low")
    
    user_input = input(f"\n➤ Enter details: ").strip()
    
    if user_input:
        parts = [p.strip() for p in user_input.split(',')]
        plant_final = parts[0] if len(parts) > 0 and parts[0] else (plant if plant != "Unknown" else "vegetable garden")
        zipcode = parts[1] if len(parts) > 1 else "92336"
        infestation = parts[2].lower() if len(parts) > 2 else "medium"
    else:
        plant_final = plant if plant != "Unknown" else "vegetable garden"
        zipcode = "92336"
        infestation = "medium"
    
    # STEP 3: Create session and generate treatment recommendations
    context = create_agentic_session(
        pest_or_disease=pest,
        severity=severity,
        plant_type=plant_final,
        infestation_level=infestation,
        zipcode=zipcode
    )
    
    # Show treatment recommendations with products
    treatment_recommendations = generate_treatment_recommendations(context)
    
    print(f"\n{'═' * 70}")
    print(treatment_recommendations)
    print(f"{'═' * 70}")
    
    # STEP 4: Show menu (without Treatment Recommendations option)
    menu_options = get_menu_options()
    
    while True:
        print(f"\n{'─' * 70}")
        print("WHAT ELSE WOULD YOU LIKE TO KNOW?")
        print(f"{'─' * 70}")
        
        for option in menu_options:
            print(option)
        
        print("\n(Type 'quit' to exit)")
        
        choice = input("\n➤ Select option (1-5): ").strip()
        
        if choice.lower() in ['quit', 'exit', 'q']:
            break
        
        try:
            option_num = int(choice)
            
            if option_num == 5:  # Custom question
                question = input("\n❓ Your question: ")
                print()
                answer = ask_custom_question(context, question)
                print(answer)
            elif 1 <= option_num <= 4:
                # Map menu options to function options (add 1 since we removed option 1)
                function_option = option_num + 1
                print()
                answer = answer_menu_option(context, function_option)
                print(f"\n{answer}")
            else:
                print("❌ Invalid option. Please select 1-5.")
        
        except ValueError:
            print("❌ Please enter a number 1-5.")
    
    print("\n✅ Session complete!")


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "test_images/test_img1.jpg"
    test_agentic_flow(image_path)
