import pytesseract
BANK_TEMPLATES = {
    "CNRB": {
        "bank_name": "Canara",
        "variants":{
            "split":{
        "amount_mode":"split",
    "columns": {
        "date": (10, 390),
        "description": (400, 1200),
        "debit": (1735, 2120),     # Withdrawals
        "credit": (1210, 1715),    # Deposits
        "balance": (2140, 2460)
    },
    "page1_start_y": 1350,        # below customer details block
    "other_pages_start_y": 250,   # below table header on page 2+
    "table_end_margin": 180       # footer + page number
},
}

    },

     "JSBL": {
         "amount_mode":"split",
    "columns": {
        "date": (209, 496),
        "description": (496, 1250),
        "debit": (1444, 1744),     # Withdrawals
        "credit": (1742, 2076),    # Deposits
        "balance": (2078, 2367)
    },
    "page1_start_y": 1350,        # below logo + address
    "other_pages_start_y": 250,   # below page header
    "table_end_margin": 250      
},
       "KKBK": {
           "bank_name": "kotak bank",
           "variants":{ 
      "merged": {         
    "amount_mode": "merged",
    "columns": {
        "date": (150, 350),
        "description": (350, 1200),
        "amount": (1500, 1950),   # Dr / Cr merged
        "balance": (1980, 2315)
    },
    "page1_start_y": 950,
    "other_pages_start_y": 150,
    "table_end_margin": 170
      },
  
    "split": {
    "amount_mode": "split",

        "columns": {
      "date": (280, 480),
      "description": (480, 1120),
       "debit": (1470, 1760),     # Withdrawal (Dr)
         "credit": (1760, 2060),    # Deposit (Cr)
        "balance": (2060, 2330)
                },

     "page1_start_y": 1180,
     "other_pages_start_y": 160,
     "table_end_margin": 250
            },

},
},
"ICICI": {
         "amount_mode":"split",
    "columns": {
       "date": (1270, 1660), 
        "description": (2060, 2765),
        "debit": (2790, 3150),
        "credit": (3150, 3510),
        "balance": (3510, 3875)
    },
    "page1_start_y": "AUTO",        # below logo + address
    "other_pages_start_y": 1,   # below page header
    "table_end_margin": 150      
},

"Phonepe": {
    "amount_mode": "merged",
    "columns": {
        "date": [80, 450], 
        "description": [450, 1600],
        "type": [1600, 1950],
        "amount": [1950, 2400]
    },
    "page1_start_y": 550,          #Adjusted to skip the full header
    "other_pages_start_y": 250,    # To skip the "Date/Details/Type/Amount" header row
    "table_end_margin": 500        # Increased to block the footer text
}
}



def get_dynamic_fallback_template(image):
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    cols = {}
    found_headers = []
    
    # NEW: Logic to find the vertical "Start Line" to skip customer details
    lowest_header_y = 0

    for i, text in enumerate(data['text']):
        word = text.upper().strip()
        if not word or int(data['conf'][i]) < 40: continue
        
        x_start = data['left'][i]
        y_top = data['top'][i]
        y_bottom = y_top + data['height'][i]

        # Identify Column Positions
        if "DATE" in word: 
            cols['date'] = (x_start - 50, x_start + 150)
            lowest_header_y = max(lowest_header_y, y_bottom)
        elif any(k in word for k in ["DETAILS", "PARTICULARS", "DESCRIPTION"]): 
            cols['description'] = (x_start - 30, x_start + 650)
            lowest_header_y = max(lowest_header_y, y_bottom)
        elif any(k in word for k in ["DEBIT", "WITHDRAW"]): 
            cols['debit'] = (x_start - 50, x_start + 150)
            found_headers.append("SPLIT")
            lowest_header_y = max(lowest_header_y, y_bottom)
        elif any(k in word for k in ["CREDIT", "DEPOSIT"]): 
            cols['credit'] = (x_start - 50, x_start + 150)
            found_headers.append("SPLIT")
            lowest_header_y = max(lowest_header_y, y_bottom)
        elif "AMOUNT" in word: 
            cols['amount'] = (x_start - 50, x_start + 250)
            lowest_header_y = max(lowest_header_y, y_bottom)
        elif "TYPE" in word: 
            cols['type'] = (x_start - 20, x_start + 150)
            found_headers.append("TYPE_COL")
            lowest_header_y = max(lowest_header_y, y_bottom)

    # Determine Mode
    if "SPLIT" in found_headers: mode = "split"
    elif "TYPE_COL" in found_headers: mode = "amount_type"
    else: mode = "merged"

    # Default safety for coordinates
    if 'date' not in cols: cols['date'] = (0, int(image.width * 0.2))
    if 'description' not in cols: cols['description'] = (int(image.width * 0.2), int(image.width * 0.7))
    
    return {
        "is_fallback": True,
        "amount_mode": mode,
        "columns": cols,
        "page1_start_y": lowest_header_y + 15 if lowest_header_y > 0 else 500,
        "other_pages_start_y": 150,
        "table_end_margin": 150
    }