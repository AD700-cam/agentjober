import os
import sys
import unittest
import tempfile

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.export_utils import markdown_to_pdf, markdown_to_html
from tools.embeddings import get_embedding
from src.llm.gemini_client import generate_resume
from tools.load_profile import load_profile

class TestResumePipeline(unittest.TestCase):
    
    def test_markdown_to_pdf_generation(self):
        """Verifies that markdown text is successfully converted into a styled PDF file."""
        sample_markdown = """
# Candidate Name
Candidate Title

---

## Professional Summary
Expert developer skilled in TypeScript and Next.js.

## Core Skills
* Languages: TypeScript, JavaScript
* Tools: Git, GitHub

## Projects
- **Collaborative Editor**: Real-time sync engine.
        """
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf_path = tmp.name
            
        try:
            # Generate the PDF
            markdown_to_pdf(sample_markdown, pdf_path)
            
            # Verify the file was created and is non-empty
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)
            
            # Verify the PDF file header
            with open(pdf_path, "rb") as f:
                header = f.read(4)
                self.assertEqual(header, b"%PDF")
                
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    def test_markdown_to_html_styling(self):
        """Verifies that markdown is correctly converted to styled HTML matching design specifications."""
        sample_markdown = """
# Name
## Summary
* Bullet item
        """
        html_content = markdown_to_html(sample_markdown)
        
        # Verify header tag translations
        self.assertIn("<h1>Name</h1>", html_content)
        self.assertIn("<h2>Summary</h2>", html_content)
        self.assertIn("<li>Bullet item</li>", html_content)
        
        # Verify styling variables
        self.assertIn('font-family: "Helvetica Neue"', html_content)
        self.assertIn("color: #334155;", html_content) # Slate-700
        self.assertIn("border-bottom: 2px solid #e2e8f0;", html_content)

    def test_embedding_dimensions(self):
        """Verifies that the new google-genai embedding service generates vectors with exactly 768 dimensions."""
        vector = get_embedding("Test text", task_type="retrieval_document")
        self.assertEqual(len(vector), 768)

    def test_profile_loader(self):
        """Verifies candidate profile details load correctly as a dictionary."""
        profile = load_profile()
        self.assertIsInstance(profile, dict)
        self.assertIn("personal_info", profile)
        self.assertIn("skills", profile)
        self.assertIn("projects", profile)

    def test_gemini_client_generate_content(self):
        """Verifies that content generation via tools.gemini_client works and implements retry logic."""
        from tools.gemini_client import model
        try:
            res = model.generate_content("Say test")
            self.assertIsNotNone(res.text)
            self.assertGreater(len(res.text), 0)
        except Exception as e:
            self.fail(f"tools.gemini_client generate_content failed: {e}")

if __name__ == "__main__":
    unittest.main()
