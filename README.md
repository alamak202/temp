# PDF Redaction Script

A command-line Python script that performs **true redaction** on PDF files using PyMuPDF (fitz). This tool permanently removes content (text, images, vector graphics) within specified coordinates, ensuring sensitive information cannot be recovered.

## Features

- **True Redaction**: Permanently removes content, not just covers it
- **Two Redaction Modes**:
  - `mask`: Replaces content with a solid black box
  - `substitute`: Replaces content with custom text (e.g., "[REDACTED]", "XXX")
- **JSON Configuration**: Define multiple redactions across different pages
- **Command-Line Interface**: Easy to use and automate
- **Batch Processing**: Apply multiple redactions in a single operation

## Installation

1. Ensure you have Python 3.6 or higher installed:
   ```bash
   python --version
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Command

```bash
python redact.py -i original.pdf -o redacted.pdf -c config.json
```

### Command-Line Arguments

- `-i, --input`: Path to the input PDF file (required)
- `-o, --output`: Path to save the redacted PDF file (required)
- `-c, --config`: Path to the JSON configuration file (required)

### Configuration File Format

The configuration file is a JSON array containing redaction instructions. Each redaction object must specify:

- `page`: The 0-based page number (0 = first page)
- `coords`: An array of four numbers `[x0, y0, x1, y1]` representing the bounding box in PDF points (1/72 inch)
  - `x0, y0`: Top-left corner coordinates
  - `x1, y1`: Bottom-right corner coordinates
- `mode`: Either `"mask"` or `"substitute"`
- `text`: (Optional) Replacement text for `"substitute"` mode. Defaults to "XXX" if not specified

### Example Configuration

See `config.example.json`:

```json
[
  {
    "page": 0,
    "coords": [50, 50, 200, 100],
    "mode": "mask"
  },
  {
    "page": 1,
    "coords": [72, 120, 300, 150],
    "mode": "substitute",
    "text": "[REDACTED]"
  },
  {
    "page": 1,
    "coords": [72, 180, 300, 210],
    "mode": "substitute"
  }
]
```

This example:
- Applies a black box redaction on page 1 (0-indexed) at coordinates [50, 50, 200, 100]
- Substitutes content on page 2 at [72, 120, 300, 150] with "[REDACTED]"
- Substitutes content on page 2 at [72, 180, 300, 210] with "XXX" (default)

## How to Find Coordinates

PDF coordinates start at the bottom-left corner of the page, but PyMuPDF uses top-left. To find the coordinates for redaction:

1. **Manual Method**: Open the PDF in a viewer that shows cursor coordinates (e.g., Adobe Acrobat Pro)
2. **PyMuPDF Method**: Use PyMuPDF to search for text and get its bounding box:
   ```python
   import fitz
   doc = fitz.open("document.pdf")
   page = doc[0]
   text_instances = page.search_for("sensitive text")
   print(text_instances)  # Returns list of rectangles
   ```

## Important Notes

- **Irreversible Operation**: Once redactions are applied, the original content cannot be recovered
- **Test First**: Always test on a copy of your document before processing originals
- **Coordinate System**: PDF points are 1/72 inch (approximately 0.35 mm)
- **Validation**: The script validates all configuration entries before applying any redactions

## Example Workflow

1. Create a copy of your sensitive PDF:
   ```bash
   cp sensitive_document.pdf test_document.pdf
   ```

2. Create your redaction configuration (use `config.example.json` as a template):
   ```bash
   cp config.example.json my_redactions.json
   # Edit my_redactions.json with your specific coordinates
   ```

3. Run the redaction script:
   ```bash
   python redact.py -i test_document.pdf -o redacted_test.pdf -c my_redactions.json
   ```

4. Verify the output in `redacted_test.pdf`

5. Once satisfied, process the original:
   ```bash
   python redact.py -i sensitive_document.pdf -o secure_document.pdf -c my_redactions.json
   ```

## Error Handling

The script includes comprehensive error handling for:
- Missing or invalid input files
- Malformed JSON configuration
- Invalid page numbers or coordinates
- Missing required fields

All errors will display clear messages and exit gracefully.

## Security Considerations

- This script performs **true redaction** by permanently removing content from the PDF structure
- Unlike simple "blacking out" with annotations, redacted content cannot be recovered by removing layers
- Always verify redacted PDFs before distribution
- Consider additional security measures for highly sensitive documents (encryption, secure deletion of originals)

## License

This script is provided as-is for educational and professional use.

## Requirements

- Python 3.6+
- PyMuPDF (fitz) 1.23.0 or higher
