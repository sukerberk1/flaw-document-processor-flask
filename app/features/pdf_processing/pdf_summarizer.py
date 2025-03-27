from typing import Dict
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize

class PdfSummarizer:
    """Summarizes text extracted from PDF files."""
    
    def __init__(self):
        # Download required NLTK resources
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
    
    def summarize(self, text: str, ratio: float = 0.3) -> Dict:
        """
        Generate a summary of the provided text.
        
        Args:
            text: The text to summarize
            ratio: The ratio of sentences to include in the summary (0.0-1.0)
            
        Returns:
            Dict containing the summary and metadata
        """
        if not text or text.isspace():
            return {"summary": "", "word_count": 0, "original_word_count": 0}
            
        # Tokenize the text into sentences
        sentences = sent_tokenize(text)
        
        if not sentences:
            return {"summary": "", "word_count": 0, "original_word_count": 0}
            
        # Calculate word frequencies
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
        
        word_frequencies = FreqDist(filtered_words)
        
        # Calculate sentence scores based on word frequencies
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            for word in word_tokenize(sentence.lower()):
                if word in word_frequencies:
                    if i in sentence_scores:
                        sentence_scores[i] += word_frequencies[word]
                    else:
                        sentence_scores[i] = word_frequencies[word]
        
        # Select top sentences
        num_sentences = max(1, int(len(sentences) * ratio))
        top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
        top_sentences = sorted(top_sentences, key=lambda x: x[0])
        
        # Create summary
        summary = " ".join([sentences[i] for i, _ in top_sentences])
        
        # Count words
        original_word_count = len(words)
        summary_word_count = len(word_tokenize(summary))
        
        return {
            "summary": summary,
            "word_count": summary_word_count,
            "original_word_count": original_word_count
        }
