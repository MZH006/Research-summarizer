import requests
import fitz  # PyMuPDF
import xml.etree.ElementTree as ET  # Import ElementTree for XML parsing
from io import BytesIO
import re

BASE_URL = "https://export.arxiv.org/api/query"

def fetch_articles(query, start=0, max_results=10):
    """
    Fetch metadata of articles from ArXiv API based on the search query.
    """
    params = {
        "search_query": f"all:{query}",
        "start": start,
        "max_results": max_results,
    }
    
    response = requests.get(BASE_URL, params=params)
    
    if response.status_code == 200:
        xml_content = response.text
        return parse_arxiv_response(xml_content)
    else:
        print(f"Error fetching articles (status {response.status_code})")
        return []

def parse_arxiv_response(xml_content):
    """
    Parse the XML response from ArXiv and extract article metadata.
    """
    articles = []
    root = ET.fromstring(xml_content)
    
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        authors = [author.find("{http://www.w3.org/2005/Atom}name").text for author in entry.findall("{http://www.w3.org/2005/Atom}author")]
        published = entry.find("{http://www.w3.org/2005/Atom}published").text
        pdf_link = entry.find("{http://www.w3.org/2005/Atom}link").attrib['href']
        pdf_link = pdf_link.replace("abs", "pdf") + ".pdf"
        
        article = {
            "title": title,
            "authors": authors,
            "published": published,
            "pdf_link": pdf_link,
        }
        articles.append(article)
    
    return articles

def extract_text_from_pdf(pdf_url):
    """
    Download PDF into memory and extract text from it using PyMuPDF (fitz).
    """
    response = requests.get(pdf_url)
    
    if response.status_code == 200:
        pdf_data = BytesIO(response.content)
        
        try:
            document = fitz.open(stream=pdf_data, filetype="pdf")
            text = ""
            
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text += page.get_text("text")
                
            cleaned_text = clean_extracted_text(text)
            return cleaned_text
        except Exception as e:
            print(f"Failed to extract text from PDF: {e}")
            return None
    else:
        print(f"Error downloading PDF (status code {response.status_code})")
        return None

def clean_extracted_text(text):
    """
    Clean extracted text by removing unwanted sections (headers, footers, etc.)
    """
    unwanted_patterns = [
        r"(?i)^(preface|acknowledgments?|references?|appendix)",
        r"^\s*$",
        r"\n{2,}",
        r"^\d{1,3}.*$",
    ]
    
    for pattern in unwanted_patterns:
        text = re.sub(pattern, "", text, flags=re.MULTILINE)
    
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    
    return text

def interactive_program():
    print("Welcome to the interactive ArXiv search tool!")

    # Step 1: User inputs a query
    query = input("Enter your search query: ").strip()

    # Step 2: Fetch articles
    articles = fetch_articles(query, start=0, max_results=10)
    
    if not articles:
        print("No articles found. Try a different query.")
        return
    
    # Step 3: Display the articles to the user
    print("\nHere are the top articles found:")
    for i, article in enumerate(articles, 1):
        print(f"{i}. {article['title']}")
        print(f"   Authors: {', '.join(article['authors'])}")
        print(f"   Published: {article['published']}")
        print(f"   PDF Link: {article['pdf_link']}\n")
    
    # Step 4: Let the user choose an article
    article_choice = input(f"Choose an article by number (1-{len(articles)}): ").strip()
    
    try:
        article_index = int(article_choice) - 1
        selected_article = articles[article_index]
    except (ValueError, IndexError):
        print("Invalid choice, please try again.")
        return
    
    print(f"\nYou selected: {selected_article['title']}")

    # Step 5: Extract and display text from the PDF of the selected article
    print("Extracting text from the PDF...")
    pdf_text = extract_text_from_pdf(selected_article['pdf_link'])
    
    if pdf_text:
        print("\nExtracted Text:")
        print(pdf_text[:10])  # Display only the first 500 characters of extracted text
    else:
        print("Failed to extract text from PDF.")

# Run the interactive program
if __name__ == '__main__':
    interactive_program()
