"""Link validation and auto-healing for PKM notes."""

import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from pkm_agent.data.link_analyzer import Link, LinkAnalyzer, LinkType
from pkm_agent.exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class LinkSuggestion:
    """Suggested fix for a broken link."""
    original_link: Link
    suggested_target: str
    confidence: float  # 0.0 to 1.0
    reason: str

    def __str__(self) -> str:
        return f"{self.suggested_target} (confidence: {self.confidence:.2%}, {self.reason})"


@dataclass
class HealingResult:
    """Result of attempting to heal a broken link."""
    link: Link
    success: bool
    action: str  # "fixed", "skipped", "failed"
    suggestion: LinkSuggestion | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "link": self.link.to_dict(),
            "success": self.success,
            "action": self.action,
            "suggestion": {
                "target": self.suggestion.suggested_target,
                "confidence": self.suggestion.confidence,
                "reason": self.suggestion.reason,
            } if self.suggestion else None,
            "error": self.error,
        }


class LinkValidator:
    """Validates and suggests fixes for broken links."""

    def __init__(self, analyzer: LinkAnalyzer, min_confidence: float = 0.7):
        """
        Initialize link validator.

        Args:
            analyzer: LinkAnalyzer instance
            min_confidence: Minimum confidence threshold for suggestions (0.0-1.0)
        """
        if not (0.0 <= min_confidence <= 1.0):
            raise ValidationError("min_confidence must be between 0.0 and 1.0")

        self.analyzer = analyzer
        self.min_confidence = min_confidence
        self.vault_root = analyzer.vault_root

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using SequenceMatcher."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def suggest_fix(self, broken_link: Link) -> LinkSuggestion | None:
        """
        Suggest a fix for a broken link using fuzzy matching.

        Args:
            broken_link: The broken link to fix

        Returns:
            LinkSuggestion if a good match is found, None otherwise
        """
        if not broken_link.is_broken:
            return None

        # Get all available note titles
        available_notes = list(self.analyzer._note_cache.keys())

        # Find best match using fuzzy matching
        best_match: str | None = None
        best_score: float = 0.0

        target_lower = broken_link.target.lower()

        for note_title in available_notes:
            score = self._calculate_similarity(broken_link.target, note_title)

            # Boost score for exact prefix matches
            if note_title.lower().startswith(target_lower):
                score += 0.2

            # Boost score for exact suffix matches
            if note_title.lower().endswith(target_lower):
                score += 0.1

            # Boost score for word matches
            target_words = set(target_lower.split())
            note_words = set(note_title.lower().split())
            if target_words & note_words:  # Intersection
                word_overlap = len(target_words & note_words) / max(len(target_words), 1)
                score += word_overlap * 0.3

            if score > best_score:
                best_score = score
                best_match = note_title

        # Only suggest if confidence is above threshold
        if best_match and best_score >= self.min_confidence:
            return LinkSuggestion(
                original_link=broken_link,
                suggested_target=best_match,
                confidence=best_score,
                reason=f"Fuzzy match (similarity: {best_score:.2%})",
            )

        return None

    def validate_vault(self, auto_suggest: bool = True) -> dict[str, any]:
        """
        Validate all links in the vault.

        Args:
            auto_suggest: Whether to generate fix suggestions for broken links

        Returns:
            Dictionary with validation results
        """
        logger.info("Validating vault links...")

        broken_links = self.analyzer.find_broken_links()
        suggestions: list[LinkSuggestion] = []

        if auto_suggest:
            for link in broken_links:
                suggestion = self.suggest_fix(link)
                if suggestion:
                    suggestions.append(suggestion)

        fixable_count = len(suggestions)
        unfixable_count = len(broken_links) - fixable_count

        result = {
            "total_broken": len(broken_links),
            "fixable": fixable_count,
            "unfixable": unfixable_count,
            "broken_links": [link.to_dict() for link in broken_links],
            "suggestions": [
                {
                    "source": s.original_link.source_path,
                    "line": s.original_link.line_number,
                    "original": s.original_link.target,
                    "suggested": s.suggested_target,
                    "confidence": s.confidence,
                    "reason": s.reason,
                }
                for s in suggestions
            ],
        }

        logger.info(
            f"Validation complete: {len(broken_links)} broken links, "
            f"{fixable_count} fixable, {unfixable_count} unfixable"
        )

        return result


class LinkHealer:
    """Auto-heals broken links in markdown notes."""

    def __init__(self, validator: LinkValidator, dry_run: bool = True):
        """
        Initialize link healer.

        Args:
            validator: LinkValidator instance
            dry_run: If True, only simulate fixes without writing changes
        """
        self.validator = validator
        self.dry_run = dry_run
        self.vault_root = validator.vault_root

    def heal_link(self, broken_link: Link, suggestion: LinkSuggestion) -> HealingResult:
        """
        Heal a single broken link by replacing it with the suggested target.

        Args:
            broken_link: The broken link to fix
            suggestion: The suggested fix

        Returns:
            HealingResult indicating success or failure
        """
        try:
            file_path = self.vault_root / broken_link.source_path

            # Read file content
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Get the specific line
            if broken_link.line_number > len(lines):
                return HealingResult(
                    link=broken_link,
                    success=False,
                    action="failed",
                    error=f"Line number {broken_link.line_number} out of range",
                )

            line = lines[broken_link.line_number - 1]  # Convert to 0-indexed

            # Replace the link based on type
            if broken_link.link_type == LinkType.WIKILINK:
                # Replace [[old]] with [[new]]
                old_pattern = f"[[{broken_link.target}]]"
                new_pattern = f"[[{suggestion.suggested_target}]]"
                new_line = line.replace(old_pattern, new_pattern, 1)

            elif broken_link.link_type == LinkType.EMBED:
                # Replace ![[old]] with ![[new]]
                old_pattern = f"![[{broken_link.target}]]"
                new_pattern = f"![[{suggestion.suggested_target}]]"
                new_line = line.replace(old_pattern, new_pattern, 1)

            elif broken_link.link_type == LinkType.MARKDOWN:
                # Replace [text](old) with [text](new)
                if broken_link.display_text:
                    old_pattern = f"[{broken_link.display_text}]({broken_link.target})"
                    new_pattern = f"[{broken_link.display_text}]({suggestion.suggested_target})"
                    new_line = line.replace(old_pattern, new_pattern, 1)
                else:
                    return HealingResult(
                        link=broken_link,
                        success=False,
                        action="failed",
                        error="Cannot fix markdown link without display text",
                    )

            else:
                return HealingResult(
                    link=broken_link,
                    success=False,
                    action="skipped",
                    error=f"Unsupported link type: {broken_link.link_type}",
                )

            # Check if replacement was successful
            if new_line == line:
                return HealingResult(
                    link=broken_link,
                    success=False,
                    action="failed",
                    error="Link pattern not found in line",
                )

            # Update the line
            lines[broken_link.line_number - 1] = new_line

            # Write back to file (if not dry run)
            if not self.dry_run:
                new_content = '\n'.join(lines)
                file_path.write_text(new_content, encoding='utf-8')
                action = "fixed"
                logger.info(f"Fixed link in {broken_link.source_path}:{broken_link.line_number}")
            else:
                action = "simulated"
                logger.info(f"[DRY RUN] Would fix link in {broken_link.source_path}:{broken_link.line_number}")

            return HealingResult(
                link=broken_link,
                success=True,
                action=action,
                suggestion=suggestion,
            )

        except Exception as e:
            logger.error(f"Error healing link: {e}")
            return HealingResult(
                link=broken_link,
                success=False,
                action="failed",
                error=str(e),
            )

    def heal_file(self, file_path: Path) -> list[HealingResult]:
        """
        Heal all broken links in a specific file.

        Args:
            file_path: Path to the markdown file

        Returns:
            List of HealingResult for each link processed
        """
        results: list[HealingResult] = []

        # Find broken links in this file
        broken_links = self.validator.analyzer.find_broken_links(file_path)

        for link in broken_links:
            # Get suggestion
            suggestion = self.validator.suggest_fix(link)

            if suggestion:
                result = self.heal_link(link, suggestion)
                results.append(result)
            else:
                results.append(HealingResult(
                    link=link,
                    success=False,
                    action="skipped",
                    error="No suitable fix suggestion found",
                ))

        return results

    def heal_vault(self, min_confidence: float | None = None) -> dict[str, any]:
        """
        Heal all broken links in the entire vault.

        Args:
            min_confidence: Override the validator's min_confidence threshold

        Returns:
            Dictionary with healing statistics and results
        """
        logger.info(f"Starting vault healing (dry_run={self.dry_run})...")

        # Validate and get suggestions
        validation_result = self.validator.validate_vault(auto_suggest=True)
        suggestions_dict = {
            (s["source"], s["line"], s["original"]): s
            for s in validation_result["suggestions"]
        }

        # Heal each broken link with a suggestion
        results: list[HealingResult] = []
        broken_links = self.validator.analyzer.find_broken_links()

        for link in broken_links:
            key = (link.source_path, link.line_number, link.target)

            if key in suggestions_dict:
                suggestion_data = suggestions_dict[key]

                # Check confidence threshold
                if min_confidence and suggestion_data["confidence"] < min_confidence:
                    results.append(HealingResult(
                        link=link,
                        success=False,
                        action="skipped",
                        error=f"Confidence {suggestion_data['confidence']:.2%} below threshold {min_confidence:.2%}",
                    ))
                    continue

                # Create suggestion object
                suggestion = LinkSuggestion(
                    original_link=link,
                    suggested_target=suggestion_data["suggested"],
                    confidence=suggestion_data["confidence"],
                    reason=suggestion_data["reason"],
                )

                result = self.heal_link(link, suggestion)
                results.append(result)
            else:
                results.append(HealingResult(
                    link=link,
                    success=False,
                    action="skipped",
                    error="No suggestion available",
                ))

        # Calculate statistics
        fixed_count = sum(1 for r in results if r.action in ("fixed", "simulated"))
        failed_count = sum(1 for r in results if r.action == "failed")
        skipped_count = sum(1 for r in results if r.action == "skipped")

        summary = {
            "dry_run": self.dry_run,
            "total_processed": len(results),
            "fixed": fixed_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "results": [r.to_dict() for r in results],
        }

        logger.info(
            f"Vault healing complete: {fixed_count} fixed, "
            f"{failed_count} failed, {skipped_count} skipped"
        )

        return summary
