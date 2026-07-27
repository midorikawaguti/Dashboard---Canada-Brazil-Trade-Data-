 # Canada Trade Dashboard
 ### An interactive trade data dashboard built with Python + Plotly Dash, visualizing merchandise data of Canada's top global trading partners.

## Dashboard Structure
- Overview page — Total exports, imports, trade balance, top trading partners, province breakdown
- Products page — HS2 commodity drill-down, butterfly chart, section/HS2/commodity filters
- Commodity detail — Price trends, seasonality, export destinations, import origins, province breakdown over time
- Filters — Province, Country, Trade Type, Period slider (Jan 2024 – Dec 2025)

```text
.
├── app.py                    # App entry point
├── requirements.txt          # Python dependencies
├── dashboard/
│   ├── data.py               # Data loading + pre-aggregation
│   ├── callbacks.py          # All Dash callbacks (interactivity)
│   ├── charts.py             # Chart builder functions
│   ├── layout.py             # App layout (sidebar, filters)
│   ├── styles.py             # Colors + CSS constants
│   ├── utils.py              # Filter helpers + formatting
│   └── pages/
│       ├── overview.py       # Overview page layout
│       └── products.py       # Products page layout
└── assets/
    └── custom.css            # Custom styling
```

## Data source

### Statistics Canada — Canadian International Merchandise Trade (CIMT)

- Period: January 2024 – Dec 2025
- ~12 million rows of commodity-level trade transactions
- Provinces, countries, HS8/HS10 commodity codes, export and import values
- [View data source](https://www150.statcan.gc.ca/n1/pub/71-607-x/2021004/exp-eng.htm)

## Run it
#### Step 1: Clone the repository 
git clone https://github.com/midorikawaguti/Dashboard---Canada-Brazil-Trade-Data-.git
cd Dashboard---Canada-Brazil-Trade-Data-

#### Step 2 — Create a virtual environment
##### Mac/Linux: 
```bash
python3 -m venv .venv
source .venv/bin/activate
```

##### Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
#### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

#### Step 4 — Download the dataset
Download it from Google Drive and place it inside a Dataset/ folder:

Create the folder:
```bash
mkdir Dataset
```
Download these two files and move them into the Dataset/ folder:
- [Dataset.parquet](https://drive.google.com/file/d/1R4r91J0yXeSTOTPAl6TqU3P8l8VR-raC/view?usp=drive_link)
- [HS2_Sections_With_Descriptions.csv] (https://drive.google.com/file/d/10Lo2xZCCLgfyAq0ikJDUH2sAvbh_vdFb/view?usp=drive_link)

#### Step 5 — Run the dashboard
```bash
python app.py
```
#### Step 6 — Open in your browser

```bash
http://localhost:8050
```
