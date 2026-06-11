import os
import sys
import unittest
import tempfile
import json
from unittest.mock import MagicMock, patch

# Ensure project root is in python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.ats_scorer_agent import ATSScorerAgent
from agents.cover_letter_agent import CoverLetterAgent
from agents.auto_submitter_agent import AutoSubmitterAgent

class MockResponse:
    def __init__(self, text):
        self.text = text

class TestAdvancedFeatures(unittest.TestCase):
    
    @patch('agents.ats_scorer_agent.model')
    def test_ats_scorer_agent_success(self, mock_model):
        """Asserts ATSScorerAgent returns valid JSON with keys when generation succeeds."""
        mock_json_content = {
            "ats_score": 92,
            "parsability_rating": "Excellent",
            "matched_keywords": ["Python", "Playwright"],
            "missing_keywords": ["Docker"],
            "recommendations": ["Add docker to core skills."]
        }
        # Include markdown code blocks to test cleaning logic
        mock_model.generate_content.return_value = MockResponse(
            f"```json\n{json.dumps(mock_json_content)}\n```"
        )
        
        agent = ATSScorerAgent()
        report = agent.evaluate_resume("Resume context", "Job description")
        
        self.assertEqual(report["ats_score"], 92)
        self.assertEqual(report["parsability_rating"], "Excellent")
        self.assertListEqual(report["matched_keywords"], ["Python", "Playwright"])
        self.assertListEqual(report["missing_keywords"], ["Docker"])
        self.assertListEqual(report["recommendations"], ["Add docker to core skills."])
        
    @patch('agents.ats_scorer_agent.model')
    def test_ats_scorer_agent_invalid_json_fallback(self, mock_model):
        """Asserts ATSScorerAgent falls back gracefully when JSON response is invalid."""
        mock_model.generate_content.return_value = MockResponse("Invalid JSON data")
        
        agent = ATSScorerAgent()
        report = agent.evaluate_resume("Resume context", "Job description")
        
        # Should return fallback report
        self.assertEqual(report["ats_score"], 60)
        self.assertEqual(report["parsability_rating"], "Good")
        self.assertIn("recommendations", report)

    @patch('agents.ats_scorer_agent.model')
    def test_ats_scorer_agent_exception_fallback(self, mock_model):
        """Asserts ATSScorerAgent falls back gracefully when generate_content raises an exception."""
        mock_model.generate_content.side_effect = RuntimeError("API rate limit exceeded")
        
        agent = ATSScorerAgent()
        report = agent.evaluate_resume("Resume context", "Job description")
        
        # Should return fallback report
        self.assertEqual(report["ats_score"], 60)
        self.assertEqual(report["parsability_rating"], "Good")
        self.assertIn("recommendations", report)

    @patch('agents.cover_letter_agent.model')
    def test_cover_letter_agent_strips_code_fences(self, mock_model):
        """Asserts CoverLetterAgent output doesn't contain markdown block code fences."""
        raw_letter = "# Cover Letter\n\nDear Hiring Team,\n\nI am writing to apply..."
        mock_model.generate_content.return_value = MockResponse(
            f"```markdown\n{raw_letter}\n```"
        )
        
        agent = CoverLetterAgent()
        result = agent.generate_cover_letter({"personal_info": {"name": "John Doe"}}, "Job description")
        
        self.assertEqual(result, raw_letter)
        self.assertNotIn("```markdown", result)
        self.assertNotIn("```", result)

    @patch('agents.cover_letter_agent.model')
    def test_cover_letter_agent_fallback_on_error(self, mock_model):
        """Asserts CoverLetterAgent returns a styled fallback letter on API error."""
        mock_model.generate_content.side_effect = Exception("General API error")
        
        agent = CoverLetterAgent()
        result = agent.generate_cover_letter({"personal_info": {"name": "Alice Smith"}}, "Job description")
        
        self.assertIn("Alice Smith", result)
        self.assertIn("Dear Hiring Team", result)
        self.assertNotIn("General API error", result)

    def test_auto_submitter_platform_detection(self):
        """Asserts AutoSubmitterAgent platform detection matches Greenhouse, Lever, Workable, LinkedIn, Ashby, SmartRecruiters, iCIMS, Taleo or generic URLs."""
        # We don't need to load profile/resume files for platform detection testing.
        with patch('agents.auto_submitter_agent.load_profile', return_value={}):
            agent = AutoSubmitterAgent(profile_path="dummy_path.json", resume_path="dummy.pdf")
            
            self.assertEqual(agent._detect_platform("https://lever.co/company/job-id"), "lever")
            self.assertEqual(agent._detect_platform("https://jobs.lever.co/company/job-id"), "lever")
            self.assertEqual(agent._detect_platform("https://boards.greenhouse.io/company/jobs/123"), "greenhouse")
            self.assertEqual(agent._detect_platform("https://apply.workable.com/company/j/abc1234"), "workable")
            self.assertEqual(agent._detect_platform("https://www.linkedin.com/jobs/view/1234"), "linkedin")
            self.assertEqual(agent._detect_platform("https://ashbyhq.com/company/jobs/123"), "ashby")
            self.assertEqual(agent._detect_platform("https://jobs.smartrecruiters.com/company/1234"), "smartrecruiters")
            self.assertEqual(agent._detect_platform("https://company.icims.com/jobs/123"), "icims")
            self.assertEqual(agent._detect_platform("https://taleo.net/careers"), "taleo")
            self.assertEqual(agent._detect_platform("https://example.com/apply"), "generic")

    def test_auto_submitter_field_classification(self):
        """Asserts AutoSubmitterAgent correctly classifies inputs based on attributes/labels for different platforms."""
        class MockElement:
            def __init__(self, attrs):
                self.attrs = attrs
            def get_attribute(self, name):
                return self.attrs.get(name)

        with patch('agents.auto_submitter_agent.load_profile', return_value={}):
            agent = AutoSubmitterAgent(profile_path="dummy_path.json", resume_path="dummy.pdf")
            
            # 1. Lever Adapter
            el_lever_linkedin = MockElement({"name": "urls[linkedin]"})
            self.assertEqual(agent._classify_field(el_lever_linkedin, "", "lever"), "linkedin")
            
            el_lever_resume = MockElement({"type": "file"})
            self.assertEqual(agent._classify_field(el_lever_resume, "", "lever"), "resume")
            
            # 2. Greenhouse Adapter
            el_greenhouse_first = MockElement({"id": "first_name"})
            self.assertEqual(agent._classify_field(el_greenhouse_first, "", "greenhouse"), "first_name")
            
            el_greenhouse_last = MockElement({"name": "last_name"})
            self.assertEqual(agent._classify_field(el_greenhouse_last, "", "greenhouse"), "last_name")

            # 3. Workable Adapter
            el_workable_phone = MockElement({"name": "phone"})
            self.assertEqual(agent._classify_field(el_workable_phone, "", "workable"), "phone")

            # 4. LinkedIn Adapter
            el_linkedin_email = MockElement({"name": "email"})
            self.assertEqual(agent._classify_field(el_linkedin_email, "Email Address", "linkedin"), "email")
            
            el_linkedin_phone = MockElement({"name": "phone"})
            self.assertEqual(agent._classify_field(el_linkedin_phone, "Mobile Phone", "linkedin"), "phone")

            # 5. Ashby Adapter
            el_ashby_linkedin = MockElement({"name": "linkedin"})
            self.assertEqual(agent._classify_field(el_ashby_linkedin, "LinkedIn URL", "ashby"), "linkedin")
            
            el_ashby_resume = MockElement({"type": "file"})
            self.assertEqual(agent._classify_field(el_ashby_resume, "Resume/CV", "ashby"), "resume")

            # 6. SmartRecruiters Adapter
            el_sr_first = MockElement({"id": "firstName"})
            self.assertEqual(agent._classify_field(el_sr_first, "", "smartrecruiters"), "first_name")
            
            el_sr_last = MockElement({"id": "lastName"})
            self.assertEqual(agent._classify_field(el_sr_last, "", "smartrecruiters"), "last_name")

            # 7. iCIMS Adapter
            el_icims_email = MockElement({"placeholder": "login"})
            self.assertEqual(agent._classify_field(el_icims_email, "", "icims"), "email")
            
            el_icims_first = MockElement({"name": "first_name"})
            self.assertEqual(agent._classify_field(el_icims_first, "", "icims"), "first_name")

            # 8. Taleo Adapter
            el_taleo_username = MockElement({"placeholder": "username"})
            self.assertEqual(agent._classify_field(el_taleo_username, "", "taleo"), "email")

            # 9. Generic Classification
            el_generic_email = MockElement({"placeholder": "Email address"})
            self.assertEqual(agent._classify_field(el_generic_email, "", "generic"), "email")
            
            el_generic_name = MockElement({"aria-label": "Full Name"})
            self.assertEqual(agent._classify_field(el_generic_name, "", "generic"), "name")

            el_custom = MockElement({"placeholder": "What is your favorite color?"})
            self.assertEqual(agent._classify_field(el_custom, "Favorite Color", "generic"), "custom_question")

    def test_telemetry_database_read_write(self):
        """Asserts telemetry application logging successfully writes, appends, and handles file reads."""
        with patch('agents.auto_submitter_agent.load_profile', return_value={}):
            agent = AutoSubmitterAgent(profile_path="dummy_path.json", resume_path="dummy.pdf")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
                temp_history_path = tmp.name
                
            try:
                # Patch os.path.join inside agents.auto_submitter_agent to return our temp_history_path
                with patch('agents.auto_submitter_agent.os.path.join', return_value=temp_history_path):
                    
                    # Log first simulated application
                    metadata_1 = {"company": "TestCorp", "title": "Software Engineer II", "readiness_score": 85, "ats_score": 90}
                    agent._log_application("https://example.com/apply/1", "success", submit=False, metadata=metadata_1)
                    
                    # Verify file exists and has one entry
                    self.assertTrue(os.path.exists(temp_history_path))
                    with open(temp_history_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    self.assertEqual(len(data), 1)
                    self.assertEqual(data[0]["company"], "TestCorp")
                    self.assertEqual(data[0]["title"], "Software Engineer II")
                    self.assertEqual(data[0]["url"], "https://example.com/apply/1")
                    self.assertEqual(data[0]["status"], "Simulated")
                    self.assertEqual(data[0]["readiness_score"], 85)
                    self.assertEqual(data[0]["ats_score"], 90)
                    self.assertIn("timestamp", data[0])
                    
                    # Log second actual application (submit=True)
                    metadata_2 = {"company": "Google", "title": "Developer Advocate", "readiness_score": 95, "ats_score": 80}
                    agent._log_application("https://example.com/apply/2", "success", submit=True, metadata=metadata_2)
                    
                    # Verify file now has two entries (appended)
                    with open(temp_history_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    self.assertEqual(len(data), 2)
                    self.assertEqual(data[1]["company"], "Google")
                    self.assertEqual(data[1]["title"], "Developer Advocate")
                    self.assertEqual(data[1]["status"], "Submitted")
                    
                    # Log failed application
                    metadata_3 = {"company": "Stripe", "title": "Senior Dev", "readiness_score": 70, "ats_score": 75}
                    agent._log_application("https://example.com/apply/3", "failed", submit=True, metadata=metadata_3)
                    
                    with open(temp_history_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    self.assertEqual(len(data), 3)
                    self.assertEqual(data[2]["company"], "Stripe")
                    self.assertEqual(data[2]["status"], "Failed")
                    
            finally:
                if os.path.exists(temp_history_path):
                    os.remove(temp_history_path)

if __name__ == "__main__":
    unittest.main()
