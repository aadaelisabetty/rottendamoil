# app.py
import streamlit as st
import folium
from streamlit_folium import st_folium

# Tuodaan omat moduulimme!
import api
import database

# 1. ASETUKSET JA TIETOKANNAN ALUSTUS
st.set_page_config(page_title="Rotterdam Oil Tracker", layout="wide")
st.title("🚢 Rotterdam Oil Tanker Tracker")
st.markdown("Reaaliaikainen seuranta ja automaattinen historiadatan keräys (SQLite).")

database.init_db()

# 2. DATAN HAKU
@st.cache_data(ttl=60, show_spinner="📡 Ladataan AIS-virtaa (10s)...")
def fetch_data():
    return api.get_and_process_data()

processed_data = fetch_data()

# 3. KÄYTTÖLIITTYMÄ JA VISUALISOINTI
if not processed_data.empty:
    
    # Tallennetaan tilannekuva tietokantaan, jos on kulunut tunti
    current_ships = len(processed_data)
    current_oil = processed_data['estimated_cargo'].sum()
    database.save_snapshot_if_needed(current_ships, current_oil)
    
    st.subheader("📊 Päivän tilannekuva vs. Todellinen historiallinen keskiarvo")
    
    hist_ships, hist_oil = database.get_historical_averages()
    ship_diff_pct = ((current_ships - hist_ships) / hist_ships * 100) if hist_ships > 0 else 0
    oil_diff_pct = ((current_oil - hist_oil) / hist_oil * 100) if hist_oil > 0 else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(
            label="Tankkereita satamassa nyt", 
            value=f"{current_ships} kpl", 
            delta=f"{ship_diff_pct:.1f}% vs historia" if hist_ships > 0 else "Kerätään historiaa..."
        )
    with kpi2:
        st.metric(
            label="Arvioitu öljy satamassa (t)", 
            value=f"{current_oil:,.0f} t", 
            delta=f"{oil_diff_pct:.1f}% vs historia" if hist_oil > 0 else "Kerätään historiaa..."
        )
    with kpi3:
        max_cargo = processed_data['estimated_cargo'].max()
        st.metric(label="Suurin yksittäinen lasti (t)", value=f"{max_cargo:,.0f} t")
        
    st.divider() 

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live-kartta")
        m = folium.Map(location=[51.95, 4.10], zoom_start=11)
        for _, row in processed_data.iterrows():
            color = 'red' if row['estimated_cargo'] > (row['dwt'] * 0.7) else 'green'
            popup = f"<b>{row['vessel_name']}</b><br>Maa: {row['Country']}<br>Syväys: {row['current_draft']}m<br>Arvioitu lasti: {row['estimated_cargo']:,.0f}t"
            folium.CircleMarker(
                location=[row['lat'], row['lon']], radius=8, color=color, fill=True, popup=popup
            ).add_to(m)
        st_folium(m, width=700, height=450)

    with col2:
        st.subheader("Laivat kotimaan mukaan")
        country_counts = processed_data['Country'].value_counts()
        st.bar_chart(country_counts)
        
        st.write("Yksityiskohtainen data:")
        st.dataframe(processed_data[['vessel_name', 'Country', 'estimated_cargo']])
        
    total_db_rows = database.get_total_db_rows()
    st.caption(f"Tietokannassa on nyt {total_db_rows} historiamittausta.")

else:
    st.warning("Ei dataa. Yritä ladata sivu uudelleen.")
