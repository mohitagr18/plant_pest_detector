# Plant Detector Project Structure

## Overview
The Plant Detector is an AI-powered agricultural assistant that identifies plant pests and diseases from images, provides location-based recommendations, and offers comprehensive treatment guidance through conversational AI.

## Project Architecture

### Core Components
1. **Plant Pest Detection** - AI-powered image analysis using Google Gemini
2. **Location Services** - Weather and soil data integration
3. **QA Engine** - Conversational AI for agricultural advice
4. **MCP Server** - External tool integrations (Amazon, Weather APIs)
5. **Testing Suite** - Comprehensive test coverage

---

## Directory Structure

```
plant_detector/
├── src/                          # Core application modules
│   ├── __init__.py              # Package initialization
│   ├── plant_pest_detector.py    # AI image analysis for pest/disease detection
│   ├── location_service.py      # Weather & soil data services
│   └── qa_engine.py             # Conversational AI engine
│
├── mcp_server/                   # Model Context Protocol server
│   ├── amazon_tools.py          # Amazon product search integration
│   └── weather_tools.py         # Weather/soil data MCP tools
│
├── test_images/                  # Test image assets
│   └── test_img1.jpg            # Sample test image
│
├── venv/                        # Python virtual environment
│   ├── bin/                     # Virtual environment executables
│   ├── lib/                     # Installed packages
│   └── pyvenv.cfg              # Virtual environment config
│
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup configuration
├── flow.txt                     # Application workflow documentation
└── PROJECT_STRUCTURE.md        # This documentation file
```

---

## File Descriptions

### Core Source Files (`src/`)

#### `plant_pest_detector.py`
- **Purpose**: AI-powered plant pest and disease detection
- **Key Features**:
  - Uses Google Gemini 2.5 Flash model for image analysis
  - Returns structured detection results (pest/disease, severity, plant type)
  - Handles image processing with PIL
- **Main Class**: `PlantPestDetector`
- **Key Methods**:
  - `identify(image_bytes)` - Analyzes image and returns detection results
  - `_extract_value(text, key)` - Parses AI response format

#### `location_service.py`
- **Purpose**: Location-based data services (weather & soil)
- **Key Features**:
  - Integrates with National Weather Service API
  - Uses USDA Soil Data Access (SDA) for authoritative soil data
  - Converts zip codes to coordinates
  - Provides comprehensive soil texture analysis
- **Main Class**: `LocationService`
- **Key Methods**:
  - `zip_to_coordinates(zipcode)` - Converts zip to lat/lon
  - `get_weather_data(zipcode)` - Fetches current weather + 3-day forecast
  - `get_soil_data(zipcode)` - Retrieves USDA soil properties
  - `_determine_texture(clay, sand, silt)` - Classifies soil texture

#### `qa_engine.py`
- **Purpose**: Conversational AI engine for agricultural advice
- **Key Features**:
  - Context-aware recommendations based on detection + location
  - Menu-driven interaction system
  - Amazon product integration for treatment recommendations
  - Conversation history tracking
- **Main Class**: `AgriQAEngine`
- **Key Methods**:
  - `set_detection_context()` - Sets pest/disease context
  - `set_location_context()` - Sets weather/soil context
  - `generate_initial_summary()` - Creates initial assessment
  - `answer_menu_selection(option)` - Handles menu interactions
  - `ask_custom_question(question)` - Processes custom queries
  - `parse_user_input(text)` - Extracts plant/zip/infestation from text

### MCP Server Files (`mcp_server/`)

#### `amazon_tools.py`
- **Purpose**: Amazon product search integration via MCP
- **Key Features**:
  - Web scraping of Amazon search results
  - Product information extraction (name, price, rating, URL)
  - Agricultural product focus
- **Key Functions**:
  - `search_amazon_products(query, max_results)` - Core search functionality
  - `search_agricultural_products()` - MCP tool wrapper

#### `weather_tools.py`
- **Purpose**: Weather and soil data MCP tools
- **Key Features**:
  - MCP server implementation using FastMCP
  - Wraps location service functionality
  - Provides tools for external AI model integration
- **Key Functions**:
  - `get_weather(zipcode)` - MCP weather tool
  - `get_soil_type(zipcode)` - MCP soil tool
  - `get_location_context(zipcode)` - Combined context tool

### Configuration Files

#### `requirements.txt`
- **Dependencies**:
  - Flask>=3.0.0 (Web framework)
  - google-generativeai>=0.6.0 (AI model integration)
  - Pillow>=10.0.0 (Image processing)
  - requests>=2.31.0 (HTTP requests)
  - python-dotenv>=1.0.0 (Environment variables)
  - fastmcp (MCP server framework)
  - beautifulsoup4>=4.12.0 (Web scraping)
  - lxml>=4.9.0 (XML parsing)

#### `setup.py`
- **Purpose**: Package configuration
- **Details**: Basic setuptools configuration for package installation

### Documentation Files

#### `flow.txt`
- **Purpose**: Application workflow documentation
- **Content**: Step-by-step user interaction flow
- **Key Steps**:
  1. Image upload → Detection summary
  2. Location input → Context gathering
  3. Enhanced summary with local data
  4. Interactive QA system

### Test Files

#### `test_location_service.py`
- **Purpose**: Tests weather and soil data services
- **Coverage**: Multiple zip codes, error handling, data validation

#### `test_phase3_flow.py`
- **Purpose**: End-to-end application flow testing
- **Features**: Complete user interaction simulation, menu testing

#### `test_amazon_integration.py`
- **Purpose**: Amazon product search testing
- **Coverage**: Multiple product queries, result validation

---

## Application Workflow

### 1. Image Analysis Phase
```
User uploads image → PlantPestDetector.identify() → 
Returns: pest/disease, severity, plant type, confidence
```

### 2. Context Gathering Phase
```
User provides: plant type, zip code, infestation level →
LocationService fetches: weather + soil data →
QA Engine sets context for recommendations
```

### 3. Interactive Recommendation Phase
```
QA Engine presents menu options:
1. Treatment Recommendations (with Amazon product links)
2. Detailed Soil Impact Analysis
3. Weather-Based Timing Guidance
4. Monitoring & Prevention Tips
5. Comprehensive Detailed Report
6. Custom Question Handling
```

### 4. External Integrations
- **Amazon Integration**: Product search and recommendation links
- **Weather API**: National Weather Service for current conditions and forecasts
- **Soil API**: USDA Soil Data Access for authoritative soil properties

---

## Key Features

### AI-Powered Detection
- Uses Google Gemini 2.5 Flash for image analysis
- Structured output format for consistent parsing
- Confidence scoring for plant identification

### Location-Aware Recommendations
- Zip code to coordinate conversion
- Real-time weather data integration
- USDA soil database integration
- Context-aware treatment recommendations

### Conversational Interface
- Menu-driven interaction system
- Custom question handling
- Conversation history tracking
- Context preservation across interactions

### Product Integration
- Amazon product search for treatment recommendations
- Product information extraction (price, rating, availability)
- Direct purchase links for recommended products

---

## Environment Setup

### Required Environment Variables
- `GOOGLE_API_KEY` - Google Gemini API access key

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python test_location_service.py
python test_phase3_flow.py test_images/test_img1.jpg
python test_amazon_integration.py
```

---

## Technical Architecture

### Data Flow
1. **Image Input** → AI Analysis → Detection Results
2. **User Input** → Location Services → Weather/Soil Data
3. **Context Assembly** → QA Engine → Recommendations
4. **Product Search** → Amazon Integration → Purchase Links

### API Integrations
- **Google Gemini API**: AI image analysis
- **National Weather Service API**: Weather data
- **USDA Soil Data Access**: Soil properties
- **Amazon Web Scraping**: Product search

### Error Handling
- Graceful degradation for API failures
- Fallback responses for missing data
- Comprehensive error logging and user feedback

---

## Future Enhancements

### Potential Improvements
1. **Database Integration**: Store detection history and user preferences
2. **Mobile App**: Native mobile application
3. **Advanced Analytics**: Detection accuracy tracking
4. **Multi-language Support**: Internationalization
5. **Expert Network**: Connect with agricultural experts
6. **IoT Integration**: Sensor data integration for monitoring

### Scalability Considerations
- **Caching**: Redis for API response caching
- **Load Balancing**: Multiple API endpoints
- **Database**: PostgreSQL for structured data storage
- **Microservices**: Service decomposition for better scalability
