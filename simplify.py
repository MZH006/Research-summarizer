import spacy
import wikipedia
from transformers import pipeline
from transformers import T5Tokenizer
import tensorflow as tf
tf.config.set_visible_devices([], 'GPU')  # Force TensorFlow to use CPU

# Load the NLP model (spaCy)
nlp = spacy.load("en_core_web_sm")

# Load the summarizer model from HuggingFace (use GPU if available)
summarizer = pipeline("summarization", model="t5-small", device=0)  # Using t5-small instead of distil-t5

# Initialize T5 tokenizer to count tokens more accurately
tokenizer = T5Tokenizer.from_pretrained("t5-small")

# Function to summarize text using Hugging Face (Abstractive summarization)
def summarize_text_advanced(text):
    # Tokenize the text to count tokens and ensure the model's token limit is not exceeded
    input_tokens = tokenizer.encode(text, truncation=True, max_length=512)
    if len(input_tokens) > 512:
        print(f"Warning: The chunk exceeds the token limit ({len(input_tokens)} tokens). It will be truncated.")
    
    # Now summarizing the text using the chunk that fits within the token limit
    max_length = min(200, len(text) // 2)  # Increase max_length for larger summaries
    min_length = max(50, max_length // 2)  # Keep min_length smaller than max_length
    
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']

# Function to get dynamic links from Wikipedia for a given term
def get_wikipedia_link(term):
    try:
        page = wikipedia.page(term)
        return page.url
    except wikipedia.exceptions.DisambiguationError as e:
        return wikipedia.page(e.options[0]).url
    except wikipedia.exceptions.PageError:
        return None
    except wikipedia.exceptions.RedirectError:
        return None
    except wikipedia.exceptions.HTTPTimeoutError:
        return None

# Function to add hyperlinks to key terms dynamically
keywords = ['machine learning', 'neural networks', 'AI', 'deep learning']
def add_hyperlinks(text, keywords):
    hyperlinked_terms = set()
    
    doc = nlp(text)
    for token in doc:
        # Only add hyperlink if the token matches a keyword
        if token.text.lower() in keywords and token.text not in hyperlinked_terms:
            link = get_wikipedia_link(token.text)
            if link:
                hyperlink = f' <a href="{link}" target="_blank" style="color:blue;">[Learn more]</a>'
                text = text.replace(token.text, token.text + hyperlink, 1)
                hyperlinked_terms.add(token.text)
    return text

# Function to split text into smaller chunks based on token length and word limit
def split_text_into_chunks(text, max_tokens=300, max_words=2500):  
    # Tokenize the text and split accordingly
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    chunks = []
    current_chunk = ""
    current_token_count = 0
    current_word_count = 0
    
    for sentence in sentences:
        # Count tokens in the sentence
        sentence_tokens = tokenizer.encode(sentence, truncation=True, max_length=512)
        sentence_token_count = len(sentence_tokens)
        sentence_word_count = len(sentence.split())
        
        # If adding the sentence would exceed max_tokens or max_words, start a new chunk
        if current_token_count + sentence_token_count <= max_tokens and current_word_count + sentence_word_count <= max_words:
            current_chunk += sentence + " "
            current_token_count += sentence_token_count
            current_word_count += sentence_word_count
        else:
            # Add the current chunk and reset for the next one
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            current_token_count = sentence_token_count
            current_word_count = sentence_word_count
        
        # If the total word count exceeds the max limit, stop
        if current_word_count >= max_words:
            break
    
    # Add any remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

# Function to process the article text: summarize and add hyperlinks
def process_article_text(text, keywords, max_words=4000):
    print("Starting text processing...")  # Debug print
    
    # Split text into smaller chunks for summarization
    chunks = split_text_into_chunks(text, max_tokens=500, max_words=max_words)
    
    summarized_text = ""
    for chunk in chunks:
        print(f"Summarizing chunk: {chunk[:100]}...")  # Debug first 100 characters of chunk
        summarized_text += summarize_text_advanced(chunk) + " "
    
    # Add hyperlinks to key terms
    final_output = add_hyperlinks(summarized_text, keywords)
    
    print(f"Processed Text: {final_output[:500]}...")  # Debug first 500 characters of final output
    
    return final_output
