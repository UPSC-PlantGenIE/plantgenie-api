import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_wizard_landing_renders(page: Page):
    page.goto("http://localhost:5173")
    expect(
        page.get_by_role("heading", name=re.compile(r"name your list", re.I))
    ).to_be_visible()
