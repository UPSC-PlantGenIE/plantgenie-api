import re

import pytest
from playwright.sync_api import Browser, Page, expect

pytestmark = pytest.mark.e2e

SITE_URL = "http://localhost:5173"


class TestNewVisitor:
    def start_a_gene_list(self, page: Page, name: str, description: str):
        page.goto(SITE_URL)
        page.get_by_role(
            "link", name=re.compile(r"new list", re.IGNORECASE)
        ).click()
        page.get_by_label(re.compile(r"list name", re.IGNORECASE)).fill(name)
        page.get_by_label(re.compile(r"description", re.IGNORECASE)).fill(
            description
        )
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()
        page.get_by_text(re.compile(r"picea abies", re.IGNORECASE)).click()
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()
        page.get_by_text(re.compile(r"genome - ", re.IGNORECASE)).click()
        page.get_by_role(
            "button", name=re.compile(r"create list", re.IGNORECASE)
        ).click()
        expect(page.get_by_role("heading", name=name)).to_be_visible()

    def test_can_start_a_gene_list(self, page: Page, live_server):
        # Ada wants to investigate some cold stress genes in Norway spruce.
        # She heard about this cool website where she can create gene lists against
        # the Norway spruce genome (and others) called PlantGenIE.

        # She navigates to the page
        page.goto(SITE_URL)
        # and sees a heading "my lists"
        expect(
            page.get_by_role(
                "heading", name=re.compile(r"my lists", re.IGNORECASE)
            )
        ).to_be_visible()

        # she doesn't see any lists, which makes sense because she hasn't created any yet.
        expect(
            page.get_by_role(
                "heading", name=re.compile(r"no lists yet", re.IGNORECASE)
            )
        ).to_be_visible()

        # She sees a button inviting her to create a new list, so she clicks on it
        page.get_by_role(
            "link", name=re.compile(r"new list", re.IGNORECASE)
        ).click()
        # she is now sees a wizard page with two inputs and a disabled continue button
        expect(
            page.get_by_role(
                "button", name=re.compile(r"continue", re.IGNORECASE)
            )
        ).to_be_disabled()

        # The first text box indicates it is for the list name, so she enters a name
        page.get_by_label(re.compile(r"list name", re.IGNORECASE)).fill(
            "Ada's cold stress genes"
        )
        # She notices while typing the continue button becomes active, "hmm.. a list requires a name"
        expect(
            page.get_by_role(
                "button", name=re.compile(r"continue", re.IGNORECASE)
            )
        ).to_be_enabled()

        # The 2nd text box asks for a description of the list, so she enters one:
        page.get_by_label(re.compile(r"description", re.IGNORECASE)).fill(
            "Known cold stress-related genes found in Norway spruce"
        )
        # she clicks the continue button
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()

        # she now sees the next step of the wizard, a list of taxa to select from
        # and a disabled continue button. In the list of taxa, she sees Norway spruce and clicks on it
        expect(
            page.get_by_role(
                "button", name=re.compile(r"continue", re.IGNORECASE)
            )
        ).to_be_disabled()
        page.get_by_text(re.compile(r"picea abies", re.IGNORECASE)).click()
        # and sees that the little circle next to it becomes filled in
        expect(
            page.get_by_role(
                "radio", name=re.compile(r"picea abies", re.IGNORECASE)
            )
        ).to_be_checked()
        # and the continue button becomes enabled
        expect(
            page.get_by_role(
                "button", name=re.compile(r"continue", re.IGNORECASE)
            )
        ).to_be_enabled()
        # she clicks the continue button
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()

        # the last step of the wizard asks which genome the list should be built
        # against. There is only one on offer for Norway spruce, so she takes it
        page.get_by_text(re.compile(r"genome - ", re.IGNORECASE)).click()
        page.get_by_role(
            "button", name=re.compile(r"create list", re.IGNORECASE)
        ).click()

        # The list is created and she is taken to it.
        expect(
            page.get_by_role("heading", name="Ada's cold stress genes")
        ).to_be_visible()

        # She notices her list has a URL of its own
        assert re.search(r"/lists/.+", page.url)

    def test_multiple_users_can_keep_their_own_lists(
        self, page: Page, browser: Browser, live_server
    ):
        # Ada makes herself a list, as before.
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )

        # Bob is in a different lab and has never used the site before
        # and has certainly never met Ada. He navigates to the page
        bobs_computer = browser.new_context()
        bobs_page = bobs_computer.new_page()
        bobs_page.goto(SITE_URL)

        # Another researcher's lists should not be visible as they should be user-specific
        # After navigating to the page, he sees, as expected, no lists have been created yet.
        expect(
            bobs_page.get_by_role(
                "heading", name=re.compile(r"no lists yet", re.IGNORECASE)
            )
        ).to_be_visible()

        bobs_computer.close()

    def test_a_list_url_is_private_to_its_owner(
        self, page: Page, browser: Browser, live_server
    ):
        # Ada makes herself a list, which lives at its own URL
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )
        adas_list_url = page.url

        # Bob has been using the site on his own computer
        bobs_computer = browser.new_context()
        bobs_page = bobs_computer.new_page()
        bobs_page.goto(SITE_URL)
        expect(
            bobs_page.get_by_role(
                "heading", name=re.compile(r"no lists yet", re.IGNORECASE)
            )
        ).to_be_visible()

        # Ada sends him her link by mistake, and he opens it
        bobs_page.goto(adas_list_url)

        # The list is not his, so he is told it cannot be loaded rather than
        # being shown its contents
        expect(bobs_page.get_by_role("alert")).to_be_visible()
        expect(
            bobs_page.get_by_role("heading", name="Ada's cold stress genes")
        ).to_have_count(0)

        bobs_computer.close()
