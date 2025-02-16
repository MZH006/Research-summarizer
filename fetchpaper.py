import requests
import fitz  # PyMuPDF
import xml.etree.ElementTree as ET
from io import BytesIO
import re
import concurrent.futures

BASE_URL = "https://export.arxiv.org/api/query"

# Fetch metadata from ArXiv API
def fetch_articles(query, start=0, max_results=5):
    params = {"search_query": f"all:{query}", "start": start, "max_results": max_results}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return parse_arxiv_response(response.text)
    else:
        print(f"Error fetching articles (status {response.status_code})")
        return []

# Parse XML response
def parse_arxiv_response(xml_content):
    articles = []
    root = ET.fromstring(xml_content)
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        authors = [author.find("{http://www.w3.org/2005/Atom}name").text for author in entry.findall("{http://www.w3.org/2005/Atom}author")]
        published = entry.find("{http://www.w3.org/2005/Atom}published").text
        pdf_link = entry.find("{http://www.w3.org/2005/Atom}link").attrib['href'].replace("abs", "pdf") + ".pdf"
        articles.append({"title": title, "authors": authors, "published": published, "pdf_link": pdf_link})
    return articles

# Extract text from first 3 pages of PDF
def extract_text_from_pdf(pdf_url, max_pages=3):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        try:
            document = fitz.open(stream=BytesIO(response.content), filetype="pdf")
            text = "".join(document[page].get_text("text") for page in range(min(max_pages, len(document))))
            return clean_extracted_text(text)
        except Exception as e:
            print(f"Failed to extract text: {e}")
    else:
        print(f"Error downloading PDF (status {response.status_code})")
    return None

# Clean extracted text
def clean_extracted_text(text):
    text = re.sub(r"(?i)^(preface|acknowledgments?|references?|appendix)", "", text, flags=re.MULTILINE)
    return "\n".join([line.strip() for line in text.splitlines() if line.strip()])

# Estimate word count
def estimate_word_count(text):
    return len(text.split())

# Fetch and filter articles using parallel processing
def fetch_and_filter_articles(query, max_results=10, max_word_count=3050):
    articles = fetch_articles(query, max_results=max_results)
    filtered_articles = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(lambda article: process_article(article, max_word_count), articles)
    return [result for result in results if result]

# Process an article
def process_article(article, max_word_count):
    pdf_text = extract_text_from_pdf(article['pdf_link'])
    if pdf_text and estimate_word_count(pdf_text) <= max_word_count:
        return article
    return None
