# src/location_service.py

import requests
from typing import Dict, Optional
import xml.etree.ElementTree as ET
import json


class LocationService:
    """
    Service to fetch weather and soil data from zip code
    Uses USDA Soil Data Access (SDA) for authoritative soil data
    """
    
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.soap_url = "https://graphical.weather.gov/xml/SOAP_server/ndfdXMLclient.php"
        self.sda_url = "https://sdmdataaccess.nrcs.usda.gov/Tabular/post.rest"
        self.user_agent = "AgriTech-Plant-Detector"
        self.headers = {"User-Agent": self.user_agent}
    
    def zip_to_coordinates(self, zipcode: str) -> Optional[tuple]:
        """
        Convert US zip code to lat/lon using NWS SOAP service
        """
        try:
            params = {'listZipCodeList': zipcode}
            response = requests.get(self.soap_url, params=params, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            lat_elem = root.find('.//latLonList')
            
            if lat_elem is not None and lat_elem.text:
                coords = lat_elem.text.strip().split(',')
                if len(coords) == 2:
                    return (float(coords[0]), float(coords[1]))
            
            return None
            
        except Exception as e:
            print(f"Error converting zip to coordinates: {e}")
            return None
    
    def get_weather_data(self, zipcode: str) -> Dict:
        """
        Get weather data for a zip code
        """
        coords = self.zip_to_coordinates(zipcode)
        
        if not coords:
            return {
                "error": f"Could not find location for zip code {zipcode}",
                "zipcode": zipcode
            }
        
        lat, lon = coords
        
        try:
            # Get grid endpoint
            points_url = f"{self.base_url}/points/{lat},{lon}"
            points_response = requests.get(points_url, headers=self.headers, timeout=10)
            points_response.raise_for_status()
            points_data = points_response.json()
            
            # Get forecast
            forecast_url = points_data["properties"]["forecast"]
            forecast_response = requests.get(forecast_url, headers=self.headers, timeout=10)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            periods = forecast_data["properties"]["periods"]
            current = periods[0] if periods else {}
            
            weather_info = {
                "zipcode": zipcode,
                "location": {
                    "latitude": lat,
                    "longitude": lon,
                    "city": points_data["properties"]["relativeLocation"]["properties"]["city"],
                    "state": points_data["properties"]["relativeLocation"]["properties"]["state"]
                },
                "current": {
                    "temperature": current.get("temperature"),
                    "temperature_unit": current.get("temperatureUnit"),
                    "wind_speed": current.get("windSpeed"),
                    "wind_direction": current.get("windDirection"),
                    "short_forecast": current.get("shortForecast"),
                    "detailed_forecast": current.get("detailedForecast")
                },
                "forecast_3day": [
                    {
                        "name": p.get("name"),
                        "temperature": p.get("temperature"),
                        "short_forecast": p.get("shortForecast")
                    }
                    for p in periods[:6]
                ]
            }
            
            return weather_info
            
        except Exception as e:
            return {
                "error": f"Failed to fetch weather data: {str(e)}",
                "zipcode": zipcode
            }
    
    def get_soil_data(self, zipcode: str) -> Dict:
        """
        Get soil data using USDA Soil Data Access (SDA)
        Returns dominant soil properties for the location
        """
        coords = self.zip_to_coordinates(zipcode)
        
        if not coords:
            return {
                "error": f"Could not find location for zip code {zipcode}",
                "zipcode": zipcode
            }
        
        lat, lon = coords
        
        try:
            # SQL query to get soil properties at this location
            sql_query = f"""
            SELECT TOP 1
                mu.muname AS soil_name,
                mu.musym AS soil_symbol,
                c.compname AS component_name,
                c.taxorder AS soil_order,
                c.taxsubgrp AS soil_subgroup,
                c.drainagecl AS drainage_class,
                ch.sandtotal_r AS sand_percent,
                ch.silttotal_r AS silt_percent,
                ch.claytotal_r AS clay_percent,
                ch.ph1to1h2o_r AS ph,
                ch.om_r AS organic_matter_percent
            FROM mapunit AS mu
            INNER JOIN component AS c ON mu.mukey = c.mukey
            INNER JOIN chorizon AS ch ON c.cokey = ch.cokey
            WHERE mu.mukey IN (
                SELECT * FROM SDA_Get_Mukey_from_intersection_with_WktWgs84(
                    'point({lon} {lat})'
                )
            )
            AND c.comppct_r = (
                SELECT MAX(c2.comppct_r)
                FROM component AS c2
                WHERE c2.mukey = mu.mukey
            )
            AND ch.hzdept_r = 0
            ORDER BY c.comppct_r DESC
            """
            
            # Make POST request to SDA
            payload = {
                "query": sql_query,
                "format": "JSON"
            }
            
            response = requests.post(
                self.sda_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response - SDA returns data as list of lists
            if "Table" in data and len(data["Table"]) > 0:
                # First row contains the data
                row = data["Table"][0]
                
                # Helper function to safely convert to float
                def safe_float(value):
                    """Convert value to float, return None if not possible"""
                    if value is None or value == "None" or value == "":
                        return None
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return None
                
                # Map to column names (order matches SELECT statement)
                soil_name = row[0] if len(row) > 0 and row[0] else "Unknown"
                soil_symbol = row[1] if len(row) > 1 and row[1] else "Unknown"
                component_name = row[2] if len(row) > 2 and row[2] else "Unknown"
                soil_order = row[3] if len(row) > 3 and row[3] else "Unknown"
                soil_subgroup = row[4] if len(row) > 4 and row[4] else "Unknown"
                drainage_class = row[5] if len(row) > 5 and row[5] else "Unknown"
                
                # Convert numeric values safely
                sand = safe_float(row[6]) if len(row) > 6 else None
                silt = safe_float(row[7]) if len(row) > 7 else None
                clay = safe_float(row[8]) if len(row) > 8 else None
                ph = safe_float(row[9]) if len(row) > 9 else None
                organic_matter = safe_float(row[10]) if len(row) > 10 else None
                
                # Determine texture from percentages
                texture = self._determine_texture(clay, sand, silt)
                
                return {
                    "zipcode": zipcode,
                    "location": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "soil_properties": {
                        "soil_name": soil_name,
                        "soil_symbol": soil_symbol,
                        "component_name": component_name,
                        "soil_order": soil_order,
                        "soil_subgroup": soil_subgroup,
                        "drainage_class": drainage_class,
                        "sand_percent": round(sand, 1) if sand is not None else "Not available",
                        "silt_percent": round(silt, 1) if silt is not None else "Not available",
                        "clay_percent": round(clay, 1) if clay is not None else "Not available",
                        "soil_texture": texture,
                        "ph": round(ph, 1) if ph is not None else "Not available",
                        "organic_matter_percent": round(organic_matter, 1) if organic_matter is not None else "Not available"
                    },
                    "data_source": "USDA SSURGO via Soil Data Access"
                }
            else:
                return {
                    "zipcode": zipcode,
                    "soil_properties": {
                        "soil_name": "No detailed soil data available for this location"
                    },
                    "data_source": "USDA SSURGO via Soil Data Access",
                    "note": "This location may not have detailed SSURGO coverage"
                }
                
        except Exception as e:
            return {
                "error": f"Failed to fetch soil data: {str(e)}",
                "zipcode": zipcode
            }


    def _determine_texture(self, clay, sand, silt):
        """
        Determine USDA soil texture class from percentages
        Handles None, string, and numeric values safely
        """
        # Convert to float and handle None/invalid values
        try:
            clay = float(clay) if clay and clay != "None" else None
            sand = float(sand) if sand and sand != "None" else None
            silt = float(silt) if silt and silt != "None" else None
        except (ValueError, TypeError):
            return "Unknown"
        
        if not all([clay, sand, silt]):
            return "Unknown"
        
        # Simplified USDA texture classification
        if clay >= 40:
            return "Clay"
        elif clay >= 27:
            if sand > 45:
                return "Sandy Clay"
            else:
                return "Clay Loam"
        elif clay >= 20:
            if sand > 45:
                return "Sandy Clay Loam"
            else:
                return "Loam"
        elif sand >= 70:
            if clay >= 15:
                return "Sandy Clay Loam"
            else:
                return "Sandy Loam"
        elif silt >= 50:
            if clay < 12:
                return "Silt Loam"
            else:
                return "Silty Clay Loam"
        else:
            return "Loam"
