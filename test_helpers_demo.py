#!/usr/bin/env python3
"""Demo script to verify MinervaTestHelper functionality."""

from pathlib import Path
from tempfile import TemporaryDirectory

from tests.helpers import MinervaTestHelper


def demo_test_helper():
    """Demonstrate MinervaTestHelper functionality."""
    helper = MinervaTestHelper()
    
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test vault setup
        vault = helper.setup_test_vault(temp_path)
        print(f"✓ Created test vault at: {vault}")
        
        # Test note creation
        note_path = helper.create_temp_note(
            vault / "notes",
            "demo.md",
            "This is a demo note",
            {"tags": ["demo", "test"], "author": "Demo Author"}
        )
        print(f"✓ Created test note at: {note_path}")
        
        # Test content validation
        helper.assert_note_content(
            note_path,
            "This is a demo note",
            {"tags": ["demo", "test"], "author": "Demo Author"}
        )
        print("✓ Content validation passed")
        
        # Test frontmatter validation
        helper.assert_frontmatter_fields(
            note_path,
            {"author": "Demo Author", "tags": list}
        )
        print("✓ Frontmatter validation passed")
        
        # Test sample notes creation
        sample_notes = helper.create_sample_notes(vault)
        print(f"✓ Created {len(sample_notes)} sample notes")
        
        # Test file utilities
        helper.assert_file_exists(note_path)
        print("✓ File existence check passed")
        
        print("\n🎉 All MinervaTestHelper functionality verified!")


if __name__ == "__main__":
    demo_test_helper()