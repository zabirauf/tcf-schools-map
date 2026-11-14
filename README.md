# TCF Schools Map

Interactive, mobile-friendly map of all school campuses run by [The Citizens Foundation (TCF)](https://www.tcf.org.pk/our-schools/) in Pakistan.

**Open the map:** https://zabirauf.github.io/tcf-schools-map/

- Pan/zoom the map. Markers cluster when zoomed out.
- Tap a school to see its photos, district, province, level, shift, start year and coordinates, plus buttons for directions and the TCF page.
- Search by school name, city or district. Filter by province, level, shift and district.
- Use **📍 locate** and the **list** button to find the TCF schools nearest to you.
- Switch between street, satellite and OpenStreetMap layers.
- Every school has a shareable link (`#s=<id>`).

`tcf_schools.csv` holds the same data as a spreadsheet.

## Data notes
- Source: tcf.org.pk (WordPress REST API for the school list, plus each school's page for details and coordinates).
- 1,071 school records are listed. 1,058 are on the map. The other 13 are empty placeholder records with no district or location.
- 25 campuses have missing or malformed coordinates on TCF's site. They appear at their district's centre with a dashed marker and are flagged "approximate".
- Coordinates are as published by TCF. A few look misplaced relative to their listed district.

## Refreshing the data
```sh
cd scripts
python3 list.py ../data/list.json
python3 details.py ../data/list.json ../data/details.jsonl
python3 gallery.py ../data/list.json ../data/details.jsonl ../data/gallery.json
python3 build.py ../data/list.json ../data/details.jsonl ../data/gallery.json template.html vendor ../index.html
mv ../index.csv ../tcf_schools.csv
```
(`mkdir ../data` first. `details.py` appends to its output, so delete the old `details.jsonl` before a full refresh.)

Built with [Leaflet](https://leafletjs.com) and [Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster). Map tiles © Esri and © OpenStreetMap contributors. Not affiliated with TCF.
