# Scripture Relationship Lookup Tool

A Python tool for finding related scripture references by scraping data from Blue Letter Bible's parallel scripture
page.

## Features

- **Two lookup methods**:
    - `dict`: Fast O(1) lookups using pre-built bidirectional dictionary
    - `filter`: Preserves original structure, slower O(n) lookups
- **Interactive mode**: Continuous scripture lookups until you quit
- **Command line mode**: Single scripture lookup and exit
- **Bidirectional relationships**: Find scriptures related to any given reference

## Installation

```bash
git clone https://github.com/yourusername/scripture-lookup-tool.git
cd scripture-lookup-tool
```

No additional dependencies required - uses only Python standard library.

## Usage

### Interactive Mode

```bash
# Interactive mode (uses dict method by default)
python relative_verse_finder.py --interactive
```

### Single Lookup

```bash
# Using dict method (default)
python relative_verse_finder.py --method dict "Psa 2"

# Using filter method  
python relative_verse_finder.py --method filter "Dan 7:28"
```

### Help

```bash
python relative_verse_finder.py --help
```

## Example Output

```
Loading data...
Scraping scriptures data...
Parsing scripture references...
Building bidirectional dictionary...

Parsed 156 scripture groups
Dictionary contains 312 unique scripture references

=== Looking up: Psa 2 ===
Dict lookup result (3) found: ['Dan 7:28', 'Rev 19:15', 'Rev 12:5']
```

## How It Works

1. **Data Source**: Scrapes scripture relationships
   from [Blue Letter Bible](https://www.blueletterbible.org/study/parallel/paral18.cfm)
2. **HTML Parsing**: Extracts psalm and related scripture references from HTML table cells
3. **Bidirectional Mapping**: Creates relationships where any scripture can find its related scriptures
4. **Two Lookup Methods**:
    - **Dict method**: Builds a complete bidirectional dictionary for fast lookups
    - **Filter method**: Searches through original parsed structure, preserving grouping context

## Code Structure

- `scrape_scripture_data()`: Downloads HTML content from Blue Letter Bible
- `parse_html_data()`: Extracts scripture references using regex
- `build_bidirectional_dict()`: Creates fast lookup dictionary
- `dict_lookup()`: Fast O(1) scripture lookup
- `filter_lookup()`: Structure-preserving O(n) lookup
- `cli_interface()`: Command line interface
- `main()`: Demonstration function with test cases

## Test Cases

The tool includes test cases for common scripture references:

- `Psa 2` → Related to Daniel 7:28, Revelation 19:15, Revelation 12:5
- `Dan 7:28` → Related to various Psalm references
- `Rev 19:15` → Related to corresponding Psalms

## Future Enhancements

- [ ] Input validation for proper scripture format
- [ ] Case-insensitive scripture matching
- [ ] Strip verse numbers (keep only book and chapter)
- [ ] More robust input cleaning and error handling
- [ ] Local caching to avoid repeated web requests
- [ ] Support for additional scripture relationship sources

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is open source. Please respect the terms of service of Blue Letter Bible when using their data.

## Disclaimer

This tool scrapes publicly available data from Blue Letter Bible. Please use responsibly and in accordance with their
terms of service.