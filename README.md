# PDF to JSON Parser

A Python script that extracts content from PDF files and outputs it into a structured JSON format.

It supports paragraphs, tables, and charts/images, while preserving page-level hierarchy and section/sub-section organization.


## Features
- Extracts **paragraphs**, **tables**, and **charts** from PDFs.
- Maintains **page-level hierarchy**.
- Uses **font-size heuristics** to detect sections and sub-sections.
- Tables extracted with **Camelot**.
- Charts/images included with bounding boxes (`bbox`) and optional `table_data: null`.

## Dependencies

Install following python packages:
1) camelot
2) pdfplumber

run the pip command on command prompt or terminal to install the libraries.
eg. pip install camelot
