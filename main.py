import os
from flask import Flask, request, render_template
import fetchpaper  
import simplify 

app = Flask(__name__)

search_results = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search_papers():
    query = request.args.get('query', '').lower()
    
    global search_results
    search_results = fetchpaper.fetch_articles(query)
    
    if not search_results:
        return render_template('results.html', query=query, results=[], message="No articles found.")
    
    return render_template('results.html', query=query, results=search_results)

@app.route('/paper/<int:paper_id>', methods=['GET'])
def view_paper(paper_id):
    if not search_results or paper_id < 0 or paper_id >= len(search_results):
        return "Paper not found", 404 

    paper = search_results[paper_id]  
    pdf_text = fetchpaper.extract_text_from_pdf(paper.get('pdf_link', ''))
    
    if pdf_text:
        keywords = ['machine learning', 'neural networks', 'AI', 'deep learning']
        simplified_text = simplify.process_article_text(pdf_text, keywords)
    else:
        simplified_text = "Failed to extract text from the selected paper."
    
    return render_template('paper.html', paper=paper, simplified_text=simplified_text)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
