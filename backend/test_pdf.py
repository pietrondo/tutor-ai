#!/usr/bin/env python3
"""
Simple test script for PDF generation functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_generator import PDFGenerator

def test_pdf_generation():
    """Test the PDF generation functionality"""
    print("Testing PDF generation...")

    try:
        # Create PDF generator
        pdf_gen = PDFGenerator()

        # Sample slide data
        test_slides = {
            "title": "Geografia Storica",
            "book_info": {
                "title": "Manuale di geografia storica",
                "author": "Autore Esempio"
            },
            "slides": [
                {
                    "slide_number": 1,
                    "title": "Introduzione alla Geografia Storica",
                    "content": [
                        "Definizione di geografia storica",
                        "Importanza dello studio delle evoluzioni territoriali",
                        "Metodologie di analisi storico-geografica",
                        "Fonti e documenti utilizzati nella ricerca"
                    ]
                },
                {
                    "slide_number": 2,
                    "title": "Concetto 1: Spazio e Tempo",
                    "content": [
                        "Relazione tra spazio geografico e tempo storico",
                        "Evoluzione dei confini territoriali",
                        "Influenza dei fattori geografici sulla storia",
                        "Esempi di cambiamenti territoriali significativi"
                    ]
                },
                {
                    "slide_number": 3,
                    "title": "Concetto 2: Cartografia Storica",
                    "content": [
                        "Sviluppo della cartografia attraverso i secoli",
                        "Tecniche di rappresentazione del territorio",
                        "Mappe antiche e loro interpretazione",
                        "Strumenti moderni per l'analisi cartografica"
                    ]
                }
            ]
        }

        # Generate PDF
        print("Generating PDF...")
        pdf_bytes = pdf_gen.generate_pdf_from_slides(test_slides)

        # Save PDF to file
        output_path = "test_geografia_storica.pdf"
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        print(f"PDF generated successfully! File saved as: {output_path}")
        print(f"PDF size: {len(pdf_bytes)} bytes")

        return True

    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    if success:
        print("\n✅ PDF generation test completed successfully!")
    else:
        print("\n❌ PDF generation test failed!")
        sys.exit(1)