import argparse
import re
import urllib.request


def scrape_scripture_data(url):
    """
    Scrape scripture relationship data from Blue Letter Bible website.

    Args:
        url: URL to scrape scripture relationships from

    Returns:
        str: Raw HTML content containing scripture relationships
    """
    file = urllib.request.urlopen(url)
    text = file.read().decode('utf-8')

    return text.strip()


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


def dict_lookup(reference, final_dict):
    """
    Fast O(1) lookup using pre-built bidirectional dictionary.

    Args:
        reference: Scripture reference to search for (e.g., 'Psa 2', 'Dan 7:28')
        final_dict: Pre-built bidirectional dictionary from build_bidirectional_dict()

    Returns:
        list: Related scripture references, or empty list if not found

    Note: Fastest lookup method but uses flattened data structure.
    """
    return final_dict.get(reference, [])


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
    # Find all groups containing the search text
    psalm_matches = list(filter(lambda index_psa: reference in index_psa[1], psalm_chapters.items()))
    related_matches = list(filter(lambda index_rel: reference in index_rel[1], related_chapters.items()))

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


def main():
    """Main function demonstrating both lookup methods"""
    # Configuration
    url = r'https://www.blueletterbible.org/study/parallel/paral18.cfm'
    test_scriptures = ['Psa 2', 'Dan 7:28', 'Rev 19:15']

    print("Scraping scriptures data...")
    html_content = scrape_scripture_data(url)

    print("Parsing scripture references...")
    psalm_chapters, related_chapters = parse_html_data(html_content)

    print("Building bidirectional dictionary...")
    scripture_map = build_bidirectional_dict(psalm_chapters, related_chapters)

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
        python script.py "Psa 2"         # One lookup and exit
    """
    parser = argparse.ArgumentParser(description='Psalm Scripture Lookup CLI')
    parser.add_argument('--interactive', '-i', action='store_true', help='Activate interactive mode.')
    parser.add_argument('--method', '-m', choices=["dict", "filter"], default="dict",
                        help="Lookup method: dict or filter")
    parser.add_argument('scripture', metavar='scripture', nargs='?', help='Scripture to look up.')

    args = parser.parse_args()

    print("Loading data...")
    url = r'https://www.blueletterbible.org/study/parallel/paral18.cfm'
    html_content = scrape_scripture_data(url)
    psalm_chapters, related_chapters = parse_html_data(html_content)
    final_dict = build_bidirectional_dict(psalm_chapters, related_chapters)

    print(f"\nParsed {len(psalm_chapters)} scripture groups")
    print(f"Dictionary contains {len(final_dict)} unique scripture references")

    if args.interactive:
        # Interactive mode - always uses dict method
        print("\nInteractive mode (dict method). Type 'quit' to exit.")
        while True:
            ref = input("\nEnter scripture: ").strip()
            if ref.lower() == 'quit':
                break
            if ref:
                print(f"\n=== Looking up: {ref} ===")

                # Dictionary lookup only
                result = dict_lookup(ref, final_dict)
                print(f"Dict lookup result ({len(result)}) found: {result}")
    else:
        # Single lookup with chosen method
        if not args.scripture:
            parser.error("Scripture reference required when not using --interactive mode")
            return

        print(f"\n=== Looking up: {args.scripture} ===")

        if args.method == 'dict':
            result = dict_lookup(args.scripture, final_dict)
            print(f"Dict lookup result ({len(result)}) found: {result}")
        else:  # filter
            result = filter_lookup(args.scripture, psalm_chapters, related_chapters)
            print(f"Filtered lookup result ({len(result)}) found: {result}")


if __name__ == '__main__':
    main()
    cli_interface()
