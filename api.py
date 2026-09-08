# api.py
import os
import json
import time
import asyncio
import websockets
import pandas as pd
from dotenv import load_dotenv

# Ladataan API-avain heti tässä moduulissa
load_dotenv()
API_KEY = os.getenv("AIS_API_KEY")

MID_CODES = {
    '230': 'Suomi', '244': 'Alankomaat', '235': 'Iso-Britannia',
    '237': 'Kreikka', '239': 'Kreikka', '240': 'Kreikka', '241': 'Kreikka',
    '211': 'Saksa', '257': 'Norja', '258': 'Norja', '259': 'Norja',
    '351': 'Panama', '352': 'Panama', '353': 'Panama', '354': 'Panama', 
    '355': 'Panama', '356': 'Panama', '357': 'Panama', '370': 'Panama',
    '538': 'Marshallinsaaret', '636': 'Liberia', '563': 'Singapore'
}

def get_country_from_mmsi(mmsi):
    if not mmsi or len(str(mmsi)) < 3:
        return "Tuntematon"
    return MID_CODES.get(str(mmsi)[:3], f"Muu ({str(mmsi)[:3]})")

async def fetch_ais_stream(api_key, duration_seconds):
    url = "wss://stream.aisstream.io/v0/stream"
    subscription = {
        "APIKey": api_key,
        "BoundingBoxes": [[[51.85, 3.9], [52.0, 4.25]]],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
    }
    vessels = {} 
    
    try:
        async with websockets.connect(url) as websocket:
            await websocket.send(json.dumps(subscription))
            end_time = time.time() + duration_seconds
            
            # Poistettiin Streamlit-tekstit täältä, koska ne kuuluvat käyttöliittymään!
            while time.time() < end_time:
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    message = json.loads(message_str)
                    
                    mmsi = message.get("MetaData", {}).get("MMSI")
                    msg_type = message.get("MessageType")
                    
                    if mmsi and mmsi not in vessels:
                        vessels[mmsi] = {
                            "mmsi": mmsi,
                            "vessel_name": message.get("MetaData", {}).get("ShipName", "Tuntematon").strip(),
                            "lat": message.get("MetaData", {}).get("latitude", 0),
                            "lon": message.get("MetaData", {}).get("longitude", 0),
                            "current_draft": 8.0, 
                            "max_draft": 15.0,    
                            "dwt": 100000         
                        }
                    
                    if msg_type == "ShipStaticData" and mmsi in vessels:
                        static_data = message.get("Message", {}).get("ShipStaticData", {})
                        vessels[mmsi]["current_draft"] = static_data.get("MaximumStaticDraught", vessels[mmsi]["current_draft"])
                        
                except asyncio.TimeoutError:
                    continue 
            return list(vessels.values())
    except Exception as e:
        print(f"API-virhe: {e}")
        return []

def get_and_process_data():
    """Hakee datan ja prosessoi sen DataFrameksi."""
    if not API_KEY:
        return pd.DataFrame()
        
    raw_list = asyncio.run(fetch_ais_stream(API_KEY, duration_seconds=10))
    df = pd.DataFrame(raw_list)
    
    if df.empty:
        return df
        
    for col in ['current_draft', 'max_draft', 'dwt']:
        df[col] = pd.to_numeric(df[col])
        
    df['draft_ratio'] = df['current_draft'] / df['max_draft']
    df['estimated_cargo'] = df.apply(
        lambda row: row['draft_ratio'] * row['dwt'] if row['draft_ratio'] > 0.3 else 0, 
        axis=1
    )
    
    df['Country'] = df['mmsi'].apply(get_country_from_mmsi)
    return df

