import os
import json
import time
import httpx
import random
import re
from playwright.sync_api import Page
from tools.gemini_client import model
from tools.load_profile import load_profile

class AutoSubmitterAgent:
    """Automates form discovery, platform-specific adaptations, resume upload, and custom question answering on job boards."""
    
    def __init__(self, profile_path: str = "data/master_profile.json", resume_path: str = "Resume.pdf", prefilled_answers: dict = None):
        self.profile_path = profile_path
        self.resume_path = resume_path
        self.prefilled_answers = prefilled_answers or {}
        self.custom_questions_logged = {}  # Store questions & answers dynamically to save later
        
        # Load profile
        try:
            self.profile = load_profile(self.profile_path)
        except Exception as e:
            print(f"[AutoSubmitter] Warning: Could not load profile: {e}")
            self.profile = {}

    def _fill_field(self, el, val: str):
        """Fills an input/textarea with a human-like delay using type."""
        try:
            el.focus()
            el.press("Control+A")
            el.press("Backspace")
            # Clear if not empty
            try:
                if el.input_value():
                    el.fill("")
            except Exception:
                pass
            
            # Simulated typing delay
            delay = random.randint(40, 100)
            el.type(val, delay=delay)
        except Exception:
            try:
                el.fill(val)
            except Exception:
                pass
            
    def fill_job_application(self, page: Page, url: str, submit=False, metadata: dict = None):
        """Navigates to the job application URL, clicks 'Apply' if necessary, fills form fields, and submits if requested."""
        yield f"🚀 Navigating to job listing: {url}"
        
        platform = self._detect_platform(url)
        yield f"⚙️ Detected Platform Adapter: '{platform.upper()}'"
        
        try:
            page.goto(url, timeout=45000)
            page.wait_for_load_state("load")
        except Exception as e:
            yield f"❌ Error navigating to job page: {e}"
            self._log_application(url, "failed", submit, metadata)
            return
            
        # Check if form fields are already visible on the page
        already_has_fields = False
        try:
            visible_fields_count = 0
            for frame in page.frames:
                visible_fields_count += len(self._find_form_elements(frame))
            if visible_fields_count >= 2:
                already_has_fields = True
        except Exception:
            pass

        # Step 1: Click "Apply" button if it exists and is visible
        apply_selectors = [
            "button:has-text('Apply')",
            "a:has-text('Apply')",
            "button:has-text('Apply for this job')",
            "a:has-text('Apply for this job')",
            "button:has-text('Apply Now')",
            "a:has-text('Apply Now')"
        ]
        
        apply_clicked = False
        if already_has_fields:
            yield "ℹ️ Form fields are already visible on the page. Skipping 'Apply' button checks."
        else:
            yield "🔍 Checking for 'Apply' links or buttons..."
            for selector in apply_selectors:
                try:
                    loc = page.locator(selector)
                    count = loc.count()
                    for idx in range(count):
                        btn = loc.nth(idx)
                        if btn.is_visible() and btn.is_enabled():
                            yield f"🖱️ Clicking Apply button: '{btn.inner_text().strip()}'"
                            btn.click()
                            page.wait_for_load_state("networkidle")
                            apply_clicked = True
                            break
                    if apply_clicked:
                        break
                except Exception:
                    pass
                    
            if not apply_clicked:
                yield "ℹ️ No visible 'Apply' button found or page directly displays the form. Proceeding to form filling."
            
        # Step 2: Form element discovery across all frames, in a loop for multi-step applications
        max_steps = 5
        step = 1
        filled_count = 0
        custom_question_count = 0
        status_outcome = "success"
        
        while step <= max_steps:
            yield f"📝 [Step {step}] Scanning for visible application form fields..."
            
            all_elements = []
            for frame in page.frames:
                try:
                    frame_elements = self._find_form_elements(frame)
                    all_elements.extend([(frame, el, tag, label) for el, tag, label in frame_elements])
                except Exception:
                    pass
            
            if not all_elements:
                yield f"ℹ️ [Step {step}] No visible input or textarea fields detected on this page."
            else:
                yield f"📋 [Step {step}] Found {len(all_elements)} visible form input elements. Auto-injecting details..."
                
                # Fill current visible elements
                for frame, el, tag, label in all_elements:
                    try:
                        # Check if the element is still attached and editable
                        if not el.is_editable():
                            continue
                            
                        # To avoid re-filling fields that already have content, we check if it's empty
                        try:
                            val_attr = el.input_value() if tag == "input" and el.get_attribute("type") != "file" else ""
                        except Exception:
                            val_attr = ""
                            
                        if val_attr and len(val_attr.strip()) > 0:
                            # Already has content, skip to avoid overwrite/loop
                            continue
                            
                        field_type = self._classify_field(el, label, platform)
                        
                        personal_info = self.profile.get("personal_info", {})
                        
                        if field_type == "name":
                            val = personal_info.get("name", "")
                            self._fill_field(el, val)
                            yield f"  ✅ Filled Name: '{val}'"
                            filled_count += 1
                        elif field_type == "first_name":
                            val = personal_info.get("name", "").split(None, 1)[0]
                            self._fill_field(el, val)
                            yield f"  ✅ Filled First Name: '{val}'"
                            filled_count += 1
                        elif field_type == "last_name":
                            parts = personal_info.get("name", "").split(None, 1)
                            val = parts[1] if len(parts) > 1 else parts[0]
                            self._fill_field(el, val)
                            yield f"  ✅ Filled Last Name: '{val}'"
                            filled_count += 1
                        elif field_type == "email":
                            val = personal_info.get("email", "")
                            self._fill_field(el, val)
                            yield f"  ✅ Filled Email: '{val}'"
                            filled_count += 1
                        elif field_type == "phone":
                            val = personal_info.get("phone", "")
                            self._fill_field(el, val)
                            yield f"  ✅ Filled Phone: '{val}'"
                            filled_count += 1
                        elif field_type == "linkedin":
                            val = personal_info.get("linkedin", "")
                            self._fill_field(el, val)
                            yield f"  ✅ Filled LinkedIn: '{val}'"
                            filled_count += 1
                        elif field_type == "github":
                            val = personal_info.get("github", "")
                            self._fill_field(el, val)
                            yield f"  ✅ Filled GitHub: '{val}'"
                            filled_count += 1
                        elif field_type == "portfolio":
                            val = personal_info.get("portfolio", "")
                            self._fill_field(el, val)
                            yield f"  ✅ Filled Portfolio/Website: '{val}'"
                            filled_count += 1
                        elif field_type == "resume":
                            el_type = el.get_attribute("type") or ""
                            if el_type == "file":
                                res_path = os.path.abspath(self.resume_path)
                                if os.path.exists(res_path):
                                    el.set_input_files(res_path)
                                    yield f"  📎 Uploaded Resume: '{self.resume_path}'"
                                    filled_count += 1
                                else:
                                    yield f"  ⚠️ Resume PDF not found at: '{self.resume_path}'. Skipping upload."
                            else:
                                yield f"  ⚠️ Detected resume text input field. Skipping file upload injection."
                        elif field_type == "custom_question":
                            custom_question_count += 1
                            question_text = label if label else (el.get_attribute("placeholder") or el.get_attribute("name") or "Custom Question")
                            yield f"  🤖 Custom Question Detected: '{question_text}'"
                            
                            # Check if we have pre-filled custom answers
                            if question_text in self.prefilled_answers:
                                ans = self.prefilled_answers[question_text]
                                yield f"    Using pre-filled answer: '{ans[:60]}...'"
                            else:
                                yield "    Generating answer via Gemini API..."
                                ans = self._generate_custom_answer(question_text)
                                
                            self._fill_field(el, ans)
                            self.custom_questions_logged[question_text] = ans
                            yield f"    ✅ Injected Answer (length: {len(ans)} chars): '{ans[:60]}...'"
                            filled_count += 1
                            
                    except Exception as fill_err:
                        yield f"  ❌ Error filling field: {fill_err}"
            
            # Now, check if there is a "Next", "Continue", "Review", "Save & Continue", "Save and Continue", or "Proceed" button.
            # If so, click it to transition to the next step of the application.
            next_selectors = [
                "button:has-text('Next')",
                "button:has-text('Continue')",
                "button:has-text('Save & Continue')",
                "button:has-text('Save and Continue')",
                "button:has-text('Proceed')",
                "button:has-text('Review')",
                "button:has-text('Next step')",
                "input[type='button'][value='Next']",
                "input[type='button'][value='Continue']"
            ]
            
            next_clicked = False
            for selector in next_selectors:
                try:
                    loc = page.locator(selector)
                    count = loc.count()
                    for idx in range(count):
                        btn = loc.nth(idx)
                        if btn.is_visible() and btn.is_enabled():
                            button_text = btn.inner_text().strip() or btn.get_attribute("value") or "Next"
                            yield f"🖱️ Clicking Next/Continue button: '{button_text}'"
                            btn.click()
                            page.wait_for_load_state("networkidle")
                            time.sleep(1.5) # Allow transition animation
                            next_clicked = True
                            step += 1
                            break
                    if next_clicked:
                        break
                except Exception:
                    pass
                    
            if not next_clicked:
                yield "ℹ️ No visible 'Next' or 'Continue' buttons found. Arrived at final step."
                break
                
        yield f"✨ Auto-fill complete. Successfully filled {filled_count} fields (including {custom_question_count} custom questions)."
        
        # Determine output directories and paths
        job_id = metadata.get("job_id", "unknown_job") if metadata else "unknown_job"
        company = metadata.get("company", "unknown_company") if metadata else "unknown_company"
        company_slug = re.sub(r'[\s/\\?%*:|"<>]', '_', company.lower())
        out_dir = os.path.join("data", "tailored_applications", f"{company_slug}_{job_id}")
        os.makedirs(out_dir, exist_ok=True)
        
        # Take a screenshot of the filled form
        screenshot_path = os.path.join(out_dir, "screenshot.png")
        try:
            page.screenshot(path=screenshot_path, full_page=True)
            yield f"📸 Captured page screenshot: {screenshot_path}"
        except Exception as ss_err:
            yield f"⚠️ Could not capture screenshot: {ss_err}"
            
        # Log custom questions
        if self.custom_questions_logged:
            q_json_path = os.path.join(out_dir, "custom_questions.json")
            try:
                with open(q_json_path, "w", encoding="utf-8") as qf:
                    json.dump(self.custom_questions_logged, qf, indent=2)
                yield f"💾 Saved custom questions log: {q_json_path}"
            except Exception as q_err:
                yield f"⚠️ Could not save custom questions log: {q_err}"
        
        # Step 4: Click Submit if requested
        if submit == True:
            yield "🚀 Submitting application..."
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Submit Application')",
                "button:has-text('Submit application')",
                "button:has-text('Apply')"
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    loc = page.locator(selector)
                    count = loc.count()
                    for idx in range(count):
                        btn = loc.nth(idx)
                        if btn.is_visible() and btn.is_enabled():
                            yield f"🖱️ Clicking Submit button: '{btn.inner_text().strip()}'"
                            btn.click()
                            page.wait_for_load_state("load")
                            submit_clicked = True
                            break
                    if submit_clicked:
                        break
                except Exception:
                    pass
            if submit_clicked:
                yield "🎉 Application submitted successfully!"
            else:
                yield "⚠️ Form filled, but could not find a visible 'Submit' button. User verification required."
                status_outcome = "partial"
        elif submit == "review":
            yield "⏳ Review Mode: Application filled and held for review. Notification queued."
            status_outcome = "review"
        else:
            yield "ℹ️ Simulation Mode: Form filled successfully. Submission skipped."
            
        # Log to telemetry database
        self._log_application(url, status_outcome, submit, metadata)

    def _detect_platform(self, url: str) -> str:
        """Determines the job application board platform from the URL."""
        url_lower = url.lower()
        if "lever.co" in url_lower:
            return "lever"
        if "greenhouse.io" in url_lower:
            return "greenhouse"
        if "workable.com" in url_lower:
            return "workable"
        if "linkedin.com" in url_lower or "linkedin" in url_lower:
            return "linkedin"
        if "ashbyhq.com" in url_lower or "ashby" in url_lower:
            return "ashby"
        if "smartrecruiters.com" in url_lower:
            return "smartrecruiters"
        if "icims.com" in url_lower:
            return "icims"
        if "taleo.net" in url_lower or "taleo" in url_lower:
            return "taleo"
        return "generic"

    def _find_form_elements(self, frame):
        """Locates all inputs and textareas in a frame and maps label associations."""
        elements = []
        inputs = frame.query_selector_all("input")
        textareas = frame.query_selector_all("textarea")
        
        label_map = {}
        labels = frame.query_selector_all("label")
        for label in labels:
            for_attr = label.get_attribute("for")
            text = label.inner_text().strip()
            if for_attr:
                label_map[for_attr] = text
                
        # Filter inputs
        for el in inputs:
            el_type = (el.get_attribute("type") or "text").lower()
            if el_type in ["hidden", "submit", "button", "checkbox", "radio", "image", "reset"]:
                continue
            if not el.is_visible():
                continue
                
            el_id = el.get_attribute("id") or ""
            label_text = label_map.get(el_id, "")
            
            if not label_text:
                parent = el.evaluate_handle("el => el.closest('label')")
                if parent.as_element():
                    label_text = parent.as_element().inner_text().strip()
                    
            elements.append((el, "input", label_text))
            
        # Filter textareas
        for el in textareas:
            if not el.is_visible():
                continue
            el_id = el.get_attribute("id") or ""
            label_text = label_map.get(el_id, "")
            if not label_text:
                parent = el.evaluate_handle("el => el.closest('label')")
                if parent.as_element():
                    label_text = parent.as_element().inner_text().strip()
                    
            elements.append((el, "textarea", label_text))
            
        return elements

    def _classify_field(self, element, label: str, platform: str) -> str:
        """Categorizes input element into standard field or custom question based on platform-specific rules."""
        el_id = (element.get_attribute("id") or "").lower()
        el_name = (element.get_attribute("name") or "").lower()
        el_placeholder = (element.get_attribute("placeholder") or "").lower()
        el_type = (element.get_attribute("type") or "").lower()
        aria_label = (element.get_attribute("aria-label") or "").lower()
        label_text = label.lower()
        
        combined = f"{el_id} {el_name} {el_placeholder} {aria_label} {label_text}".strip()
        
        if platform == "lever":
            if el_name == "name": return "name"
            if el_name == "email": return "email"
            if el_name == "phone": return "phone"
            if el_name == "resume" or el_type == "file": return "resume"
            if "linkedin" in el_name or "urls[linkedin]" in el_name: return "linkedin"
            if "github" in el_name or "urls[github]" in el_name: return "github"
            if "portfolio" in el_name or "urls[portfolio]" in el_name or "org" in el_name: return "portfolio"
            
        elif platform == "greenhouse":
            if el_id == "first_name" or el_name == "first_name": return "first_name"
            if el_id == "last_name" or el_name == "last_name": return "last_name"
            if el_id == "email" or el_name == "email": return "email"
            if el_id == "phone" or el_name == "phone": return "phone"
            if el_type == "file" or "resume" in combined: return "resume"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined: return "portfolio"
            
        elif platform == "workable":
            if el_name == "name" or el_id == "name": return "name"
            if el_name == "email" or el_id == "email": return "email"
            if el_name == "phone" or el_id == "phone": return "phone"
            if el_type == "file" or el_name == "resume": return "resume"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined: return "portfolio"

        elif platform == "linkedin":
            if el_type == "file" or "resume" in combined or "cv" in combined: return "resume"
            if "email" in combined or "login" in combined or "username" in combined: return "email"
            if "phone" in combined or "mobile" in combined: return "phone"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined or "blog" in combined: return "portfolio"
            if "first" in combined and "last" not in combined: return "first_name"
            if "last" in combined and "first" not in combined: return "last_name"
            if "name" in combined: return "name"
            
        elif platform == "ashby":
            if el_type == "file" or "resume" in combined or "cv" in combined: return "resume"
            if "email" in combined or "login" in combined or "username" in combined: return "email"
            if "phone" in combined or "mobile" in combined: return "phone"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined or "url" in combined: return "portfolio"
            if "first" in combined and "last" not in combined: return "first_name"
            if "last" in combined and "first" not in combined: return "last_name"
            if "name" in combined or "fullname" in combined: return "name"

        elif platform == "smartrecruiters":
            if el_type == "file" or "resume" in combined or "cv" in combined or "upload" in combined: return "resume"
            if el_id == "email" or "email" in combined or "login" in combined or "username" in combined: return "email"
            if el_id == "phoneNumber" or "phone" in combined or "mobile" in combined: return "phone"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined or "websiteurl" in combined: return "portfolio"
            if el_id == "firstName" or "first" in combined: return "first_name"
            if el_id == "lastName" or "last" in combined: return "last_name"

        elif platform == "icims":
            if el_type == "file" or "resume" in combined or "cv" in combined: return "resume"
            if "email" in combined or "login" in combined or "username" in combined: return "email"
            if "phone" in combined or "mobile" in combined: return "phone"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined: return "portfolio"
            if "first" in combined: return "first_name"
            if "last" in combined: return "last_name"
            if "name" in combined: return "name"

        elif platform == "taleo":
            if el_type == "file" or "resume" in combined or "cv" in combined: return "resume"
            if "email" in combined or "login" in combined or "username" in combined: return "email"
            if "phone" in combined or "mobile" in combined: return "phone"
            if "linkedin" in combined: return "linkedin"
            if "github" in combined: return "github"
            if "portfolio" in combined or "website" in combined: return "portfolio"
            if "first" in combined: return "first_name"
            if "last" in combined: return "last_name"
            if "name" in combined: return "name"
            
        if el_type == "file" or "resume" in combined or "cv" in combined or "upload" in combined:
            return "resume"
        if "email" in combined or "mail" in combined:
            return "email"
        if "linkedin" in combined:
            return "linkedin"
        if "github" in combined:
            return "github"
        if "portfolio" in combined or "website" in combined or "web_site" in combined or "homepage" in combined:
            return "portfolio"
        if "phone" in combined or "mobile" in combined or "tel" in combined or "phone_number" in combined:
            return "phone"
        if "name" in combined or "fullname" in combined or "full_name" in combined or "first" in combined or "last" in combined:
            return "name"
            
        return "custom_question"

    def _generate_custom_answer(self, question: str) -> str:
        """Queries Gemini to construct a tailored professional answer for custom questions."""
        prompt = f"""
You are a professional candidate filling out a job application.
Candidate profile:
{json.dumps(self.profile, indent=2)}

Please answer the following application question professionally, concisely, and under 150 words.
Do not include any greeting, intro, quotes, or formatting explanation. Write ONLY the raw text answer.

Question:
{question}
"""
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[AutoSubmitter] Custom answer generation error: {e}")
            return "I am highly interested in this role and look forward to contributing my technical skills and experience in software development."

    def _log_application(self, url: str, status: str, submit, metadata: dict):
        """Saves details of the application to data/application_history.json."""
        history_path = os.path.join("data", "application_history.json")
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        
        # Determine company & job title
        company = "Unknown Company"
        title = "Unknown Title"
        readiness_score = 50
        ats_score = 50
        job_id = "unknown_job"
        
        if metadata:
            company = metadata.get("company", company)
            title = metadata.get("title", title)
            readiness_score = metadata.get("readiness_score", readiness_score)
            ats_score = metadata.get("ats_score", ats_score)
            job_id = metadata.get("job_id", job_id)
            
        # Determine status string
        if status == "review":
            status_str = "Pending Review"
        elif submit == True and status == "success":
            status_str = "Submitted"
        elif status == "success":
            status_str = "Simulated"
        else:
            status_str = "Failed"
            
        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "company": company,
            "title": title,
            "url": url,
            "status": status_str,
            "readiness_score": readiness_score,
            "ats_score": ats_score,
            "job_id": job_id
        }
        
        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
                
        # Update existing record if it is a re-submission or transition of an existing job_id
        updated = False
        if job_id != "unknown_job":
            for idx, item in enumerate(history):
                if item.get("job_id") == job_id:
                    # Update status, timestamp, and scores
                    history[idx]["status"] = status_str
                    history[idx]["timestamp"] = record["timestamp"]
                    history[idx]["readiness_score"] = readiness_score
                    history[idx]["ats_score"] = ats_score
                    updated = True
                    break
        
        if not updated:
            history.append(record)
        
        try:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"[AutoSubmitter] Failed to log application history: {e}")
