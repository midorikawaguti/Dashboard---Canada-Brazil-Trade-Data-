import pandas as pd

# ── HS2 Chapter Labels ─────────────────────────────────────────────────────────
HS2_LABELS = {
    "01": "Live Animals",
    "02": "Meat & Edible Offal",
    "03": "Fish & Seafood",
    "04": "Dairy, Eggs & Honey",
    "05": "Animal Products (Bones, Ivory, etc.)",
    "06": "Live Plants, Bulbs & Cut Flowers",
    "07": "Fresh & Frozen Vegetables",
    "08": "Fresh & Frozen Fruits",
    "09": "Coffee, Tea & Spices",
    "10": "Cereals & Grains",
    "11": "Milling Products (Flour, Starch)",
    "12": "Oil Seeds, Fodder & Industrial Plants",
    "13": "Vegetable Gums, Resins & Extracts",
    "14": "Vegetable Plaiting Materials",
    "15": "Animal & Vegetable Fats & Oils",
    "16": "Prepared Meat & Seafood",
    "17": "Sugars, Syrups & Confectionery",
    "18": "Cocoa & Chocolate Products",
    "19": "Baked Goods, Pasta & Cereals",
    "20": "Preserved Fruits & Vegetables",
    "21": "Miscellaneous Food Preparations",
    "22": "Beverages (Water, Beer, Spirits)",
    "23": "Animal Feed & Food Industry Residues",
    "24": "Tobacco & Nicotine Products",
    "25": "Salt, Cement & Construction Minerals",
    "26": "Ores & Mineral Concentrates",
    "27": "Petroleum, Fuels & Related Products",
    "28": "Inorganic Chemicals & Compounds",
    "29": "Organic Chemicals",
    "30": "Pharmaceutical Products",
    "31": "Fertilizers",
    "32": "Paints, Varnishes & Dyes",
    "33": "Cosmetics, Perfumes & Toiletries",
    "34": "Soaps, Cleaning & Polishing Prep.",
    "35": "Starches, Proteins & Adhesives",
    "36": "Explosives, Pyrotechnics & Matches",
    "37": "Photographic & Cinematographic Goods",
    "38": "Miscellaneous Chemical Products",
    "39": "Plastics & Plastic Articles",
    "40": "Rubber & Rubber Articles",
    "41": "Raw Hides, Skins & Leather",
    "42": "Leather Articles, Saddlery & Handbags",
    "43": "Furskins & Artificial Fur",
    "44": "Wood & Wood Articles",
    "45": "Cork & Cork Articles",
    "46": "Straw, Basketware & Wickerwork",
    "47": "Pulp of Wood",
    "48": "Paper & Paperboard",
    "49": "Printed Books & Newspapers",
    "50": "Silk & Silk Fabrics",
    "51": "Wool & Animal Hair Fabrics",
    "52": "Cotton & Cotton Fabrics",
    "53": "Vegetable Textile Fibres (Jute, Flax)",
    "54": "Synthetic Filaments & Fabrics",
    "55": "Synthetic & Artificial Staple Fibres",
    "56": "Wadding, Felt, Nonwovens & Special Yarns",
    "57": "Carpets & Textile Floor Coverings",
    "58": "Woven Fabrics (Pile, Tapestry, Lace)",
    "59": "Impregnated & Coated Textile Fabrics",
    "60": "Knitted & Crocheted Fabrics",
    "61": "Knitted Apparel & Clothing",
    "62": "Woven Apparel & Clothing",
    "63": "Textile Made-Up Articles & Worn Clothing",
    "64": "Footwear",
    "65": "Headgear & Hat Accessories",
    "66": "Umbrellas, Walking Sticks & Whips",
    "67": "Feathers, Artificial Flowers & Hair Articles",
    "68": "Stone, Cement & Abrasive Articles",
    "69": "Ceramic Products",
    "70": "Glass & Glassware",
    "71": "Precious Stones, Metals & Jewellery",
    "72": "Iron & Steel",
    "73": "Iron & Steel Articles",
    "74": "Copper & Copper Articles",
    "75": "Nickel & Nickel Articles",
    "76": "Aluminium & Aluminium Articles",
    "77": "Reserved for Future Use",
    "78": "Lead & Lead Articles",
    "79": "Zinc & Zinc Articles",
    "80": "Tin & Tin Articles",
    "81": "Other Base Metals & Cermets",
    "82": "Hand Tools & Cutting Tools",
    "83": "Metal Fittings, Mountings & Hardware",
    "84": "Industrial Machinery & Mechanical Equipment",
    "85": "Electrical Equipment & Electronics",
    "86": "Rail Transport Equipment",
    "87": "Motor Vehicles & Parts",
    "88": "Aircraft & Aerospace Equipment",
    "89": "Ships & Watercraft",
    "90": "Optical, Medical & Measuring Instruments",
    "91": "Clocks, Watches & Parts",
    "92": "Musical Instruments & Parts",
    "93": "Arms, Ammunition & Parts",
    "94": "Furniture, Bedding & Lighting",
    "95": "Toys, Games & Sports Equipment",
    "96": "Miscellaneous Manufactured Articles",
    "97": "Art, Antiques & Collectibles",
    "98": "Special Transactions (Repairs, Gifts)",
    "99": "Confidential & Low-Value Transactions",
}


# ── Value formatter ────────────────────────────────────────────────────────────
def fmt_value(value):
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f'${value / 1_000_000_000:.1f}B'
    elif abs_val >= 1_000_000:
        return f'${value / 1_000_000:.1f}M'
    elif abs_val >= 1_000:
        return f'${value / 1_000:.1f}K'
    else:
        return f'${value:.1f}'


# ── Shared filter function ─────────────────────────────────────────────────────
def apply_filters(df, period_range, selected_hs2, selected_province, selected_country, period_index=None, selected_trade_type=None):
    """
    Applies the four standard dropdown filters to any dataframe.
    Works with both df (has 'Year' column) and df_kpi (pre-aggregated).
    Returns a filtered copy.
    """
    filtered = df.copy()

    if period_range and period_index:
        start = period_index[period_range[0]].to_timestamp()
        end   = period_index[period_range[1]].to_timestamp() + pd.offsets.MonthEnd(0)
        filtered = filtered[
            (filtered['Period'] >= start) &
            (filtered['Period'] <= end)
        ]
    print('start-apply-filters:', period_index[period_range[0]])
    print('end-apply-filters:',   period_index[period_range[1]])

    if selected_hs2 and 'ALL' not in selected_hs2:
        filtered = filtered[filtered['HS2'].isin(selected_hs2)]

    if selected_province and 'ALL' not in selected_province:
        filtered = filtered[filtered['Province'].isin(selected_province)]

    if selected_country and 'ALL' not in selected_country:
        filtered = filtered[filtered['Country'].isin(selected_country)]

    if selected_trade_type and 'ALL' not in selected_trade_type:
        filtered = filtered[filtered['trade_type'].isin(selected_trade_type)]

    return filtered

# ── Fasted Growing Commodity ─────────────────────────────────────────────────────
def get_fastest_growing_commodity(filtered_commodity):
    """
    Compares total value per commodity between the last year
    and the previous year in the filtered data.
    Returns (name, yoy_pct) of the fastest growing commodity.
    """
    # Add year column for grouping
    df = filtered_commodity.copy()
    df['year'] = df['Period'].dt.year

    by_year = (
        df.groupby(['year', 'Commodity'], observed=True)['Value ($)']
        .sum()
        .reset_index()
    )

    years = sorted(by_year['year'].unique())

    # Need at least 2 years to compare
    if len(years) < 2:
        return None, None

    curr_year = years[-1]
    prev_year = years[-2]

    curr = by_year[by_year['year'] == curr_year].set_index('Commodity')['Value ($)']
    prev = by_year[by_year['year'] == prev_year].set_index('Commodity')['Value ($)']

    # Only compare commodities that exist in both years
    common = curr.index.intersection(prev.index)
    curr = curr.loc[common]
    prev = prev.loc[common]

    # Avoid division by zero
    prev = prev[prev > 0]
    curr = curr.loc[prev.index]

    if curr.empty:
        return None, None

    yoy = ((curr - prev) / prev * 100)
    fastest = yoy.idxmax()

    return fastest, yoy[fastest]


def get_fastest_growing_hs2(filtered_hs2, full_hs2):
    df_curr = filtered_hs2.copy()
    df_curr['year']  = df_curr['Period'].dt.year
    df_curr['month'] = df_curr['Period'].dt.month

    if df_curr.empty:
        return None, None, 'No data for selected period'

    curr = (
        df_curr
        .groupby('HS2', observed=True)['Value ($)']
        .sum()
    )
    fastest_curr = curr.idxmax()

    # Get exact year-month pairs in current selection
    current_periods = df_curr[['year', 'month']].drop_duplicates()
    current_periods = current_periods.copy()
    current_periods['prev_year'] = current_periods['year'] - 1

    # Build prior period
    df_prev = full_hs2.copy()
    df_prev['year']  = df_prev['Period'].dt.year
    df_prev['month'] = df_prev['Period'].dt.month

    prev_rows = []
    for _, row in current_periods.iterrows():
        match = df_prev[
            (df_prev['year']  == row['prev_year']) &
            (df_prev['month'] == row['month'])
        ]
        prev_rows.append(match)

    if not prev_rows:
        return fastest_curr, None, 'No data from same period prior year'

    prev_df = pd.concat(prev_rows)

    # ── Key check: all months must have prior year data ────────────────
    expected_count = len(current_periods)          # how many year-month pairs we need
    found_count = prev_df[['year', 'month']].drop_duplicates().shape[0]

    if found_count < expected_count:               # some months are missing
        return fastest_curr, None, 'No data from same period prior year'
    # ───────────────────────────────────────────────────────────────────

    if prev_df.empty:
        return fastest_curr, None, 'No data from same period prior year'

    prev = prev_df.groupby('HS2', observed=True)['Value ($)'].sum()

    common = curr.index.intersection(prev.index)
    curr   = curr.loc[common]
    prev   = prev.loc[common]
    prev   = prev[prev > 0]
    curr   = curr.loc[prev.index]

    if curr.empty:
        return fastest_curr, None, 'No data from same period prior year'

    yoy     = ((curr - prev) / prev * 100)
    fastest = yoy.idxmax()

    return fastest, yoy[fastest], None