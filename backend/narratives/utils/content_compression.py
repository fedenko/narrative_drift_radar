"""
Content compression utilities for cost-efficient LLM processing.
Implements medoid detection, TextRank, TF-IDF, and NER for reducing token usage.
"""
import numpy as np
import hashlib
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Any, Optional

# Optional dependency - use fallback if not available
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False


class ContentCompressor:
    """
    Compresses article content for efficient LLM processing.
    
    Features:
    - Medoid detection for cluster representatives
    - TextRank for key sentence extraction
    - TF-IDF for important terms
    - Basic NER for entities
    - Content deduplication
    """
    
    def __init__(self, language='uk'):
        self.language = language
        self.tfidf_vectorizer = None
        self.stop_words = self._get_stop_words(language)
    
    def _get_stop_words(self, language):
        """Get stop words for specified language."""
        if language == 'uk':
            return {
                'і', 'в', 'на', 'з', 'до', 'за', 'під', 'над', 'між', 'про', 'для',
                'від', 'при', 'по', 'у', 'та', 'або', 'але', 'а', 'чи', 'не', 'ні',
                'що', 'який', 'яка', 'яке', 'які', 'хто', 'де', 'коли', 'як', 'чому',
                'це', 'той', 'та', 'те', 'ті', 'він', 'вона', 'воно', 'вони', 'я',
                'ти', 'ми', 'ви', 'мій', 'твій', 'його', 'її', 'наш', 'ваш', 'їх',
                'є', 'був', 'була', 'було', 'були', 'буде', 'будуть', 'мати', 'має',
                'мав', 'мала', 'мало', 'мали', 'можна', 'треба', 'потрібно'
            }
        else:  # English fallback
            return {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
            }
    
    def find_medoids(self, embeddings: np.ndarray, articles: List[Any], 
                     max_medoids: int = 3) -> List[int]:
        """
        Find medoids (most representative articles) in cluster.
        
        Args:
            embeddings: Article embeddings array
            articles: List of article objects
            max_medoids: Maximum number of medoids to return
            
        Returns:
            List of indices of medoid articles
        """
        if len(embeddings) <= max_medoids:
            return list(range(len(embeddings)))
        
        # Calculate pairwise distances
        similarities = cosine_similarity(embeddings)
        distances = 1 - similarities
        
        # Find articles with minimum average distance to others
        avg_distances = np.mean(distances, axis=1)
        medoid_indices = np.argsort(avg_distances)[:max_medoids]
        
        return medoid_indices.tolist()
    
    def extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        return sentences
    
    def textrank_sentences(self, sentences: List[str], max_sentences: int = 8) -> List[str]:
        """
        Extract key sentences using TextRank algorithm.
        
        Args:
            sentences: List of sentences
            max_sentences: Maximum sentences to return
            
        Returns:
            List of most important sentences
        """
        if len(sentences) <= max_sentences:
            return sentences
        
        # Try TextRank with NetworkX if available
        if HAS_NETWORKX:
            try:
                return self._textrank_with_networkx(sentences, max_sentences)
            except Exception:
                pass  # Fall through to simple fallback
        
        # Fallback: TF-IDF based sentence ranking
        return self._simple_sentence_ranking(sentences, max_sentences)
    
    def _textrank_with_networkx(self, sentences: List[str], max_sentences: int) -> List[str]:
        """TextRank implementation using NetworkX."""
        stop_words = list(self.stop_words) if self.language == 'uk' else 'english'
        vectorizer = TfidfVectorizer(stop_words=stop_words, lowercase=True)
        tfidf_matrix = vectorizer.fit_transform(sentences)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Create graph
        nx_graph = nx.from_numpy_array(similarity_matrix)
        
        # Calculate PageRank scores
        scores = nx.pagerank(nx_graph)
        
        # Sort sentences by score
        ranked_sentences = sorted(
            [(score, sentence) for sentence, score in 
             zip(sentences, scores.values())], 
            reverse=True
        )
        
        return [sentence for _, sentence in ranked_sentences[:max_sentences]]
    
    def _simple_sentence_ranking(self, sentences: List[str], max_sentences: int) -> List[str]:
        """Simple sentence ranking based on TF-IDF scores."""
        try:
            stop_words = list(self.stop_words) if self.language == 'uk' else 'english'
            vectorizer = TfidfVectorizer(stop_words=stop_words, lowercase=True)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # Calculate sentence importance as sum of TF-IDF scores
            sentence_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
            
            # Get top sentences
            top_indices = np.argsort(sentence_scores)[-max_sentences:][::-1]
            
            return [sentences[i] for i in top_indices]
            
        except Exception:
            # Final fallback: return first sentences
            return sentences[:max_sentences]
    
    def extract_key_terms(self, texts: List[str], max_terms: int = 15) -> List[str]:
        """
        Extract key terms using TF-IDF.
        
        Args:
            texts: List of texts to analyze
            max_terms: Maximum terms to return
            
        Returns:
            List of important terms
        """
        try:
            # Combine texts
            combined_text = ' '.join(texts)
            
            # Create TF-IDF vectorizer
            stop_words = list(self.stop_words) if self.language == 'uk' else 'english'
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=stop_words,
                ngram_range=(1, 2),  # Include bigrams
                min_df=1,
                lowercase=True
            )
            
            tfidf_matrix = vectorizer.fit_transform([combined_text])
            feature_names = vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # Get top terms
            top_indices = np.argsort(tfidf_scores)[-max_terms:][::-1]
            key_terms = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]
            
            return key_terms
            
        except Exception:
            # Fallback: simple word frequency
            words = re.findall(r'\b[a-zA-Z]{3,}\b', ' '.join(texts).lower())
            word_freq = Counter(w for w in words if w not in self.stop_words)
            return [word for word, _ in word_freq.most_common(max_terms)]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Basic NER using regex patterns for both Ukrainian and English.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with entity types and lists of entities
        """
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],  # Geopolitical entity
            'MONEY': [],
            'DATE': []
        }
        
        if self.language == 'uk':
            return self._extract_ukrainian_entities(text, entities)
        else:
            return self._extract_english_entities(text, entities)
    
    def _extract_ukrainian_entities(self, text: str, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Extract entities from Ukrainian text."""
        
        # Ukrainian person names (often end with -енко, -ський, -цький, -ич, etc.)
        person_pattern = r'\b[А-ЯІЇЄҐ][а-яіїєґ]+(?:\s[А-ЯІЇЄҐ][а-яіїєґ]+){1,2}\b'
        entities['PERSON'] = list(set(re.findall(person_pattern, text)))
        
        # Organizations (Ukrainian terms)
        org_pattern = r'\b[А-ЯІЇЄҐ][а-яіїєґ\s]*(?:підприємство|компанія|корпорація|організація|агентство|департамент|міністерство|служба|установа|фонд|партія)\b'
        entities['ORG'] = list(set(re.findall(org_pattern, text)))
        
        # Locations (after prepositions like 'у', 'в', 'з')
        location_pattern = r'(?:у|в|з|до|від)\s+([А-ЯІЇЄҐ][а-яіїєґ]+(?:\s[А-ЯІЇЄҐ][а-яіїєґ]+)?)'
        matches = re.findall(location_pattern, text)
        entities['GPE'] = list(set(match[0] if isinstance(match, tuple) else match for match in matches))
        
        # Money amounts (hryvnia, dollars, euros)
        money_pattern = r'(?:₴|грн\.?|\$|€)\s?[\d\s,]+(?:\.\d{2})?(?:\s*(?:мільйон|мільярд|трильйон|тисяч|млн|млрд))?'
        entities['MONEY'] = list(set(re.findall(money_pattern, text, re.IGNORECASE)))
        
        # Ukrainian dates
        date_pattern = r'\b(?:січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)\s+\d{1,2}(?:,?\s+\d{4})?\b'
        entities['DATE'] = list(set(re.findall(date_pattern, text, re.IGNORECASE)))
        
        # Filter empty entities
        return {k: v for k, v in entities.items() if v}
    
    def _extract_english_entities(self, text: str, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Extract entities from English text."""
        
        # Person names (capitalized words, often 2-3 words)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b'
        entities['PERSON'] = list(set(re.findall(person_pattern, text)))
        
        # Organizations (words with Corp, Inc, Ltd, etc.)
        org_pattern = r'\b[A-Z][a-zA-Z\s]*(?:Corp|Inc|Ltd|LLC|Company|Organization|Agency|Department|Ministry)\b'
        entities['ORG'] = list(set(re.findall(org_pattern, text)))
        
        # Locations (capitalized words after 'in', 'at', 'from')
        location_pattern = r'(?:in|at|from)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)'
        entities['GPE'] = list(set(match[0] if isinstance(match, tuple) else match 
                                 for match in re.findall(location_pattern, text)))
        
        # Money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|trillion))?'
        entities['MONEY'] = list(set(re.findall(money_pattern, text, re.IGNORECASE)))
        
        # Dates
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        entities['DATE'] = list(set(re.findall(date_pattern, text, re.IGNORECASE)))
        
        # Filter empty entities
        return {k: v for k, v in entities.items() if v}
    
    def compress_cluster_content(self, articles: List[Any], 
                                embeddings: Optional[np.ndarray] = None,
                                max_medoids: int = 3,
                                max_sentences: int = 8,
                                max_terms: int = 15) -> Dict[str, Any]:
        """
        Compress cluster content for efficient LLM processing.
        
        Args:
            articles: List of article objects
            embeddings: Optional pre-computed embeddings
            max_medoids: Maximum medoid articles
            max_sentences: Maximum key sentences
            max_terms: Maximum key terms
            
        Returns:
            Compressed content dictionary
        """
        if not articles:
            return {}
        
        # Select medoid articles if embeddings available
        medoid_indices = None
        if embeddings is not None and len(embeddings) == len(articles):
            medoid_indices = self.find_medoids(embeddings, articles, max_medoids)
            selected_articles = [articles[i] for i in medoid_indices]
        else:
            # Fallback: select first few articles
            selected_articles = articles[:max_medoids]
        
        # Extract content from selected articles
        all_text = []
        article_summaries = []
        
        for article in selected_articles:
            text = f"{article.title}. {article.content}"
            all_text.append(text)
            article_summaries.append({
                'title': article.title,
                'source': article.source,
                'url': article.url,
                'published_date': article.published_date.isoformat()
            })
        
        # Extract key sentences using TextRank
        all_sentences = []
        for text in all_text:
            all_sentences.extend(self.extract_sentences(text))
        
        key_sentences = self.textrank_sentences(all_sentences, max_sentences)
        
        # Extract key terms
        key_terms = self.extract_key_terms(all_text, max_terms)
        
        # Extract entities from combined text
        combined_text = ' '.join(all_text)
        entities = self.extract_entities(combined_text)
        
        # Calculate content hash for caching
        content_hash = hashlib.md5(
            ''.join(key_sentences + key_terms).encode()
        ).hexdigest()
        
        return {
            'medoid_articles': article_summaries,
            'key_sentences': key_sentences,
            'key_terms': key_terms,
            'entities': entities,
            'content_hash': content_hash,
            'total_articles': len(articles),
            'compression_ratio': len(' '.join(key_sentences)) / len(combined_text)
        }
    
    def create_llm_prompt_content(self, compressed_data: Dict[str, Any]) -> str:
        """
        Create optimized content for LLM prompts.
        
        Args:
            compressed_data: Output from compress_cluster_content
            
        Returns:
            Formatted string for LLM prompt
        """
        content_parts = []
        
        # Key sentences
        if compressed_data.get('key_sentences'):
            content_parts.append("Key points:")
            for i, sentence in enumerate(compressed_data['key_sentences'][:6], 1):
                content_parts.append(f"{i}. {sentence}")
        
        # Important terms
        if compressed_data.get('key_terms'):
            terms = compressed_data['key_terms'][:10]
            content_parts.append(f"\\nImportant terms: {', '.join(terms)}")
        
        # Entities
        if compressed_data.get('entities'):
            entities_str = []
            for entity_type, entity_list in compressed_data['entities'].items():
                if entity_list:
                    entities_str.append(f"{entity_type}: {', '.join(entity_list[:3])}")
            if entities_str:
                content_parts.append(f"\\nKey entities: {'; '.join(entities_str)}")
        
        # Sources info
        if compressed_data.get('medoid_articles'):
            sources = [art['source'] for art in compressed_data['medoid_articles']]
            unique_sources = list(set(sources))
            content_parts.append(f"\\nSources ({len(unique_sources)}): {', '.join(unique_sources)}")
        
        return '\\n'.join(content_parts)
    
    def calculate_coherence_score(self, embeddings: np.ndarray) -> float:
        """
        Calculate coherence score for a cluster using cosine similarity.
        
        Args:
            embeddings: Array of embeddings in the cluster
            
        Returns:
            Average cosine similarity (coherence score)
        """
        if len(embeddings) < 2:
            return 1.0  # Perfect coherence for single article
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Calculate pairwise similarities
            similarities = cosine_similarity(embeddings)
            
            # Get upper triangle (excluding diagonal)
            n = len(similarities)
            upper_triangle = []
            
            for i in range(n):
                for j in range(i + 1, n):
                    upper_triangle.append(similarities[i][j])
            
            # Return average similarity
            return np.mean(upper_triangle) if upper_triangle else 0.0
            
        except Exception as e:
            # Fallback to 0 if calculation fails
            return 0.0