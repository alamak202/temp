#!/usr/bin/env python3
"""
PDF Redaction Script
Performs true redaction on PDF files using PyMuPDF (fitz).
"""

import argparse
import json
import sys
import fitz  # PyMuPDF


def load_config(config_path):
    """Load and validate the redaction configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)

        if not isinstance(config, list):
            print("Error: Config file must contain a JSON array of redaction objects.")
            sys.exit(1)

        return config
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)


def validate_redaction(redaction, index):
    """Validate a single redaction configuration."""
    required_fields = ['page', 'coords', 'mode']

    for field in required_fields:
        if field not in redaction:
            print(f"Error: Redaction {index} missing required field: {field}")
            return False

    if not isinstance(redaction['page'], int) or redaction['page'] < 0:
        print(f"Error: Redaction {index} has invalid page number (must be non-negative integer)")
        return False

    if not isinstance(redaction['coords'], list) or len(redaction['coords']) != 4:
        print(f"Error: Redaction {index} has invalid coords (must be array of 4 numbers)")
        return False

    # Validate normalized coordinates if specified
    is_normalized = redaction.get('normalized', False)
    if is_normalized:
        for i, coord in enumerate(redaction['coords']):
            if not isinstance(coord, (int, float)) or not (0 <= coord <= 1):
                print(f"Error: Redaction {index} has invalid normalized coord at index {i} (must be between 0 and 1)")
                return False

    if redaction['mode'] not in ['mask', 'substitute']:
        print(f"Error: Redaction {index} has invalid mode (must be 'mask' or 'substitute')")
        return False

    return True


def apply_redaction(page, redaction):
    """Apply a single redaction to a page."""
    coords = redaction['coords']
    mode = redaction['mode']
    is_normalized = redaction.get('normalized', False)

    # Convert normalized coordinates to absolute coordinates if needed
    if is_normalized:
        page_rect = page.rect  # Get page dimensions
        page_width = page_rect.width
        page_height = page_rect.height

        # Convert normalized coords (0-1) to absolute coords
        abs_coords = [
            coords[0] * page_width,   # x0
            coords[1] * page_height,  # y0
            coords[2] * page_width,   # x1
            coords[3] * page_height   # y1
        ]
        coords = abs_coords

    # Create the rectangle for redaction (x0, y0, x1, y1)
    rect = fitz.Rect(coords[0], coords[1], coords[2], coords[3])

    if mode == 'mask':
        # Black box redaction
        page.add_redact_annot(rect, fill=(0, 0, 0))

    elif mode == 'substitute':
        # Text substitution redaction
        text = redaction.get('text', 'XXX')  # Default to 'XXX' if not specified
        page.add_redact_annot(rect, text=text, fill=(1, 1, 1), text_color=(0, 0, 0))


def redact_pdf(input_path, output_path, config):
    """Main redaction function."""
    try:
        # Open the PDF document
        doc = fitz.open(input_path)
        print(f"Opened PDF: {input_path}")
        print(f"Total pages: {doc.page_count}")

        # Track which pages have redactions
        redacted_pages = set()

        # Apply all redaction annotations
        for index, redaction in enumerate(config):
            if not validate_redaction(redaction, index):
                doc.close()
                sys.exit(1)

            page_num = redaction['page']

            # Check if page exists
            if page_num >= doc.page_count:
                print(f"Warning: Redaction {index} targets page {page_num}, but PDF only has {doc.page_count} pages. Skipping.")
                continue

            page = doc[page_num]
            apply_redaction(page, redaction)
            redacted_pages.add(page_num)

            mode_desc = redaction['mode']
            if redaction['mode'] == 'substitute':
                mode_desc += f" (text: '{redaction.get('text', 'XXX')}')"

            coord_type = "normalized" if redaction.get('normalized', False) else "absolute"
            print(f"  Added redaction {index + 1}: Page {page_num}, coords {redaction['coords']} ({coord_type}), mode: {mode_desc}")

        # Apply all redactions (this is the irreversible step)
        print("\nApplying redactions (permanently removing content)...")
        for page_num in sorted(redacted_pages):
            page = doc[page_num]
            page.apply_redactions()

        # Save the redacted PDF
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()

        print(f"\nSuccessfully redacted PDF and saved to: {output_path}")
        print(f"Total redactions applied: {len(config)}")

    except FileNotFoundError:
        print(f"Error: Input PDF file not found: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)


def main():
    """Parse arguments and execute redaction."""
    parser = argparse.ArgumentParser(
        description='Perform true redaction on PDF files using PyMuPDF.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python redact.py -i original.pdf -o redacted.pdf -c config.json
  python redact.py --input document.pdf --output secure.pdf --config redactions.json
        """
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        help='Path to the input PDF file'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to save the redacted PDF file'
    )

    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Path to the JSON configuration file containing redaction instructions'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Perform redaction
    redact_pdf(args.input, args.output, config)


if __name__ == '__main__':
    main()
