import pdfplumber
import json
import argparse
import os
from collections import defaultdict

try:
    import camelot
except ImportError:
    camelot = None


SECTION_FONT_SIZE = 14
SUBSECTION_FONT_SIZE = 12


def identify_text_role(chars):
    if not chars:
        return "paragraph"
    font_sizes = defaultdict(int)
    for ch in chars:
        font_sizes[round(ch["size"])] += 1
    dominant_size = max(font_sizes, key=font_sizes.get)
    if dominant_size >= SECTION_FONT_SIZE:
        return "section"
    elif dominant_size >= SUBSECTION_FONT_SIZE:
        return "sub_section"
    return "paragraph"


def is_number_line(text):
    clean = text.replace(" ", "").replace("-", "").replace(".", "").replace("%", "")
    return clean.isdigit()


def deduplicate_charts(charts):
    seen = set()
    unique = []
    for ch in charts:
        bbox = tuple(round(v, 1) for v in ch["bbox"])
        if bbox not in seen:
            seen.add(bbox)
            unique.append(ch)
    return unique


def extract_tables_with_camelot(pdf_path, page_number):
    if not camelot:
        return []

    try:
        tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="stream")
        extracted = []
        for t in tables:
            extracted.append(t.data)  
        return extracted
    except Exception:
        return []


def parse_pdf(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")

    final_structure = {"pages": []}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            page_content = []
            current_section = None
            current_sub_section = None

            lines = defaultdict(list)
            for ch in page.chars:
                lines[round(ch["top"])] += [ch]

            sorted_lines = sorted(lines.items())
            previous_entry = None

            for top, char_list in sorted_lines:
                line_text = "".join([c["text"] for c in char_list]).strip()
                if not line_text:
                    continue

                if line_text.isupper() and len(line_text.split()) <= 2 and len(line_text) < 15:
                    continue

                role = identify_text_role(char_list)
                if role == "section":
                    current_section = line_text
                    current_sub_section = None
                elif role == "sub_section":
                    current_sub_section = line_text

                if is_number_line(line_text) and previous_entry:
                    previous_entry["text"] += " " + line_text
                    continue

                entry = {
                    "type": "paragraph",
                    "section": current_section,
                    "sub_section": current_sub_section,
                    "text": line_text,
                    "top": top,
                }
                page_content.append(entry)
                previous_entry = entry

            camelot_tables = extract_tables_with_camelot(pdf_path, page_num)
            for tbl in camelot_tables:
                page_content.append({
                    "type": "table",
                    "section": current_section,
                    "sub_section": current_sub_section,
                    "table_data": tbl,
                    "description": None,
                    "top": None
                })

            if not camelot_tables:
                for tbl in page.extract_tables():
                    if tbl and any(any(cell for cell in row) for row in tbl):
                        page_content.append({
                            "type": "table",
                            "section": current_section,
                            "sub_section": current_sub_section,
                            "table_data": tbl,
                            "description": None,
                            "top": None
                        })

            charts = []
            for img in page.images:
                charts.append({
                    "type": "chart",
                    "section": current_section,
                    "sub_section": current_sub_section,
                    "description": f"Chart or image on page {page_num}",
                    "bbox": (img["x0"], img["top"], img["x1"], img["bottom"]),
                    "table_data": None,  
                    "top": img["top"]
                })
            charts = deduplicate_charts(charts)
            page_content.extend(charts)

            
            page_content = sorted(
                page_content,
                key=lambda x: x["top"] if isinstance(x.get("top"), (int, float)) else 1e9
            )

            final_structure["pages"].append({
                "page_number": page_num,
                "content": page_content
            })

    return final_structure


def main():
    parser = argparse.ArgumentParser(
        description="Parse a PDF into structured JSON (text, tables with Camelot, charts)."
    )
    parser.add_argument("input_pdf", help="Path to input PDF")
    parser.add_argument("output_json", help="Path to output JSON")

    args = parser.parse_args()

    try:
        print(f"Parsing '{args.input_pdf}'...")
        extracted_data = parse_pdf(args.input_pdf)

        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)

        print(f"Extracted content saved to '{args.output_json}'")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
