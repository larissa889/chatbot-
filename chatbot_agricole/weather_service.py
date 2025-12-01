import requests
from datetime import datetime

class WeatherService:
    """Service de récupération des données météo"""
    
    def __init__(self):
        self.api_key = "1280bad0b69086c43f7d650a09d995a3" 
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        self.forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
    
    def obtenir_meteo_actuelle(self, ville):
        """Récupère la météo actuelle pour une ville"""
        try:
            params = {
                'q': f"{ville},BF",
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'temperature': round(data['main']['temp'], 1),
                    'humidite': data['main']['humidity'],
                    'description': data['weather'][0]['description'],
                    'ville': data['name']
                }
            else:
                return None
                
        except Exception as e:
            print(f"Erreur météo : {e}")
            return None
    
    def obtenir_previsions(self, ville):
        """Récupère les prévisions sur 5 jours"""
        try:
            params = {
                'q': f"{ville},BF",
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'fr'
            }
            
            response = requests.get(self.forecast_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                previsions = []
                
                for item in data['list'][:8]: 
                    previsions.append({
                        'heure': item['dt_txt'],
                        'temperature': round(item['main']['temp'], 1),
                        'description': item['weather'][0]['description'],
                        'humidite': item['main']['humidity']
                    })
                
                return previsions
            else:
                return []
                
        except Exception as e:
            print(f"Erreur prévisions : {e}")
            return []
    
    def verifier_alertes(self, ville):
        """Vérifie s'il y a des alertes météo"""
        meteo = self.obtenir_meteo_actuelle(ville)
        alertes = []
        
        if meteo:
            # alerte sécheresse
            if meteo['humidite'] < 30:
                alertes.append("Alerte sécheresse : Humidité très faible, irrigation recommandée")
            
            # alerte température élevée
            if meteo['temperature'] > 38:
                alertes.append("🌡️ Alerte chaleur : Températures extrêmes, protégez vos cultures")
            
            # alerte pluie
            if 'pluie' in meteo['description'].lower() or 'orage' in meteo['description'].lower():
                alertes.append("🌧️ Alerte pluie : Précipitations attendues, vérifiez le drainage")
        
        return alertes