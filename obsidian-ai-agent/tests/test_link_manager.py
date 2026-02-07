"""
Unit tests for Dead Link Detection and Repair (Issue #98)
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from link_manager import (
    LinkManager,
    LinkParser,
    LinkDatabase,
    LinkRepairSuggester,
    Link,
    LinkType,
    LinkStatus,
    LinkReport
)


class TestLinkParser(unittest.TestCase):
    """Test link parsing functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "vault"
        self.vault_path.mkdir()
        self.parser = LinkParser(str(self.vault_path))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_parse_wiki_link(self):
        """Test parsing [[Wiki Link]]."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("Link to [[Another Note]] here.")
        
        links = self.parser.parse_note(note_path)
        
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, "Another Note")
        self.assertEqual(links[0].link_type, LinkType.WIKI)
        self.assertEqual(links[0].line_number, 1)
    
    def test_parse_wiki_alias(self):
        """Test parsing [[Note|Display]]."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("See [[Target Note|this note]] for more.")
        
        links = self.parser.parse_note(note_path)
        
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, "Target Note")
        self.assertEqual(links[0].display_text, "this note")
        self.assertEqual(links[0].link_type, LinkType.WIKI_ALIAS)
    
    def test_parse_embed(self):
        """Test parsing ![[Embedded]]."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("Embedded: ![[Diagram]].")
        
        links = self.parser.parse_note(note_path)
        
        # Should find at least the embed link
        embed_links = [l for l in links if l.link_type == LinkType.EMBED]
        self.assertEqual(len(embed_links), 1)
        self.assertEqual(embed_links[0].target, "Diagram")
    
    def test_parse_markdown_link(self):
        """Test parsing [Text](path)."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("[Click here](./other.md) for more.")
        
        links = self.parser.parse_note(note_path)
        
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, "./other.md")
        self.assertEqual(links[0].display_text, "Click here")
        self.assertEqual(links[0].link_type, LinkType.MARKDOWN)
    
    def test_ignore_external_links(self):
        """Test that external URLs are ignored in markdown links."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("[Google](https://google.com) search.")
        
        links = self.parser.parse_note(note_path)
        
        # External links are skipped during parsing
        self.assertEqual(len(links), 0)
    
    def test_multiple_links(self):
        """Test parsing multiple links in one note."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("""# Test

Link to [[Note A]] and [[Note B]].
Also see [[Note C|this one]].
""")
        
        links = self.parser.parse_note(note_path)
        
        self.assertEqual(len(links), 3)
        targets = [l.target for l in links]
        self.assertIn("Note A", targets)
        self.assertIn("Note B", targets)
        self.assertIn("Note C", targets)
    
    def test_line_numbers(self):
        """Test correct line number reporting."""
        note_path = self.vault_path / "test.md"
        note_path.write_text("""Line 1
Line 2 with [[Link A]]
Line 3
Line 4 with [[Link B]]
""")
        
        links = self.parser.parse_note(note_path)
        
        self.assertEqual(len(links), 2)
        line_numbers = [l.line_number for l in links]
        self.assertIn(2, line_numbers)
        self.assertIn(4, line_numbers)


class TestLinkDatabase(unittest.TestCase):
    """Test link database operations."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "links.db"
        self.db = LinkDatabase(str(self.db_path))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_and_retrieve_link(self):
        """Test adding and retrieving a link."""
        link = Link(
            source_note="source.md",
            target="target.md",
            display_text="Target",
            link_type=LinkType.WIKI,
            line_number=5,
            column_start=10,
            column_end=25,
            original_text="[[target.md]]",
            context="...context...",
            status=LinkStatus.VALID
        )
        
        self.db.add_link(link)
        
        links = self.db.get_links_from_note("source.md")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].target, "target.md")
        self.assertEqual(links[0].line_number, 5)
    
    def test_add_note(self):
        """Test adding note metadata."""
        self.db.add_note(
            note_id="test.md",
            file_path="/vault/test.md",
            title="Test",
            aliases=["Alias1", "Alias2"]
        )
        
        # Should not raise error
        self.assertTrue(True)
    
    def test_persistence(self):
        """Test data persists across connections."""
        link = Link(
            source_note="source.md",
            target="target.md",
            display_text="Target",
            link_type=LinkType.WIKI,
            line_number=1,
            column_start=0,
            column_end=10,
            original_text="[[target.md]]",
            context="context"
        )
        
        self.db.add_link(link)
        
        # Create new connection
        del self.db
        self.db = LinkDatabase(str(self.db_path))
        
        links = self.db.get_links_from_note("source.md")
        self.assertEqual(len(links), 1)


class TestLinkManager(unittest.TestCase):
    """Test main link manager functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "vault"
        self.vault_path.mkdir()
        self.db_path = Path(self.temp_dir) / "links.db"
        self.manager = LinkManager(str(self.vault_path), str(self.db_path))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_note(self, path: str, content: str):
        """Helper to create a test note."""
        note_path = self.vault_path / path
        note_path.parent.mkdir(parents=True, exist_ok=True)
        note_path.write_text(content, encoding='utf-8')
        return note_path
    
    def test_scan_valid_links(self):
        """Test scanning notes with valid links."""
        self.create_note("noteA.md", "Link to [[noteB]].")
        self.create_note("noteB.md", "Link to [[noteA]].")
        
        report = self.manager.scan_vault()
        
        self.assertEqual(report.total_notes, 2)
        self.assertEqual(report.total_links, 2)
        self.assertEqual(len(report.broken_links), 0)
        self.assertEqual(len(report.valid_links), 2)
    
    def test_detect_broken_links(self):
        """Test detection of broken links."""
        self.create_note("noteA.md", "Link to [[MissingNote]].")
        self.create_note("noteB.md", "No links here.")
        
        report = self.manager.scan_vault()
        
        self.assertEqual(len(report.broken_links), 1)
        self.assertEqual(report.broken_links[0].target, "MissingNote")
        self.assertEqual(report.broken_links[0].source_note, "noteA.md")
    
    def test_detect_orphans(self):
        """Test detection of orphan notes."""
        self.create_note("noteA.md", "Link to [[noteB]].")
        self.create_note("noteB.md", "Got a link!")
        self.create_note("orphan.md", "No one links to me.")
        
        report = self.manager.scan_vault()
        
        # Should detect orphan.md (noteA and noteB are linked)
        self.assertGreaterEqual(len(report.orphan_notes), 1)
        self.assertIn("orphan.md", report.orphan_notes)
    
    def test_suggestions_for_broken_links(self):
        """Test suggestion generation for broken links."""
        self.create_note("My Document.md", "Content here.")
        self.create_note("source.md", "Link to [[My Doc]] with typo.")
        
        report = self.manager.scan_vault()
        
        self.assertEqual(len(report.broken_links), 1)
        # Should suggest "My Document.md" as a fix
        self.assertGreater(len(report.broken_links[0].suggestions), 0)
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive link matching."""
        self.create_note("MyNote.md", "Content.")
        self.create_note("source.md", "Link to [[mynote]].")
        
        report = self.manager.scan_vault()
        
        # Should detect as ambiguous (similar but different case)
        self.assertGreater(len(report.ambiguous_links) + len(report.valid_links), 0)
    
    def test_report_export(self):
        """Test report export to JSON."""
        self.create_note("note.md", "[[Other]].")
        self.create_note("other.md", "Content.")
        
        report = self.manager.scan_vault()
        output_path = Path(self.temp_dir) / "report.json"
        
        success = self.manager.export_report(report, str(output_path))
        
        self.assertTrue(success)
        self.assertTrue(output_path.exists())
        
        import json
        data = json.loads(output_path.read_text())
        self.assertIn('total_notes', data)
        self.assertIn('broken_links', data)


class TestLinkRepair(unittest.TestCase):
    """Test link repair functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "vault"
        self.vault_path.mkdir()
        self.db_path = Path(self.temp_dir) / "links.db"
        self.manager = LinkManager(str(self.vault_path), str(self.db_path))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_repair_wiki_link(self):
        """Test repairing a wiki link."""
        # Create notes
        source_path = self.vault_path / "source.md"
        source_path.write_text("Link to [[Old Name]] here.")
        
        target_path = self.vault_path / "New Name.md"
        target_path.write_text("Content.")
        
        # Create broken link
        link = Link(
            source_note="source.md",
            target="Old Name",
            display_text="Old Name",
            link_type=LinkType.WIKI,
            line_number=1,
            column_start=8,
            column_end=20,
            original_text="[[Old Name]]",
            context="Link to [[Old Name]] here."
        )
        
        # Repair
        success = self.manager.repair_link(link, "New Name")
        
        self.assertTrue(success)
        
        # Verify
        content = source_path.read_text()
        self.assertIn("[[New Name]]", content)
        self.assertNotIn("[[Old Name]]", content)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_complex_vault(self):
        """Test with a complex vault structure."""
        temp_dir = tempfile.mkdtemp()
        try:
            vault_path = Path(temp_dir) / "vault"
            vault_path.mkdir()
            
            # Create folder structure
            (vault_path / "projects").mkdir()
            (vault_path / "notes").mkdir()
            
            # Create notes with various link types
            (vault_path / "README.md").write_text("""# Vault

- [[projects/Project A]]
- [[notes/Ideas]]
- [[Missing Link]]
""")
            
            (vault_path / "projects" / "Project A.md").write_text("""# Project A

See [[README]] for overview.
Details in [[notes/Ideas|Ideas]].
""")
            
            (vault_path / "notes" / "Ideas.md").write_text("""# Ideas

Random thoughts.
""")
            
            # Orphan note
            (vault_path / "notes" / "Draft.md").write_text("""# Draft

Unfinished work.
""")
            
            # Scan
            manager = LinkManager(str(vault_path))
            report = manager.scan_vault()
            
            # Verify results
            self.assertEqual(report.total_notes, 4)
            self.assertEqual(len(report.broken_links), 1)
            self.assertEqual(report.broken_links[0].target, "Missing Link")
            self.assertEqual(len(report.orphan_notes), 1)
            self.assertIn("notes/Draft.md", report.orphan_notes)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
