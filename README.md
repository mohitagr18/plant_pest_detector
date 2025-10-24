# 🌱 Agricultural Assistant

AI-powered pest & disease detection with personalized treatment recommendations

[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B.svg)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Gemini-blue.svg)](https://gemini.google/us/about/?hl=en)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com)
[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Deployed-4285F4.svg)](https://cloud.google.com/run)

**Live Demo:** https://agri-assistant-g57ai3hf4a-uc.a.run.app/

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Usage](#usage)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Docker Setup](#docker-setup)
- [Deployment](#deployment)
- [API Keys & Environment Variables](#api-keys--environment-variables)
- [License](#license)
- [Acknowledgments](#acknowledgments)
- [Known Issues](#known-issues)
- [Future Enhancements](#future-enhancements)

---

## 🎯 Overview

Agricultural Assistant is an intelligent web application that helps gardeners identify plant pests and diseases through image recognition, then provides personalized treatment recommendations based on local weather conditions, soil types, and severity levels.

The application uses **agentic AI architecture** powered by Google Gemini 2.0 Flash, where the AI autonomously decides when to call tools for weather data, soil information, and product recommendations to generate comprehensive treatment plans.

### Why This Project?

- **Problem:** Home gardeners often struggle to identify pests/diseases and find appropriate treatments quickly
- **Solution:** Instant AI-powered diagnosis with location-specific recommendations
- **Innovation:** Agentic AI that integrates multiple data sources automatically

---

## ✨ Features

### Core Capabilities

- **🔍 AI-Powered Detection**
  - Upload plant images for instant pest/disease identification
  - Severity assessment (Mild, Moderate, Severe)
  - Plant type recognition
  - Sample images available for testing

- **🌐 Agentic AI Architecture**
  - Google Gemini autonomously calls tools based on context
  - Real-time weather data integration
  - Automatic soil type analysis
  - Dynamic product search

- **💊 Personalized Treatment Plans**
  - Severity-based treatment recommendations
  - Weather-optimized application timing
  - Soil-specific advice
  - Organic product suggestions from Amazon

- **📊 Interactive Menu System**
  - Soil Impact Analysis
  - Weather-Based Timing
  - Monitoring Guidelines
  - Full Comprehensive Report
  - Custom Q&A

---

## 📖 Usage

### 1. Upload Image
- Upload a photo of your affected plant
- Or click "Use Sample Image" to try with default example

### 2. Enter Location Details
- **ZIP Code:** For weather and soil data
- **Infestation Level:** Mild, Moderate, or Severe
- **Plant Type:** (auto-detected or manual entry)

### 3. View Treatment Recommendations
- **Initial Assessment:** Severity and urgency
- **Treatment Plan:** Specific recommendations based on weather/soil
- **Product Links:** Amazon product suggestions

### 4. Explore Additional Options
- **🪨 Soil Impact:** How soil affects treatment
- **🌤️ Weather Timing:** Best timing based on forecast
- **👀 Monitoring:** Follow-up care guidelines
- **📄 Full Report:** Comprehensive analysis
- **💬 Ask Questions:** Custom queries about your plant

---

## 🏗️ Architecture

### Agentic AI Workflow

```

User Upload → Gemini Vision (Detection) → Gemini Agent (Context Gathering)
↓
Tool Calls:
\- get\_weather()
\- get\_soil\_type()
\- search\_amazon\_products()
↓
Personalized Recommendations

```

### Technology Stack

**Frontend:**
- Streamlit (Web UI)
- Custom CSS for mobile responsiveness

**Backend:**
- Google Gemini 2.5 Flash (Agentic AI)
- Python 3.11
- PIL (Image processing)

**Data Sources:**
- NOAA Weather Service API
- USDA Web Soil Survey
- Serper Google Search API (Product search)

**Infrastructure:**
- Docker (Containerization)
- Google Cloud Run (Serverless deployment)
- Google Artifact Registry (Container storage)
- Google Secret Manager (API key management)
- GitHub Actions (CI/CD)

---

## 🗂️ Project Structure

```

plant\_pest\_detector/
│
├── app.py                          \# Main Streamlit application
│
├── src/                            \# Core application modules
│   ├── plant\_pest\_detector.py      \# Gemini Vision for pest detection
│   ├── qa\_engine\_agentic.py        \# Agentic AI with tool calling
│   ├── location\_service.py         \# Weather & soil data integration
│   └── **init**.py
│
├── mcp\_server/                     \# MCP tool definitions (optional)
│   └── agri\_tools.py               \# MCP-decorated tools for external clients
│
├── samples/                        \# Sample images for testing
│   └── citrus-aphids.jpg                  \# Default sample image
|   └── test\_img.png
│
├── .github/                        \# CI/CD workflows
│   └── workflows/
│       └── deploy.yml              \# GitHub Actions deployment
│
├── Dockerfile                      \# Docker container configuration
├── .dockerignore                   \# Docker build exclusions
├── requirements.txt                \# Python dependencies
├── .env.example                    \# Environment variables template
├── .gitignore                      \# Git exclusions
└── README.md                       \# This file

```

### Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit UI with 3-stage workflow |
| `src/plant_pest_detector.py` | Gemini Vision API integration for image analysis |
| `src/qa_engine_agentic.py` | Agentic AI engine with autonomous tool calling |
| `src/location_service.py` | NOAA Weather & USDA Soil API integration |
| `mcp_server/agri_tools.py` | MCP-decorated tools (for Claude Desktop, etc.) |
| `Dockerfile` | Multi-platform Docker build (AMD64 for Cloud Run) |

---

## 🚀 Installation

### Prerequisites

- Python 3.11+
- Docker (for containerization)
- Google Cloud SDK (for deployment)
- Git

### Local Development Setup

1. **Clone the repository**
```

git clone [https://github.com/YOUR\_USERNAME/plant\_pest\_detector.git](https://github.com/YOUR_USERNAME/plant_pest_detector.git)
cd plant\_pest\_detector

```

2. **Create virtual environment**
```

python3 -m venv venv
source venv/bin/activate  \# On Windows: venv\\Scripts\\activate

```

3. **Install dependencies**
```

pip install -r requirements.txt

```

4. **Set up environment variables**
```

cp .env.example .env

# Edit .env and add your API keys

```

Required API keys:
- `GOOGLE_API_KEY` - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `SERPER_API_KEY` - Get from [Serper.dev](https://serper.dev/)

5. **Run locally**
```

streamlit run app.py

```

The app will open at `http://localhost:8501`

---

## 🐳 Docker Setup

### Build and Run Locally

```

# Build Docker image

docker build -t agri-assistant:local .

# Run container

docker run -p 8080:8080 --env-file .env agri-assistant:local

```

Access at `http://localhost:8080`

### Build for Cloud Run (Apple Silicon Macs)

```

# Build for AMD64 architecture

docker buildx build --platform linux/amd64  
\-t us-central1-docker.pkg.dev/YOUR\_PROJECT\_ID/agri-assistant/agri-assistant:latest  
\--push .

```

---

## ☁️ Deployment

### Google Cloud Run Deployment

**One-time setup:**

1. **Enable required APIs**
```

gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com

```

2. **Create Artifact Registry repository**
```

gcloud artifacts repositories create agri-assistant  
\--repository-format=docker  
\--location=us-central1

```

3. **Store secrets**
```

echo -n "your-google-api-key" | gcloud secrets create GOOGLE\_API\_KEY --data-file=-
echo -n "your-serper-api-key" | gcloud secrets create SERPER\_API\_KEY --data-file=-

```

4. **Deploy to Cloud Run**
```

gcloud run deploy agri-assistant  
\--image us-central1-docker.pkg.dev/YOUR\_PROJECT\_ID/agri-assistant/agri-assistant:latest  
\--platform managed  
\--region us-central1  
\--allow-unauthenticated  
\--set-secrets=GOOGLE\_API\_KEY=GOOGLE\_API\_KEY:latest,SERPER\_API\_KEY=SERPER\_API\_KEY:latest  
\--memory 2Gi  
\--cpu 2  
\--timeout 300

```

---

## 🔧 API Keys & Environment Variables

Create a `.env` file in the root directory:

```

# Required

GOOGLE\_API\_KEY=your\_google\_gemini\_api\_key
SERPER\_API\_KEY=your\_serper\_api\_key

# Optional

LOG\_LEVEL=INFO

```

### Getting API Keys

**Google Gemini API:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Free tier: 60 requests/minute

**Serper API:**
1. Visit [Serper.dev](https://serper.dev/)
2. Sign up (free tier: 2,500 searches/month)
3. Get API key from dashboard

---

## 📝 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## 🙏 Acknowledgments

- Google AI for Gemini API
- NOAA for weather data
- USDA for soil database
- Streamlit community for amazing framework

---

## 🐛 Known Issues

- Large images (>5MB) may take longer to process
- Weather data limited to US ZIP codes
- Product search results may vary by location

---

## 🔮 Future Enhancements

- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Image history and tracking
- [ ] Community-contributed treatment data
- [ ] Integration with IoT sensors
- [ ] Offline mode support

---

**Built with ❤️ using Google Gemini 2.5 Flash**
