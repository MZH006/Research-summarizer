import spacy
import wikipedia
from transformers import pipeline
from transformers import T5Tokenizer
import tensorflow as tf
tf.config.set_visible_devices([], 'GPU')  

nlp = spacy.load("en_core_web_sm")


summarizer = pipeline("summarization", model="t5-small", device=0)  

tokenizer = T5Tokenizer.from_pretrained("t5-small")

def summarize_text_advanced(text):
    input_tokens = tokenizer.encode(text, truncation=True, max_length=512)
    if len(input_tokens) > 512:
        print(f"Warning: The chunk exceeds the token limit ({len(input_tokens)} tokens). It will be truncated.")
    
    max_length = min(200, len(text) // 2)  # Increase max_length for larger summaries
    min_length = max(50, max_length // 2)  # Keep min_length smaller than max_length
    
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]['summary_text']

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


keywords = ['machine learning', 'neural networks', 'AI', 'deep learning']
def add_hyperlinks(text, keywords):
    hyperlinked_terms = set()
    
    doc = nlp(text)
    for token in doc:

        if token.text.lower() in keywords and token.text not in hyperlinked_terms:
            link = get_wikipedia_link(token.text)
            if link:
                hyperlink = f' <a href="{link}" target="_blank" style="color:blue;">[Learn more]</a>'
                text = text.replace(token.text, token.text + hyperlink, 1)
                hyperlinked_terms.add(token.text)
    return text

def split_text_into_chunks(text, max_tokens=300, max_words=2500):  
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    
    chunks = []
    current_chunk = ""
    current_token_count = 0
    current_word_count = 0
    
    for sentence in sentences:
        sentence_tokens = tokenizer.encode(sentence, truncation=True, max_length=512)
        sentence_token_count = len(sentence_tokens)
        sentence_word_count = len(sentence.split())
        
        if current_token_count + sentence_token_count <= max_tokens and current_word_count + sentence_word_count <= max_words:
            current_chunk += sentence + " "
            current_token_count += sentence_token_count
            current_word_count += sentence_word_count
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            current_token_count = sentence_token_count
            current_word_count = sentence_word_count
        
        if current_word_count >= max_words:
            break
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_article_text(text, keywords, max_words=4000):
    print("Starting text processing...")  
    
    chunks = split_text_into_chunks(text, max_tokens=500, max_words=max_words)
    
    summarized_text = ""
    for chunk in chunks:
        print(f"Summarizing chunk: {chunk[:100]}...")  
        summarized_text += summarize_text_advanced(chunk) + " "
    

    final_output = add_hyperlinks(summarized_text, keywords)
    
    print(f"Processed Text: {final_output[:500]}...")  
    
    return final_output
