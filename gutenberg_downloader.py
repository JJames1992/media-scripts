#!/usr/bin/env python3
"""
Bulk download EPUBs from Project Gutenberg and Standard Ebooks into a Calibre library.
"""
import os
import sys
import re
import time
import argparse
import subprocess
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

CALIBRE_LIBRARY = Path("/c/Users/jonat/Calibre Library")
CALIBREDB = r"C:\Program Files\Calibre2\calibredb.exe"

# Project Gutenberg categories to fetch (popular ones)
GUTENBERG_CATEGORIES = [
    "browse/scores/top",      # Top 100
    "browse/scores/top100",   # Top 100 last 30 days
    "browse/languages/en",    # English books
]

# Standard Ebooks - they have a nice API/feed
STANDARD_EBOOKS_FEED = "https://standardebooks.org/feeds/atom/new-releases"
STANDARD_EBOOKS_ALL_FEED = "https://standardebooks.org/feeds/atom/all"

def run_calibredb(args):
    """Run calibredb command."""
    cmd = [CALIBREDB] + args + ["--with-library", str(CALIBRE_LIBRARY)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def add_book_to_calibre(epub_path, metadata=None):
    """Add an EPUB to Calibre library."""
    args = ["add", str(epub_path)]
    if metadata:
        for key, value in metadata.items():
            args.extend([f"--{key}", value])
    return run_calibredb(args)

def download_file(url, dest_path):
    """Download a file with progress."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        with open(dest_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False

def fetch_gutenberg_top(limit=50):
    """Fetch top books from Project Gutenberg."""
    books = []
    url = "https://www.gutenberg.org/browse/scores/top"
    try:
        resp = requests.get(url, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Find the "Top 100 EBooks yesterday" section
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/ebooks/') and href[8:].isdigit():
                book_id = href[8:]
                title = link.get_text(strip=True)
                if title and len(title) > 3:
                    books.append({
                        'id': book_id,
                        'title': title,
                        'source': 'gutenberg',
                        'epub_url': f"https://www.gutenberg.org/ebooks/{book_id}.epub.images"
                    })
                    if len(books) >= limit:
                        break
    except Exception as e:
        print(f"Error fetching Gutenberg top: {e}")
    return books

def fetch_standard_ebooks(limit=50, feed_url=None):
    """Fetch books from Standard Ebooks."""
    if feed_url is None:
        feed_url = STANDARD_EBOOKS_FEED
    books = []
    try:
        resp = requests.get(feed_url, timeout=30)
        soup = BeautifulSoup(resp.content, 'lxml-xml')
        for entry in soup.find_all('entry')[:limit]:
            title_elem = entry.find('title')
            link_elem = entry.find('link', rel='alternate')
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                # Get the EPUB download link from the book page
                books.append({
                    'title': title,
                    'source': 'standardebooks',
                    'book_url': url
                })
    except Exception as e:
        print(f"Error fetching Standard Ebooks: {e}")
    return books

def get_standardebooks_epub(book_url):
    """Get EPUB download URL from Standard Ebooks book page."""
    metadata = {'title': None, 'author': None}
    try:
        resp = requests.get(book_url, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract title from schema:name or og:title or h1
        title_elem = (soup.find(property='schema:name') or 
                      soup.find('meta', property='og:title') or 
                      soup.find('h1'))
        if title_elem:
            if title_elem.name == 'meta':
                metadata['title'] = title_elem.get('content', '').strip()
            else:
                metadata['title'] = title_elem.get_text(strip=True)
        
        # Extract author from schema:author
        author_elem = soup.find(property='schema:author')
        if author_elem:
            name_elem = author_elem.find(property='schema:name')
            if name_elem:
                metadata['author'] = name_elem.get_text(strip=True)
        
        # Fallback: look for author link
        if not metadata['author']:
            for link in soup.find_all('a', href=True):
                if '/ebooks/' in link['href'] and link['href'].count('/') >= 3:
                    # Pattern like /ebooks/author-name/book-title
                    parts = link['href'].strip('/').split('/')
                    if len(parts) >= 2 and parts[0] == 'ebooks':
                        metadata['author'] = link.get_text(strip=True)
                        break
        
        # Look for EPUB download link (prefer the standard epub over advanced/kepub)
        epub_url = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.epub') and 'advanced' not in href and 'kepub' not in href:
                epub_url = urljoin(book_url, href)
                break
        
        if not epub_url:
            # Fallback to any epub
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.epub' in href:
                    epub_url = urljoin(book_url, href)
                    break
        
        return epub_url, metadata
    except Exception as e:
        print(f"  Error getting EPUB URL: {e}")
    return None, metadata

def main():
    parser = argparse.ArgumentParser(description="Bulk download EPUBs to Calibre")
    parser.add_argument('--gutenberg', type=int, default=50, help='Number of Gutenberg books')
    parser.add_argument('--standardebooks', type=int, default=50, help='Number of Standard Ebooks')
    parser.add_argument('--all-feed', action='store_true', help='Use the "all ebooks" feed instead of new releases')
    parser.add_argument('--dry-run', action='store_true', help='List books without downloading')
    args = parser.parse_args()

    all_books = []

    print(f"Fetching {args.gutenberg} books from Project Gutenberg...")
    gutenberg_books = fetch_gutenberg_top(args.gutenberg)
    all_books.extend(gutenberg_books)
    print(f"  Found {len(gutenberg_books)} books")

    se_feed = STANDARD_EBOOKS_ALL_FEED if args.all_feed else STANDARD_EBOOKS_FEED
    feed_name = "all ebooks" if args.all_feed else "new releases"
    print(f"Fetching {args.standardebooks} books from Standard Ebooks ({feed_name})...")
    se_books = fetch_standard_ebooks(args.standardebooks, feed_url=se_feed)
    all_books.extend(se_books)
    print(f"  Found {len(se_books)} books")

    if args.dry_run:
        for book in all_books:
            print(f"  [{book['source']}] {book['title']}")
        return

    # Download and add to Calibre
    temp_dir = Path(os.environ.get('TEMP', '/tmp')) / "calibre_imports"
    temp_dir.mkdir(exist_ok=True)

    for i, book in enumerate(all_books, 1):
        print(f"\n[{i}/{len(all_books)}] {book['title']} ({book['source']})")

        if book['source'] == 'gutenberg':
            epub_url = book['epub_url']
            epub_path = temp_dir / f"gutenberg_{book['id']}.epub"
            metadata = {}
        else:
            epub_url, se_metadata = get_standardebooks_epub(book['book_url'])
            if not epub_url:
                print("  Could not find EPUB URL")
                continue
            # Use extracted metadata if available
            title = se_metadata.get('title') or book['title']
            author = se_metadata.get('author')
            safe_title = re.sub(r'[^\w\s-]', '', title)[:50]
            epub_path = temp_dir / f"se_{safe_title}.epub"
            metadata = {}
            if title:
                metadata['title'] = title
            if author:
                metadata['authors'] = author

        print(f"  Downloading...")
        if download_file(epub_url, epub_path):
            print(f"  Adding to Calibre...")
            success, out, err = add_book_to_calibre(epub_path, metadata)
            if success:
                print(f"  ✓ Added")
            else:
                print(f"  ✗ Failed: {err}")
            # Clean up
            epub_path.unlink(missing_ok=True)
        else:
            print(f"  ✗ Download failed")

        time.sleep(1)  # Be polite

    print("\nDone!")

if __name__ == "__main__":
    main()