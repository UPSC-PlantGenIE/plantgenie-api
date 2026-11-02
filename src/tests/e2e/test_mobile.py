import re

import pytest
from playwright.sync_api import Page, expect

from .test_functional import SITE_URL, create_account, sign_in

pytestmark = pytest.mark.e2e


@pytest.fixture(autouse=True)
def phone_screen(page: Page):
    page.set_viewport_size({"width": 375, "height": 667})


class TestOnAPhone:
    def test_navbar_fits(self, page: Page, site):
        # Ada checks her lists on her phone
        account_id = create_account()
        sign_in(page, account_id)
        page.goto(SITE_URL + "/lists")
        expect(
            page.get_by_role(
                "heading", name=re.compile(r"my lists", re.IGNORECASE)
            )
        ).to_be_visible()

        # Everything she needs in the navbar is fully on screen
        for control in [
            page.get_by_role("link", name="PlantGenIE"),
            page.get_by_role("link", name="Lists", exact=True),
            page.get_by_role("link", name="Blast", exact=True),
            page.get_by_role(
                "button", name=re.compile(r"log out", re.IGNORECASE)
            ),
        ]:
            expect(control).to_be_in_viewport(ratio=1)

        # Her long account ID is left out to make room
        expect(page.get_by_text(account_id)).to_be_hidden()

        # and the page does not scroll sideways
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
