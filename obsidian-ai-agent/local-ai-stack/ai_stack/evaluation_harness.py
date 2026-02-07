#!/usr/bin/env python3
"""
Evaluation and Hallucination Detection
Provides:
- Response quality evaluation
- Hallucination detection
- Faithfulness checking
- Answer relevance scoring
- Feedback loop for improvement
"""

import json
import logging
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('evaluation')


@dataclass
class EvaluationResult:
    """Result of evaluating a response"""
    overall_score: float  # 0.0 to 1.0
    metrics: Dict[str, float]
    issues: List[str]
    suggestions: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'overall_score': self.overall_score,
            'metrics': self.metrics,
            'issues': self.issues,
            'suggestions': self.suggestions,
            'timestamp': self.timestamp
        }


class HallucinationDetector:
    """
    Detects hallucinations in LLM responses
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        
        # Patterns that indicate uncertainty
        self.uncertainty_patterns = [
            r'\b(might|may|could|possibly|perhaps|probably|likely)\b',
            r'\b(I think|I believe|it seems|appears to be)\b',
            r'\b(if I recall|if I remember|from what I know)\b',
            r'\b(not sure|unclear|unknown)\b'
        ]
        
        # Patterns for factual claims
        self.factual_patterns = [
            r'\b(is|are|was|were)\s+\w+',  # "X is Y"
            r'\b(has|have|had)\s+\w+',      # "X has Y"
            r'\d{4}',  # Years (potential historical claims)
            r'\b(percent|percentage)\b',
        ]
    
    def detect(self, response: str, context: str = "") -> Dict:
        """
        Detect potential hallucinations in response
        """
        issues = []
        confidence_score = 1.0
        
        # 1. Check for unsupported claims
        unsupported = self._check_unsupported_claims(response, context)
        if unsupported:
            issues.extend(unsupported)
            confidence_score -= 0.2 * len(unsupported)
        
        # 2. Check for contradictions with context
        contradictions = self._check_contradictions(response, context)
        if contradictions:
            issues.extend(contradictions)
            confidence_score -= 0.3 * len(contradictions)
        
        # 3. Check confidence markers
        confidence_markers = self._analyze_confidence_markers(response)
        confidence_score -= confidence_markers['uncertainty_penalty']
        
        # 4. Check for specific hallucination patterns
        hallucination_patterns = self._check_hallucination_patterns(response)
        if hallucination_patterns:
            issues.extend(hallucination_patterns)
            confidence_score -= 0.15 * len(hallucination_patterns)
        
        # Normalize confidence
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        return {
            'is_hallucination': confidence_score < 0.5,
            'confidence_score': confidence_score,
            'issues': issues,
            'risk_level': 'high' if confidence_score < 0.3 else 'medium' if confidence_score < 0.7 else 'low'
        }
    
    def _check_unsupported_claims(self, response: str, context: str) -> List[str]:
        """Identify claims not supported by context"""
        issues = []
        
        # Extract factual sentences
        sentences = re.split(r'[.!?]+', response)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if it looks like a factual claim
            is_factual = any(re.search(pattern, sentence, re.IGNORECASE) 
                           for pattern in self.factual_patterns)
            
            if is_factual:
                # Check if supported by context
                if context and not self._is_supported(sentence, context):
                    issues.append(f"Potentially unsupported claim: '{sentence[:100]}...'")
        
        return issues
    
    def _is_supported(self, claim: str, context: str) -> bool:
        """Check if claim is supported by context (simple keyword overlap)"""
        claim_words = set(re.findall(r'\b\w{4,}\b', claim.lower()))
        context_words = set(re.findall(r'\b\w{4,}\b', context.lower()))
        
        if not claim_words:
            return True
        
        overlap = len(claim_words & context_words)
        overlap_ratio = overlap / len(claim_words)
        
        return overlap_ratio > 0.3  # At least 30% of claim words in context
    
    def _check_contradictions(self, response: str, context: str) -> List[str]:
        """Check for contradictions with context"""
        issues = []
        
        # Simple contradiction detection
        # Look for negations of context statements
        negation_patterns = [
            (r'is\s+(\w+)', r'is\s+not\s+\1'),
            (r'are\s+(\w+)', r'are\s+not\s+\1'),
            (r'(\w+)\s+is', r'\1\s+is\s+not'),
        ]
        
        for pos_pattern, neg_pattern in negation_patterns:
            for match in re.finditer(pos_pattern, context, re.IGNORECASE):
                concept = match.group(1)
                # Check if response negates it
                if re.search(neg_pattern.replace(r'\1', concept), response, re.IGNORECASE):
                    issues.append(f"Possible contradiction regarding '{concept}'")
        
        return issues
    
    def _analyze_confidence_markers(self, response: str) -> Dict:
        """Analyze confidence markers in response"""
        uncertainty_count = 0
        for pattern in self.uncertainty_patterns:
            uncertainty_count += len(re.findall(pattern, response, re.IGNORECASE))
        
        uncertainty_penalty = min(0.3, uncertainty_count * 0.05)
        
        return {
            'uncertainty_count': uncertainty_count,
            'uncertainty_penalty': uncertainty_penalty
        }
    
    def _check_hallucination_patterns(self, response: str) -> List[str]:
        """Check for known hallucination patterns"""
        issues = []
        
        # Pattern 1: References to non-existent documents
        doc_refs = re.findall(r'\b(according to|in|from)\s+(?:the\s+)?["\']?([^"\']+)(?:document|paper|article|book)', 
                              response, re.IGNORECASE)
        for _, ref in doc_refs:
            issues.append(f"Reference to external source: '{ref}'")
        
        # Pattern 2: Specific numbers without context
        suspicious_numbers = re.findall(r'\b\d{5,}\b', response)
        if suspicious_numbers:
            issues.append(f"Suspiciously specific numbers: {suspicious_numbers}")
        
        # Pattern 3: Invention of names/details
        invented_details = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:said|stated|mentioned)\b', response)
        if invented_details:
            issues.append(f"Potentially invented quotes or attributions")
        
        return issues


class FaithfulnessChecker:
    """
    Check if response is faithful to retrieved context
    """
    
    def check(self, response: str, contexts: List[str]) -> Dict:
        """
        Calculate faithfulness metrics
        """
        combined_context = " ".join(contexts)
        
        # 1. Answer coverage (does it use the context?)
        coverage = self._calculate_coverage(response, combined_context)
        
        # 2. Information precision (is it adding new info?)
        precision = self._calculate_precision(response, combined_context)
        
        # 3. Semantic similarity
        similarity = self._calculate_similarity(response, combined_context)
        
        # Overall faithfulness
        faithfulness = (coverage * 0.3 + precision * 0.4 + similarity * 0.3)
        
        return {
            'faithfulness_score': faithfulness,
            'coverage': coverage,
            'precision': precision,
            'similarity': similarity,
            'is_faithful': faithfulness > 0.7
        }
    
    def _calculate_coverage(self, response: str, context: str) -> float:
        """Calculate how much of the context is used in response"""
        context_words = set(re.findall(r'\b\w{4,}\b', context.lower()))
        response_words = set(re.findall(r'\b\w{4,}\b', response.lower()))
        
        if not context_words:
            return 1.0
        
        coverage = len(response_words & context_words) / len(context_words)
        return coverage
    
    def _calculate_precision(self, response: str, context: str) -> float:
        """Calculate precision (how much of response is from context)"""
        response_words = set(re.findall(r'\b\w{4,}\b', response.lower()))
        context_words = set(re.findall(r'\b\w{4,}\b', context.lower()))
        
        if not response_words:
            return 1.0
        
        precision = len(response_words & context_words) / len(response_words)
        return precision
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple semantic similarity using word overlap"""
        words1 = set(re.findall(r'\b\w{4,}\b', text1.lower()))
        words2 = set(re.findall(r'\b\w{4,}\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


class AnswerRelevanceScorer:
    """
    Score how relevant an answer is to the question
    """
    
    def score(self, question: str, answer: str) -> Dict:
        """
        Calculate relevance metrics
        """
        # Extract key terms from question
        question_terms = self._extract_key_terms(question)
        
        # Check if answer addresses these terms
        answer_lower = answer.lower()
        matched_terms = [term for term in question_terms if term in answer_lower]
        
        term_coverage = len(matched_terms) / len(question_terms) if question_terms else 1.0
        
        # Check for direct answer patterns
        direct_answer_score = self._check_direct_answer(question, answer)
        
        # Overall relevance
        relevance = (term_coverage * 0.6 + direct_answer_score * 0.4)
        
        return {
            'relevance_score': relevance,
            'term_coverage': term_coverage,
            'direct_answer_score': direct_answer_score,
            'matched_terms': matched_terms,
            'is_relevant': relevance > 0.5
        }
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Remove stop words and extract meaningful terms
        stop_words = {'what', 'when', 'where', 'which', 'how', 'does', 'is', 'are', 'the', 'and', 'or'}
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return [w for w in words if w not in stop_words]
    
    def _check_direct_answer(self, question: str, answer: str) -> float:
        """Check if answer directly addresses the question type"""
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        score = 0.0
        
        # Yes/No questions
        if re.match(r'^(is|are|does|do|can|will|has|have)\b', question_lower):
            if re.search(r'\b(yes|no|indeed|certainly|not)\b', answer_lower):
                score = 1.0
        
        # What/Which questions
        elif re.match(r'^(what|which)\b', question_lower):
            if len(answer.split()) > 3:  # Substantial answer
                score = 0.8
        
        # How questions
        elif re.match(r'^how\b', question_lower):
            if re.search(r'\b(step|first|then|next|finally|by)\b', answer_lower):
                score = 1.0
            else:
                score = 0.6
        
        # Why questions
        elif re.match(r'^why\b', question_lower):
            if re.search(r'\b(because|since|as|reason|due to)\b', answer_lower):
                score = 1.0
        
        return score


class ResponseEvaluator:
    """
    Complete response evaluation combining all metrics
    """
    
    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.hallucination_detector = HallucinationDetector(llm_client)
        self.faithfulness_checker = FaithfulnessChecker()
        self.relevance_scorer = AnswerRelevanceScorer()
    
    def evaluate(self, question: str, answer: str, 
                 retrieved_contexts: List[str] = None) -> EvaluationResult:
        """
        Complete evaluation of a response
        """
        retrieved_contexts = retrieved_contexts or []
        combined_context = " ".join(retrieved_contexts)
        
        metrics = {}
        issues = []
        suggestions = []
        
        # 1. Hallucination detection
        hallucination_result = self.hallucination_detector.detect(answer, combined_context)
        metrics['hallucination_risk'] = 1.0 - hallucination_result['confidence_score']
        issues.extend(hallucination_result['issues'])
        
        # 2. Faithfulness check
        if retrieved_contexts:
            faithfulness_result = self.faithfulness_checker.check(answer, retrieved_contexts)
            metrics['faithfulness'] = faithfulness_result['faithfulness_score']
            metrics['coverage'] = faithfulness_result['coverage']
            
            if not faithfulness_result['is_faithful']:
                issues.append("Response may not be fully faithful to retrieved context")
                suggestions.append("Consider using more information from the retrieved documents")
        
        # 3. Relevance scoring
        relevance_result = self.relevance_scorer.score(question, answer)
        metrics['relevance'] = relevance_result['relevance_score']
        
        if not relevance_result['is_relevant']:
            issues.append("Answer may not be fully relevant to the question")
            suggestions.append(f"Try to address these key terms: {relevance_result['matched_terms']}")
        
        # 4. Quality heuristics
        metrics['length_appropriateness'] = self._check_length(answer)
        metrics['structure_quality'] = self._check_structure(answer)
        
        # Calculate overall score
        overall = self._calculate_overall_score(metrics)
        
        # Generate suggestions
        if metrics.get('hallucination_risk', 0) > 0.3:
            suggestions.append("Add more citations or reduce unsupported claims")
        
        if metrics.get('coverage', 1.0) < 0.3:
            suggestions.append("Use more information from the retrieved context")
        
        return EvaluationResult(
            overall_score=overall,
            metrics=metrics,
            issues=issues,
            suggestions=suggestions
        )
    
    def _check_length(self, text: str) -> float:
        """Check if response length is appropriate"""
        word_count = len(text.split())
        
        if word_count < 10:
            return 0.5  # Too short
        elif word_count < 50:
            return 0.8  # Brief but OK
        elif word_count < 500:
            return 1.0  # Good length
        else:
            return 0.7  # Might be too long
    
    def _check_structure(self, text: str) -> float:
        """Check response structure quality"""
        score = 1.0
        
        # Check for proper paragraphing
        paragraphs = text.split('\n\n')
        if len(paragraphs) == 1 and len(text) > 200:
            score -= 0.2  # Wall of text
        
        # Check for proper sentences
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        if avg_sentence_length > 30:
            score -= 0.2  # Sentences too long
        
        return max(0.0, score)
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall quality score"""
        weights = {
            'faithfulness': 0.25,
            'relevance': 0.25,
            'hallucination_risk': 0.20,  # Inverted
            'coverage': 0.15,
            'length_appropriateness': 0.10,
            'structure_quality': 0.05
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for metric, weight in weights.items():
            if metric in metrics:
                value = metrics[metric]
                if metric == 'hallucination_risk':
                    value = 1.0 - value  # Invert so higher is better
                weighted_sum += value * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5


class FeedbackLoop:
    """
    Collect and apply feedback for continuous improvement
    """
    
    def __init__(self, storage_path: str = "./feedback"):
        self.storage_path = storage_path
        self.feedback_history: List[Dict] = []
    
    def collect_feedback(self, query: str, response: str, 
                         user_rating: int, user_comment: str = "",
                         evaluation_metrics: Dict = None):
        """Collect user feedback on a response"""
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'user_rating': user_rating,  # 1-5
            'user_comment': user_comment,
            'auto_metrics': evaluation_metrics or {}
        }
        
        self.feedback_history.append(feedback)
        
        # Save to disk
        self._save_feedback()
    
    def _save_feedback(self):
        """Save feedback to disk"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
        
        filepath = f"{self.storage_path}/feedback_{datetime.now().strftime('%Y%m')}.jsonl"
        with open(filepath, 'a') as f:
            for fb in self.feedback_history:
                f.write(json.dumps(fb) + '\n')
    
    def get_insights(self) -> Dict:
        """Analyze feedback for insights"""
        if not self.feedback_history:
            return {'message': 'No feedback collected yet'}
        
        ratings = [fb['user_rating'] for fb in self.feedback_history]
        
        return {
            'total_feedback': len(self.feedback_history),
            'average_rating': sum(ratings) / len(ratings),
            'rating_distribution': {
                str(i): ratings.count(i) for i in range(1, 6)
            },
            'common_issues': self._extract_common_issues()
        }
    
    def _extract_common_issues(self) -> List[str]:
        """Extract common issues from feedback"""
        issue_counts = defaultdict(int)
        
        for fb in self.feedback_history:
            comment = fb.get('user_comment', '').lower()
            
            # Check for common complaint patterns
            if 'wrong' in comment or 'incorrect' in comment:
                issue_counts['incorrect_info'] += 1
            if 'long' in comment or 'verbose' in comment:
                issue_counts['too_long'] += 1
            if 'short' in comment or 'brief' in comment:
                issue_counts['too_short'] += 1
            if 'relevant' in comment or 'related' in comment:
                issue_counts['not_relevant'] += 1
        
        # Return top issues
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        return [f"{issue} ({count} times)" for issue, count in sorted_issues[:5]]


# Example usage
if __name__ == '__main__':
    # Create evaluator
    evaluator = ResponseEvaluator()
    
    # Test evaluation
    question = "What is machine learning?"
    answer = "Machine learning is a subset of artificial intelligence that enables systems to learn from data. It uses algorithms to identify patterns and make predictions without explicit programming."
    context = ["Machine learning is a method of data analysis that automates analytical model building.", 
               "It is a branch of artificial intelligence based on the idea that systems can learn from data."]
    
    result = evaluator.evaluate(question, answer, context)
    
    print("Evaluation Result:")
    print(json.dumps(result.to_dict(), indent=2))
