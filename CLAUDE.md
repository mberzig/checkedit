# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChequEdit is a Python tool for generating and printing bank cheques (checks). It creates PDFs with amounts in both digits and letters (French), formatted for Algerian Dinars (DA), ready to print on A4 paper with a physical cheque positioned on it.

## Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate a single cheque
python cheque_printer.py -m 1500000 -o "Bénéficiaire" -l Alger --ouvrir

# Interactive mode
python cheque_printer.py --interactif

# Batch import from CSV
python cheque_printer.py --csv cheques.csv

# Generate calibration page
python cheque_printer.py --calibration

# Create example CSV
python cheque_printer.py --exemple-csv
```

## Architecture

Single-file application (`cheque_printer.py`) with one main class:

- **`ChequePrinter`**: Core class handling PDF generation via ReportLab
  - `POSITIONS`: Dict defining x/y coordinates (in mm) for each cheque field
  - `CHEQUE_OFFSET`: Position of cheque on A4 page
  - `nombre_en_lettres()`: Converts numbers to French words (handles millions, accords grammaticaux)
  - `_formater_montant()`: Formats amount with thousand separators (spaces) and DA symbol
  - `generer_cheque()`: Creates PDF with all fields positioned
  - `calibration_page()`: Generates alignment grid with tape zones and L-guides

- **Standalone functions**: `mode_interactif()`, `importer_csv()`, `creer_csv_exemple()`, `main()`

## Key Configuration

Positions are in millimeters from bottom-left corner of cheque area. Adjust these constants in `ChequePrinter` class for different cheque models:

```python
POSITIONS = {
    'montant_chiffres': {'x': 165, 'y': 75},
    'montant_lettres_ligne1': {'x': 25, 'y': 62},
    'montant_lettres_ligne2': {'x': 25, 'y': 55},
    'ordre': {'x': 45, 'y': 48},
    'lieu': {'x': 130, 'y': 35},
    'date': {'x': 155, 'y': 35},
}
CHEQUE_OFFSET = {'x': 10, 'y': 180}
```

## CSV Format

Semicolon-delimited (`;`) with comma as decimal separator:
```
montant;ordre;lieu;date
1250000,50;Sonatrach;Alger;07/01/2026
```
