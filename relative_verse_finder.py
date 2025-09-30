import argparse
import os
import pickle
import re
import urllib.request

# Constants
SCRIPTURE_URL = r'https://www.blueletterbible.org/study/parallel/paral18.cfm'


# Data processing functions
def scrape_scripture_data(url):
    """
    Scrape scripture relationship data from Blue Letter Bible website.

    Args:
        url: URL to scrape scripture relationships from

    Returns:
        str: Raw HTML content containing scripture relationships
    """
    try:
        file = urllib.request.urlopen(url)
        text = file.read().decode('utf-8')
        return text.strip()
    except Exception as e:
        raise Exception(f"Error fetching data: {e}")


def parse_html_data(html_content):
    """
    Parse HTML content to extract psalm and related scripture relationships.

    Args:
        html_content: Raw HTML string containing scripture data

    Returns:
        tuple: (psalm_chapters, related_chapters) dictionaries
               - psalm_chapters: {index: [list of psalm references]}
               - related_chapters: {index: [list of related scripture references]}

    Note: Indices correspond to matching pairs from HTML table cells.
    psalm_chapters[i] and related_chapters[i] represent related scriptures.
    """
    # Extract table cell content containing scripture lists
    psalms_list = re.findall(r'<td class="label--inline" data-label="Psalms:">(.*?)</td>', html_content, re.DOTALL)
    related_list = re.findall(r'<td class="label--inline" data-label="After What Scripture:">(.*?)</td>', html_content,
                              re.DOTALL)

    # Parse psalm references from HTML links
    psalm_chapters = {}
    for index, chapter in enumerate(psalms_list):
        psa_match = re.findall(r'<a.*?>(.*?)</a>', chapter, re.DOTALL)
        psalm_chapters[index] = ['Psa ' + num for num in psa_match]

    # Parse related scripture references from HTML links
    related_chapters = {}
    for index, chapter in enumerate(related_list):
        rel_match = re.findall(r'<a.*?>(.*?)<', chapter, re.DOTALL)
        related_chapters[index] = rel_match

    return psalm_chapters, related_chapters


def build_bidirectional_dict(psalm_chapters, related_chapters):
    """
    Build a bidirectional dictionary for fast scripture lookups.

    Args:
        psalm_chapters: Dict mapping indices to lists of psalm references
        related_chapters: Dict mapping indices to lists of related scripture references

    Returns:
        dict: Bidirectional mapping where any scripture can be a key.
              Each key maps to a list of all its related scriptures.

    Note: Creates copies of lists to avoid reference sharing issues.
    Flattens the original structure - faster O(1) lookups but loses
    the original grouping context from HTML parsing.
    """
    scripture_map = {}

    # Add psalm to related scripture mappings
    for index in psalm_chapters:
        for psa in psalm_chapters[index]:
            if psa not in scripture_map:
                scripture_map[psa] = related_chapters[index].copy()  # Copy to avoid reference issues
            else:
                scripture_map[psa].extend(related_chapters[index])

        # Add related scripture to psalm mappings (bidirectional)
        for rel in related_chapters[index]:
            if rel not in scripture_map:
                scripture_map[rel] = psalm_chapters[index].copy()  # Copy to avoid reference issues
            else:
                scripture_map[rel].extend(psalm_chapters[index])

    return scripture_map


# Utility functions
def load_or_parse_data():
    """Load scripture data from cache or parse from website if cache not found"""
    # Define cache file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_file = os.path.join(script_dir, 'scripture_cache.pkl')

    # If scripture_cache file exists, load from it
    if os.path.exists(cache_file):
        print("Loading data from cache...")
        with open(cache_file, 'rb') as f:
            psalm_chapters, related_chapters, scripture_map = pickle.load(f)
    else:
        print("Cache file not found, parsing data...")
        psalm_chapters, related_chapters, scripture_map = parse_once()
        with open(cache_file, 'wb') as f:
            pickle.dump((psalm_chapters, related_chapters, scripture_map), f)

    return psalm_chapters, related_chapters, scripture_map


def parse_once():
    """Parse the scripture data once and return the structures"""
    print("Scraping scriptures data...")
    html_content = scrape_scripture_data(SCRIPTURE_URL)
    print("Parsing HTML data...")
    psalm_chapters, related_chapters = parse_html_data(html_content)
    scripture_map = build_bidirectional_dict(psalm_chapters, related_chapters)
    return psalm_chapters, related_chapters, scripture_map


# pattern = r'([A-Za-z]+)'
# input = related_chapters
def scripture_format_validator(scripture):
    """
    Normalizes scripture reference format by standardizing capitalization and spacing.

    Args:
        scripture: Raw scripture reference string (e.g., '1 john 2', 'psa 23:1')

    Returns:
        str: Normalized scripture reference with:
            - Proper title case
            - No space between book number and name (e.g., '1John')
            - Standardized Psalm format (removes verse numbers from Psalms)

    Examples:
        >>> scripture_format_validator('1 john 2')
        '1John 2'
        >>> scripture_format_validator('psa 23:1')
        'Psa 23'
    """
    # Convert to title case and trim whitespace
    scripture = scripture.title().strip()

    # Join numeric prefix with book name (e.g., '1John' instead of '1 John')
    pattern = r"^(\d+)\s+([A-Za-z])"
    scripture = re.sub(pattern, r'\1\2', scripture)

    # Truncate book names to first 3 characters (e.g., 'Psa' for 'Psalms', '1Sa' for '1Samuel')
    pattern = r'(^[A-Za-z0-9]+)'
    scripture = re.sub(pattern, lambda m: m.group(1)[:3], scripture)

    # Remove extra spaces between book and chapter
    scripture = re.sub(r'\s+', ' ', scripture)
    scripture = re.sub(r'\s*:\s*', ':', scripture)  # Remove spaces around colon

    # Ensure input has a chapter
    pattern = r"([A-Za-z0-9]+)\s+(\d+)"
    match = re.match(pattern, scripture)
    if not match:
        raise ValueError(
            f"Invalid format: {scripture}, Expected format: 'Book Chapter' or 'Book Chapter:Verse' (e.g., 'Psa 2' or '1Sa 2:1')")

    # Remove verse numbers from Psalms (e.g., 'Psa 23' instead of 'Psa 23:1')
    pattern = r'Psa\s*(\d+).*'
    scripture = re.sub(pattern, r'Psa \1', scripture)

    return scripture


# Lookup functions
def dict_lookup(reference, scripture_map):
    """
    Fast O(1) lookup using pre-built bidirectional dictionary. If exact match is not found,
     attempt chapter-level match by removing verse numbers.

    Args:
        reference: Scripture reference to search for (e.g., 'Psa 2', 'Dan 7:28')
        scripture_map: Pre-built bidirectional dictionary from build_bidirectional_dict()

    Returns:
        list: For exact match - list of related scriptures
             For chapter match - list of all related scriptures for all matching chapter references
             Empty list if no match found

    Example:
        >>> dict_lookup('Psa 2:4', scripture_map)  # No exact match
        "Showing results for Psa 2"
        ['1Ch 14:2', 'Neh 13:2']  # Returns all references related to Psa 2
    """
    # Try exact match first for O(1) lookup
    if reference in scripture_map:
        return scripture_map[reference]

    # Try chapter-level match by removing verse number
    base_reference = reference.split(":")[0] if ":" in reference else reference
    print(f"Showing results for {base_reference}")

    # Get all references that match at chapter level
    matches = [scripture_map[key] for key in scripture_map.keys() if key.split(":")[0] == base_reference]

    if matches:
        return matches

    return []


def filter_lookup(reference, psalm_chapters, related_chapters):
    """
    Search through original parsed data structure using index-based connections.

    Args:
        reference: Scripture reference to search for
        psalm_chapters: Dict mapping indices to lists of psalm references
        related_chapters: Dict mapping indices to lists of related scripture references

    Returns:
        list: All related scripture references found across all matching groups

    Note: Preserves original HTML parsing structure and grouping context.
    Each index represents corresponding pairs from scraped table data.
    Slower O(n) lookup but maintains data integrity and original relationships.
    """
    # Find all groups containing the search text using exact match
    psalm_matches = list(filter(lambda index_psa: reference in index_psa[1], psalm_chapters.items()))
    related_matches = list(filter(lambda index_rel: reference in index_rel[1], related_chapters.items()))

    # If no exact matches, try chapter-level match by removing verse number
    if not psalm_matches and not related_matches:
        base_reference = reference.split(":")[0] if ":" in reference else reference
        print(f"Showing results for {base_reference}")
        psalm_matches = list(filter(lambda index_psa: base_reference in [psa.split(":")[0] for psa in index_psa[1]],
                                    psalm_chapters.items()))
        related_matches = list(filter(lambda index_rel: base_reference in [rel.split(":")[0] for rel in index_rel[1]],
                                      related_chapters.items()))

    all_relations = []  # Reset for each search

    # If found in psalm_chapters, get corresponding related_chapters
    if psalm_matches:
        for match in psalm_matches:
            index = match[0]  # Extract group index
            rels = related_chapters[index]  # Get relationships from same group
            all_relations.extend(rels)

    # If found in related_chapters, get corresponding psalm_chapters
    if related_matches:
        for match in related_matches:
            index = match[0]  # Extract group index
            rels = psalm_chapters[index]  # Get relationship from same group
            all_relations.extend(rels)

    return all_relations


# Interactive functions
def main():
    """Main function demonstrating both lookup methods"""
    # Configuration
    psalm_chapters, related_chapters, scripture_map = load_or_parse_data()
    test_scriptures = ['Psa 2', 'Dan 7:28', 'Rev 19:15']

    print(f"\nParsed {len(psalm_chapters)} scripture groups")
    print(f"Dictionary contains {len(scripture_map)} unique scripture references")

    # Test both lookup methods
    for reference in test_scriptures:
        print(f"\n=== Looking up: {reference} ===")

        # Method 1: Dictionary lookup (fast)
        dict_result = dict_lookup(reference, scripture_map)
        print(f"Dict lookup result ({len(dict_result)}) found: {dict_result}")

        # Method 2: Filter lookup (preserves original structure)
        filtered_result = filter_lookup(reference, psalm_chapters, related_chapters)
        print(f"Filtered lookup result ({len(filtered_result)}) found: {filtered_result}")

        # Compare results
        if set(dict_result) == set(filtered_result):
            print('Both methods returned same results')
        else:
            print("Methods returns different results")


def cli_interface():
    """
    Simple CLI interface for scripture lookups.

    Usage:
        python script.py --interactive    # Interactive mode
        python script.py "Psa 2"    # One lookup and exit
    """
    parser = argparse.ArgumentParser(description='Psalm Scripture Lookup CLI')
    parser.add_argument('--interactive', '-i', action='store_true', help='Activate interactive mode.')
    parser.add_argument('--method', '-m', choices=["dict", "filter"], default="dict",
                        help="Lookup method: dict or filter")
    parser.add_argument('scripture', metavar='scripture', nargs='?', help='Scripture to look up. e.g "Psa 2"')

    args = parser.parse_args()

    print("Loading data...")
    # Parse scripture data
    try:
        psalm_chapters, related_chapters, scripture_map = load_or_parse_data()
    except Exception as e:
        print(e)
        return

    print(f"\nParsed {len(psalm_chapters)} scripture groups")
    print(f"Dictionary contains {len(scripture_map)} unique scripture references")

    if args.interactive:
        # Interactive mode - always uses dict method
        print("\nInteractive mode (dict method). Type 'quit' to exit.")
        while True:
            # Get scripture from user and validate format
            ref = input("\nEnter scripture: ").strip()
            if ref.lower() == 'quit':
                break
            if ref:
                # Validate scripture format
                try:
                    valid_ref = scripture_format_validator(ref)
                except ValueError as e:
                    print(f"Error: {e}")
                    continue

                print(f"\n=== Looking up: {valid_ref} ===")

                # Dictionary lookup only
                result = dict_lookup(valid_ref, scripture_map)
                print(f"Dict lookup result ({len(result)}) found: {result}")
    else:
        # Single lookup with chosen method
        if not args.scripture:
            parser.error("Scripture reference required when not using --interactive mode")
            return

        # Validate scripture format
        try:
            valid_ref = scripture_format_validator(args.scripture)
        except ValueError as e:
            print(f"Error: {e}")
            return

        print(f"\n=== Looking up: {valid_ref} ===")

        # Validate scripture format
        if args.method == 'dict':
            result = dict_lookup(valid_ref, scripture_map)
            print(f"Dict lookup result ({len(result)}) found: {result}")
        else:  # filter
            result = filter_lookup(valid_ref, psalm_chapters, related_chapters)
            print(f"Filtered lookup result ({len(result)}) found: {result}")


# Entry point
if __name__ == '__main__':
    # Choose which one to run
    import sys

    if len(sys.argv) > 1:
        cli_interface()  # If args provided, run CLI
    else:
        main()
