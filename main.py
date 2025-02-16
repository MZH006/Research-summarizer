from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

papers = []

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search_papers():
    query = request.args.get('query', '').lower()
    results = []

    for paper in papers:
        if query in paper['title'].lower() or query in paper['abstract'].lower():
            results.append(paper)
    
    return render_template('results.html', query=query, results=results)

@app.route('/paper/<int:paper_id>', methods=['GET'])
def view_paper(paper_id):
    # Find the paper by its ID
    paper = next((p for p in papers if p["id"] == paper_id), None)
    
    if paper is None:
        return "Paper not found", 404
    
    summary = f"This paper discusses the main ideas of {paper['title']}. It focuses on key points such as [insert simplified points here]."

    return render_template('paper.html', paper=paper, summary=summary)

if __name__ == "__main__":
    app.run(debug=True)
