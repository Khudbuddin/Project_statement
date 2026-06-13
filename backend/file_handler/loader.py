import os
import pandas as pd
from .pdf_load import load_pdf
from .csv_load import load_csv

def load_file(file_path, password=None):
    ext = os.path.splitext(file_path)[1].lower()
    
    # Routing based on extension
    if ext == '.csv': 
        return load_csv(file_path)
    elif ext == '.pdf': 
        return load_pdf(file_path, password)
  