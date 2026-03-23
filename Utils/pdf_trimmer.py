import argparse
import sys
import os

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Error: The 'pypdf' library is not installed.")
    print("Please install it by running: pip install pypdf")
    sys.exit(1)


def parse_page_ranges(page_str: str) -> set:
    """
    Parses a string like '3 5-7' or '3,5,8' into a set of 0-indexed page numbers.
    """
    pages_to_drop = set()
    if not page_str:
        return pages_to_drop
    
    # Standardize delimiters: replace commas with spaces
    parts = page_str.replace(",", " ").split()
    for part in parts:
        try:
            if "-" in part:
                start, end = part.split("-")
                # users provide 1-indexed pages, convert to 0-indexed
                pages_to_drop.update(range(int(start) - 1, int(end)))
            else:
                pages_to_drop.add(int(part) - 1)
        except ValueError:
            print(f"Warning: Could not parse page identifier '{part}'. Format should be a number or range (e.g. '5' or '5-7').")
            
    return set(pages_to_drop)


def trim_pdf(input_path: str, output_path: str, drop_front: int = 0, drop_back: int = 0, drop_pages: str = ""):
    """
    Removes the specified number of pages from the beginning, end, and specific pages of a PDF.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        sys.exit(1)

    print(f"Reading '{input_path}'...")
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    total_pages = len(reader.pages)
    
    start_idx = drop_front
    end_idx = total_pages - drop_back
    specific_drops = parse_page_ranges(drop_pages)
    
    # Validation
    if start_idx >= end_idx or start_idx >= total_pages or end_idx <= 0:
        print(f"Error: Cannot drop {drop_front} front and {drop_back} back pages from a {total_pages}-page PDF.")
        print("The resulting PDF would have 0 or negative pages from front/back trimming alone.")
        sys.exit(1)
        
    pages_added = 0
    dropped_specifics = []
    
    # Add the remaining pages to the new PDF
    for i in range(total_pages):
        if i < start_idx:
            continue
        if i >= end_idx:
            continue
        if i in specific_drops:
            dropped_specifics.append(i + 1) # 1-indexed for logging
            continue
            
        writer.add_page(reader.pages[i])
        pages_added += 1
        
    if pages_added == 0:
        print("Error: All pages were dropped. Resulting PDF would be empty.")
        sys.exit(1)
        
    # Write the output file
    with open(output_path, "wb") as out_file:
        writer.write(out_file)
        
    print("\n✅ Success!")
    print(f"Original pages: {total_pages}")
    print(f"Pages removed from front: {drop_front}")
    print(f"Pages removed from back:  {drop_back}")
    
    if dropped_specifics:
        print(f"Specific pages removed:   {', '.join(map(str, sorted(dropped_specifics)))}")
        
    print(f"New page count: {pages_added}")
    print(f"Saved to:       {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Trim pages from the start, end, or specific interior pages of a PDF file.")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("-o", "--output", help="Path to the output PDF file (default: input_trimmed.pdf)")
    parser.add_argument("-f", "--front", type=int, default=0, help="Number of pages to delete from the front (default: 0)")
    parser.add_argument("-b", "--back", type=int, default=0, help="Number of pages to delete from the back (default: 0)")
    parser.add_argument("-d", "--drop", type=str, default="", help="Specific pages to drop, formatted like '3 5-7' or '3,5,8'")

    args = parser.parse_args()

    input_pdf = args.input
    output_pdf = args.output
    
    # Generate default output name if none provided
    if not output_pdf:
        base, ext = os.path.splitext(input_pdf)
        output_pdf = f"{base}_trimmed{ext}"

    trim_pdf(input_pdf, output_pdf, drop_front=args.front, drop_back=args.back, drop_pages=args.drop)


if __name__ == "__main__":
    main()
