"""
Ukrainian Natural Language Processing utilities.
Provides spaCy integration for Ukrainian text processing.
"""
import logging
from typing import List, Dict, Any, Optional, Set
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import spaCy and Ukrainian model
try:
    import spacy
    from spacy import displacy
    
    # Try to load Ukrainian model
    try:
        nlp_uk = spacy.load("uk_core_news_sm")
        HAS_UKRAINIAN_MODEL = True
    except OSError:
        logger.warning("Ukrainian spaCy model not found. Install with: python -m spacy download uk_core_news_sm")
        nlp_uk = None
        HAS_UKRAINIAN_MODEL = False
        
    HAS_SPACY = True
except ImportError:
    logger.warning("spaCy not installed. Install with: pip install spacy")
    spacy = None
    nlp_uk = None
    HAS_SPACY = False
    HAS_UKRAINIAN_MODEL = False


class UkrainianNLP:
    """Ukrainian NLP processor using spaCy."""
    
    def __init__(self):
        self.nlp = nlp_uk if HAS_UKRAINIAN_MODEL else None
        self.available = HAS_UKRAINIAN_MODEL
        
        if not self.available:
            logger.warning("Ukrainian NLP not available. Using fallback methods.")
    
    def is_available(self) -> bool:
        """Check if Ukrainian NLP is available."""
        return self.available
    
    def process_text(self, text: str) -> Optional[Any]:
        """
        Process text with spaCy Ukrainian model.
        
        Args:
            text: Text to process
            
        Returns:
            spaCy Doc object or None if not available
        """
        if not self.available:
            return None
            
        try:
            return self.nlp(text)
        except Exception as e:
            logger.error(f"Error processing text with Ukrainian NLP: {e}")
            return None
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from Ukrainian text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with entity types and lists of entities
        """
        if not self.available:
            return self._fallback_entity_extraction(text)
        
        try:
            doc = self.nlp(text)
            entities = {}
            
            for ent in doc.ents:
                entity_type = ent.label_
                entity_text = ent.text.strip()
                
                if entity_type not in entities:
                    entities[entity_type] = []
                
                if entity_text and entity_text not in entities[entity_type]:
                    entities[entity_type].append(entity_text)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return self._fallback_entity_extraction(text)
    
    def extract_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """
        Extract keywords from Ukrainian text using POS tagging and frequency.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of important keywords
        """
        if not self.available:
            return self._fallback_keyword_extraction(text, max_keywords)
        
        try:
            doc = self.nlp(text)
            
            # Extract important words (nouns, adjectives, proper nouns)
            important_pos = {'NOUN', 'ADJ', 'PROPN'}
            keywords = []
            
            for token in doc:
                if (token.pos_ in important_pos and 
                    not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) > 2 and
                    token.text.isalpha()):
                    
                    lemma = token.lemma_.lower()
                    if lemma not in keywords:
                        keywords.append(lemma)
            
            # Simple frequency-based selection
            from collections import Counter
            word_freq = Counter(keywords)
            return [word for word, _ in word_freq.most_common(max_keywords)]
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return self._fallback_keyword_extraction(text, max_keywords)
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from Ukrainian text.
        
        Args:
            text: Text to process
            
        Returns:
            List of sentences
        """
        if not self.available:
            return self._fallback_sentence_extraction(text)
        
        try:
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
            return sentences
            
        except Exception as e:
            logger.error(f"Error extracting sentences: {e}")
            return self._fallback_sentence_extraction(text)
    
    def get_language_stats(self, text: str) -> Dict[str, Any]:
        """
        Get language statistics for Ukrainian text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with language statistics
        """
        if not self.available:
            return self._fallback_language_stats(text)
        
        try:
            doc = self.nlp(text)
            
            pos_counts = {}
            for token in doc:
                pos = token.pos_
                pos_counts[pos] = pos_counts.get(pos, 0) + 1
            
            return {
                'token_count': len(doc),
                'sentence_count': len(list(doc.sents)),
                'entity_count': len(doc.ents),
                'pos_distribution': pos_counts,
                'is_ukrainian': True
            }
            
        except Exception as e:
            logger.error(f"Error getting language stats: {e}")
            return self._fallback_language_stats(text)
    
    def _fallback_entity_extraction(self, text: str) -> Dict[str, List[str]]:
        """Fallback entity extraction using regex patterns."""
        import re
        
        entities = {
            'PERSON': [],
            'ORG': [],
            'GPE': [],
            'MONEY': [],
            'DATE': []
        }
        
        # Ukrainian person names
        person_pattern = r'\b[А-ЯІЇЄҐ][а-яіїєґ]+(?:\s[А-ЯІЇЄҐ][а-яіїєґ]+){1,2}\b'
        entities['PERSON'] = list(set(re.findall(person_pattern, text)))
        
        # Organizations
        org_pattern = r'\b[А-ЯІЇЄҐ][а-яіїєґ\s]*(?:підприємство|компанія|корпорація|організація|міністерство|служба|установа|фонд|партія)\b'
        entities['ORG'] = list(set(re.findall(org_pattern, text)))
        
        # Locations
        location_pattern = r'(?:у|в|з|до|від)\s+([А-ЯІЇЄҐ][а-яіїєґ]+(?:\s[А-ЯІЇЄҐ][а-яіїєґ]+)?)'
        matches = re.findall(location_pattern, text)
        entities['GPE'] = list(set(matches))
        
        # Money amounts
        money_pattern = r'(?:₴|грн\.?|\$|€)\s?[\d\s,]+(?:\.\d{2})?(?:\s*(?:мільйон|мільярд|трильйон|тисяч|млн|млрд))?'
        entities['MONEY'] = list(set(re.findall(money_pattern, text, re.IGNORECASE)))
        
        # Ukrainian dates
        date_pattern = r'\b(?:січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня)\s+\d{1,2}(?:,?\s+\d{4})?\b'
        entities['DATE'] = list(set(re.findall(date_pattern, text, re.IGNORECASE)))
        
        return {k: v for k, v in entities.items() if v}
    
    def _fallback_keyword_extraction(self, text: str, max_keywords: int) -> List[str]:
        """Fallback keyword extraction using simple frequency analysis."""
        import re
        from collections import Counter
        
        # Ukrainian stop words
        stop_words = {
            'і', 'в', 'на', 'з', 'до', 'за', 'під', 'над', 'між', 'про', 'для',
            'від', 'при', 'по', 'у', 'та', 'або', 'але', 'а', 'чи', 'не', 'ні',
            'що', 'який', 'яка', 'яке', 'які', 'хто', 'де', 'коли', 'як', 'чому',
            'це', 'той', 'та', 'те', 'ті', 'він', 'вона', 'воно', 'вони', 'я',
            'ти', 'ми', 'ви', 'мій', 'твій', 'його', 'її', 'наш', 'ваш', 'їх'
        }
        
        # Extract words
        words = re.findall(r'\b[а-яіїєґА-ЯІЇЄҐ]{3,}\b', text.lower())
        words = [w for w in words if w not in stop_words]
        
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(max_keywords)]
    
    def _fallback_sentence_extraction(self, text: str) -> List[str]:
        """Fallback sentence extraction using simple splitting."""
        import re
        
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return sentences
    
    def _fallback_language_stats(self, text: str) -> Dict[str, Any]:
        """Fallback language statistics."""
        import re
        
        words = re.findall(r'\b\w+\b', text)
        sentences = self._fallback_sentence_extraction(text)
        
        return {
            'token_count': len(words),
            'sentence_count': len(sentences),
            'entity_count': 0,
            'pos_distribution': {},
            'is_ukrainian': bool(re.search(r'[іїєґ]', text.lower()))
        }


# Global instance
ukrainian_nlp = UkrainianNLP()