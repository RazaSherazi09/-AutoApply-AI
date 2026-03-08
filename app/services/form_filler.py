"""
Domain-specific form filling handlers for job application pages.

Includes handlers for LinkedIn Easy Apply, Greenhouse, Lever, Workday,
and a generic heuristic fallback. Falls back to MANUAL_REVIEW when
confidence is below 60%.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page

from app.models.resume import Resume


@dataclass
class ApplyResult:
    """Result of a form fill attempt."""
    status: str = "SUCCESS"  # SUCCESS, MANUAL_REVIEW, FAILED
    confidence: float = 1.0
    error: str = ""
    fields_filled: int = 0
    fields_total: int = 0


@dataclass
class UserProfile:
    """User data extracted from resume for form filling."""
    name: str = ""
    email: str = ""
    phone: str = ""
    resume_path: str = ""
    skills: list[str] = field(default_factory=list)
    experience_years: float = 0.0

    @classmethod
    def from_resume(cls, resume: Resume) -> UserProfile:
        data = json.loads(resume.structured_data) if resume.structured_data else {}
        return cls(
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            resume_path=resume.file_path,
            skills=data.get("skills", []),
            experience_years=data.get("experience_years", 0.0),
        )


# ── Base handler ABC ──

class BaseFormHandler(ABC):
    """Abstract base for domain-specific form handlers."""

    name: str = "base"

    @abstractmethod
    async def detect(self, page: Page) -> bool:
        """Return True if this handler can handle the current page."""
        ...

    @abstractmethod
    async def fill_and_submit(self, page: Page, profile: UserProfile) -> ApplyResult:
        """Fill out the application form and optionally submit."""
        ...


# ── LinkedIn Easy Apply ──

class LinkedInEasyApplyHandler(BaseFormHandler):
    """Handler for LinkedIn Easy Apply flow."""

    name = "linkedin"

    async def detect(self, page: Page) -> bool:
        url = page.url.lower()
        if "linkedin.com" not in url:
            return False
        easy_apply = await page.query_selector('[data-control-name="jobdetails_topcard_inapply"]')
        if not easy_apply:
            easy_apply = await page.query_selector('button.jobs-apply-button')
        return easy_apply is not None

    async def fill_and_submit(self, page: Page, profile: UserProfile) -> ApplyResult:
        result = ApplyResult(fields_total=0, fields_filled=0)
        try:
            # Click Easy Apply button
            apply_btn = await page.query_selector('button.jobs-apply-button')
            if apply_btn:
                await apply_btn.click()
                await page.wait_for_timeout(2000)

            # Fill multi-step form
            steps = 0
            max_steps = 10
            while steps < max_steps:
                steps += 1
                filled = await self._fill_current_step(page, profile, result)
                if not filled:
                    break

                # Look for Next or Submit button
                next_btn = await page.query_selector('button[aria-label="Continue to next step"]')
                submit_btn = await page.query_selector('button[aria-label="Submit application"]')

                if submit_btn:
                    result.confidence = result.fields_filled / max(result.fields_total, 1)
                    if result.confidence < 0.6:
                        result.status = "MANUAL_REVIEW"
                        return result
                    await submit_btn.click()
                    await page.wait_for_timeout(2000)
                    result.status = "SUCCESS"
                    return result
                elif next_btn:
                    await next_btn.click()
                    await page.wait_for_timeout(1500)
                else:
                    break

            result.status = "MANUAL_REVIEW"
            result.error = "Could not complete all form steps"
        except Exception as e:
            result.status = "FAILED"
            result.error = str(e)
            logger.exception("LinkedIn Easy Apply failed")

        return result

    async def _fill_current_step(
        self, page: Page, profile: UserProfile, result: ApplyResult
    ) -> bool:
        inputs = await page.query_selector_all('input:visible, textarea:visible, select:visible')
        if not inputs:
            return False
        for inp in inputs:
            result.fields_total += 1
            filled = await _heuristic_fill_input(page, inp, profile)
            if filled:
                result.fields_filled += 1
        return True


# ── Greenhouse ──

class GreenhouseHandler(BaseFormHandler):
    """Handler for Greenhouse ATS application forms."""

    name = "greenhouse"

    async def detect(self, page: Page) -> bool:
        url = page.url.lower()
        return "greenhouse.io" in url or "boards.greenhouse" in url

    async def fill_and_submit(self, page: Page, profile: UserProfile) -> ApplyResult:
        result = ApplyResult(fields_total=0, fields_filled=0)
        try:
            # Greenhouse uses standard form with id="application_form" or similar
            inputs = await page.query_selector_all(
                '#application_form input:visible, '
                '#application_form textarea:visible, '
                '#application_form select:visible, '
                'form input:visible, form textarea:visible, form select:visible'
            )
            result.fields_total = len(inputs)

            for inp in inputs:
                filled = await _heuristic_fill_input(page, inp, profile)
                if filled:
                    result.fields_filled += 1

            # File upload for resume
            file_input = await page.query_selector('input[type="file"]')
            if file_input and profile.resume_path:
                await file_input.set_input_files(profile.resume_path)
                result.fields_filled += 1

            result.confidence = result.fields_filled / max(result.fields_total, 1)
            if result.confidence < 0.6:
                result.status = "MANUAL_REVIEW"
            else:
                # Submit
                submit = await page.query_selector('input[type="submit"], button[type="submit"]')
                if submit:
                    await submit.click()
                    await page.wait_for_timeout(3000)
                    result.status = "SUCCESS"
                else:
                    result.status = "MANUAL_REVIEW"
                    result.error = "Submit button not found"

        except Exception as e:
            result.status = "FAILED"
            result.error = str(e)
            logger.exception("Greenhouse form fill failed")

        return result


# ── Lever ──

class LeverHandler(BaseFormHandler):
    """Handler for Lever ATS application forms."""

    name = "lever"

    async def detect(self, page: Page) -> bool:
        url = page.url.lower()
        return "lever.co" in url or "jobs.lever" in url

    async def fill_and_submit(self, page: Page, profile: UserProfile) -> ApplyResult:
        result = ApplyResult(fields_total=0, fields_filled=0)
        try:
            # Click "Apply for this job" button if present
            apply_btn = await page.query_selector('a.postings-btn-wrapper, .posting-btn-submit')
            if apply_btn:
                await apply_btn.click()
                await page.wait_for_timeout(2000)

            # Lever uses specific class names
            inputs = await page.query_selector_all(
                '.application-form input:visible, '
                '.application-form textarea:visible, '
                '.application-form select:visible, '
                'form input:visible, form textarea:visible'
            )
            result.fields_total = len(inputs)

            for inp in inputs:
                filled = await _heuristic_fill_input(page, inp, profile)
                if filled:
                    result.fields_filled += 1

            # Resume upload
            file_input = await page.query_selector('input[type="file"][name="resume"]')
            if not file_input:
                file_input = await page.query_selector('input[type="file"]')
            if file_input and profile.resume_path:
                await file_input.set_input_files(profile.resume_path)
                result.fields_filled += 1

            result.confidence = result.fields_filled / max(result.fields_total, 1)
            if result.confidence < 0.6:
                result.status = "MANUAL_REVIEW"
            else:
                submit = await page.query_selector(
                    'button[type="submit"], input[type="submit"], .postings-btn'
                )
                if submit:
                    await submit.click()
                    await page.wait_for_timeout(3000)
                    result.status = "SUCCESS"
                else:
                    result.status = "MANUAL_REVIEW"

        except Exception as e:
            result.status = "FAILED"
            result.error = str(e)
            logger.exception("Lever form fill failed")

        return result


# ── Workday ──

class WorkdayHandler(BaseFormHandler):
    """Handler for Workday ATS application forms."""

    name = "workday"

    async def detect(self, page: Page) -> bool:
        url = page.url.lower()
        return "myworkdayjobs.com" in url or "workday.com" in url

    async def fill_and_submit(self, page: Page, profile: UserProfile) -> ApplyResult:
        result = ApplyResult(fields_total=0, fields_filled=0)
        try:
            # Workday uses data-automation-id attributes
            await page.wait_for_timeout(3000)  # Workday pages load slowly

            apply_btn = await page.query_selector('[data-automation-id="jobApplyButton"]')
            if apply_btn:
                await apply_btn.click()
                await page.wait_for_timeout(3000)

            # Fill visible inputs
            inputs = await page.query_selector_all(
                'input:visible, textarea:visible, select:visible'
            )
            result.fields_total = len(inputs)

            for inp in inputs:
                filled = await _heuristic_fill_input(page, inp, profile)
                if filled:
                    result.fields_filled += 1

            # Resume upload
            file_input = await page.query_selector(
                'input[type="file"][data-automation-id="file-upload-input-ref"]'
            )
            if not file_input:
                file_input = await page.query_selector('input[type="file"]')
            if file_input and profile.resume_path:
                await file_input.set_input_files(profile.resume_path)
                result.fields_filled += 1

            result.confidence = result.fields_filled / max(result.fields_total, 1)
            if result.confidence < 0.6:
                result.status = "MANUAL_REVIEW"
            else:
                submit = await page.query_selector(
                    '[data-automation-id="bottom-navigation-next-button"], '
                    'button[type="submit"]'
                )
                if submit:
                    await submit.click()
                    await page.wait_for_timeout(3000)
                    result.status = "SUCCESS"
                else:
                    result.status = "MANUAL_REVIEW"

        except Exception as e:
            result.status = "FAILED"
            result.error = str(e)
            logger.exception("Workday form fill failed")

        return result


# ── Generic heuristic fallback ──

class GenericFormHandler(BaseFormHandler):
    """Heuristic-based form handler using input ID/name/label matching."""

    name = "generic"

    async def detect(self, page: Page) -> bool:
        # Always matches as last resort
        return True

    async def fill_and_submit(self, page: Page, profile: UserProfile) -> ApplyResult:
        result = ApplyResult(fields_total=0, fields_filled=0)
        try:
            forms = await page.query_selector_all('form')
            target_form = forms[0] if forms else page

            inputs = await target_form.query_selector_all(
                'input:visible, textarea:visible, select:visible'
            )
            result.fields_total = len(inputs)

            for inp in inputs:
                filled = await _heuristic_fill_input(page, inp, profile)
                if filled:
                    result.fields_filled += 1

            # File upload
            file_input = await target_form.query_selector('input[type="file"]')
            if file_input and profile.resume_path:
                await file_input.set_input_files(profile.resume_path)
                result.fields_filled += 1

            result.confidence = result.fields_filled / max(result.fields_total, 1)
            if result.confidence < 0.6:
                result.status = "MANUAL_REVIEW"
                result.error = f"Low confidence: {result.confidence:.2f}"
            else:
                submit = await target_form.query_selector(
                    'button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Apply")'
                )
                if submit:
                    # Don't auto-submit on generic forms — always manual review
                    result.status = "MANUAL_REVIEW"
                    result.error = "Generic form — requires manual confirmation"
                else:
                    result.status = "MANUAL_REVIEW"

        except Exception as e:
            result.status = "FAILED"
            result.error = str(e)
            logger.exception("Generic form fill failed")

        return result


# ── Shared heuristic input filler ──

async def _heuristic_fill_input(page: Page, element, profile: UserProfile) -> bool:
    """
    Map a form input to a profile field using ID, name, label, and placeholder heuristics.

    Returns True if the field was filled.
    """
    try:
        input_type = await element.get_attribute("type") or "text"
        if input_type in ("hidden", "submit", "button", "checkbox", "radio", "file"):
            return False

        # Gather identifiers
        input_id = (await element.get_attribute("id") or "").lower()
        input_name = (await element.get_attribute("name") or "").lower()
        placeholder = (await element.get_attribute("placeholder") or "").lower()
        label_text = ""

        # Try to find associated label
        if input_id:
            label = await page.query_selector(f'label[for="{input_id}"]')
            if label:
                label_text = (await label.inner_text() or "").lower()

        identifiers = f"{input_id} {input_name} {placeholder} {label_text}"

        # Map to profile fields
        if _matches(identifiers, ["email", "e-mail", "e_mail"]):
            await element.fill(profile.email)
            return True
        elif _matches(identifiers, ["phone", "tel", "mobile", "cell"]):
            await element.fill(profile.phone)
            return True
        elif _matches(identifiers, ["name", "full_name", "fullname", "your name"]):
            await element.fill(profile.name)
            return True
        elif _matches(identifiers, ["first_name", "firstname", "first name", "fname"]):
            parts = profile.name.split()
            await element.fill(parts[0] if parts else "")
            return True
        elif _matches(identifiers, ["last_name", "lastname", "last name", "lname", "surname"]):
            parts = profile.name.split()
            await element.fill(parts[-1] if len(parts) > 1 else "")
            return True
        elif _matches(identifiers, ["linkedin", "linked_in"]):
            return False  # Skip LinkedIn URL fields
        elif _matches(identifiers, ["website", "portfolio", "url", "github"]):
            return False  # Skip optional URL fields

        return False

    except Exception:
        return False


def _matches(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in the identifier text."""
    return any(kw in text for kw in keywords)


# ── Dispatcher ──

class FormFillerDispatcher:
    """
    Dispatches form filling to the appropriate domain handler.

    Tries handlers in order: LinkedIn → Greenhouse → Lever → Workday → Generic.
    """

    handlers: list[BaseFormHandler] = [
        LinkedInEasyApplyHandler(),
        GreenhouseHandler(),
        LeverHandler(),
        WorkdayHandler(),
        GenericFormHandler(),
    ]

    async def fill_from_url(self, url: str, resume: Resume) -> ApplyResult:
        """
        Open URL in Playwright and attempt to fill the application form.

        Uses the browser pool for managed page lifecycle.
        """
        from app.worker.browser_pool import BrowserPool

        profile = UserProfile.from_resume(resume)
        pool = BrowserPool.get_instance()

        async with pool.acquire_page() as page:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)

            for handler in self.handlers:
                if await handler.detect(page):
                    logger.info("Using {} handler for {}", handler.name, url)
                    return await handler.fill_and_submit(page, profile)

        return ApplyResult(status="MANUAL_REVIEW", error="No handler matched")
