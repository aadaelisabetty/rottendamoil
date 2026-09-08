# Rotterdam Oil Tanker Tracker (Geospatial Intelligence)

Reaaliaikainen Geospatial Intelligence (GIS) -seurantatyökalu Rotterdamin sataman öljytankkereille. Ohjelma hyödyntää maantieteellisesti rajattua WebSocket-datavirtaa, analysoi laivojen datan, arvioi lastin koon syväyksen perusteella ja ylläpitää historiallista tietokantaa trendien seurantaa varten.

## Ohjelmistoarkkitehtuuri

Projekti on rakennettu modulaariseksi (Separation of Concerns). Ydinajatuksena on tehokas paikkatietopohjainen suodatus: lataamme vain sen datan, mitä tarvitsemme.

```mermaid
graph TD
    A[Aisstream.io WebSocket API] -->|Koordinaattiraja: Bounding Box Filter| B(api.py - Paikkatietohaku)
    B -->|Jäsennelty Pandas DataFrame| C{app.py - Streamlit Pääohjelma}
    
    C -->|Tallenna tunneittain tilannekuva| D[(database.py - SQLite)]
    D -->|Hae historialliset keskiarvot ja aikasarjat| C
    
    C --> E[Folium GIS-Kartta]
    C --> F[KPI Mittaristot]
    C --> G[Trendikaaviot]
#
#Bounding box & websockets = valikoitui koska olisi liian hidasta ja kuormittavaa ladata livelaivaliikenne kaikkialta. Aisstream.io rajapinta on hyvä kun isnne voi lähettää bounding box koordinaatit, eli pakotan suodattimen datalle jo palvelimen päässä. Suojaan omaa konettani ja sen prosessoreita näin. asynciolla sitten ylläpidän yhteydet jotta reaaliaikaisuus on mahdollista
# GEOspatial: Folium ja streamliy-folium= Pelkät leveys ja pituuspiirit näyttää tyhjältä ja siksi folium + se hyödyntää leaflet.js kirjastoa joka mahdollistaa dynaamisten GIS karttojen luonnon pelkällä pYthonilla. Laivojen sijainnit ja niiden about lasketun öljylastin suoraan karttamerkkeihin joka tekee datasta heti tulkittavaa.
# datan laskenta ja prosessointi pandasilla JSON paikkatietovirta on hidasta käsitellä pelkällä Pythonin silmukoiden avulta. Pandas dataFramet mahdollistavat vektoroidut laskutoimitukset, jolloin voi yhdistää sijaintidatan ja laivojen staattiset tiedot ja sit yhdistetään se arvioidun syväyksen ja kapasiteetin perusteella.  
#Squlite3 historian vuoksi kun pelkkä karttanäkymä ei säilytä tietoa. Pyhtonissa on sisäänrakennettuna sqlite 3 iisin lokaalin anlytiikkatietokannan, se tallentaa sataman kokonaistilanteen ja vertaa sitten historialliseen keskiarvoon ilman ulkoista tietokantapalvelinta 
