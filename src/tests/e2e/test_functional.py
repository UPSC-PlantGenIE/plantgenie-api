import re

import httpx
import pytest
from playwright.sync_api import Browser, Page, expect

pytestmark = pytest.mark.e2e

SITE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"


def create_account() -> str:
    response = httpx.post(f"{API_URL}/api/v2/accounts", timeout=10)
    response.raise_for_status()
    return response.json()["accountId"]


def sign_in(page: Page, account_id: str):
    page.goto(SITE_URL)
    page.evaluate(
        "accountId => localStorage.setItem('accountId', accountId)",
        account_id,
    )


class TestNewVisitor:
    def start_a_gene_list(self, page: Page, name: str, description: str):
        page.goto(SITE_URL + "/lists")
        page.get_by_role(
            "link", name=re.compile(r"new list", re.IGNORECASE)
        ).click()
        page.get_by_text(re.compile(r"picea abies", re.IGNORECASE)).click()
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()
        page.get_by_text(re.compile(r"genome - ", re.IGNORECASE)).click()
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()
        page.get_by_label(re.compile(r"list name", re.IGNORECASE)).fill(
            name
        )
        page.get_by_label(re.compile(r"description", re.IGNORECASE)).fill(
            description
        )
        page.get_by_role(
            "button", name=re.compile(r"create list", re.IGNORECASE)
        ).click()
        expect(page.get_by_role("heading", name=name)).to_be_visible()

    def test_can_start_a_gene_list(self, page: Page, site):
        # Ada wants to investigate some cold stress genes in Norway spruce.
        # She heard about this cool website where she can create gene lists against
        # the Norway spruce genome (and others) called PlantGenIE.

        # She navigates to the page and is welcomed with an explanation of the app
        page.goto(SITE_URL)
        expect(
            page.get_by_role(
                "heading", name=re.compile(r"plantgenie", re.IGNORECASE)
            )
        ).to_be_visible()

        # She sees two possibilities
        # (1) to create a new id
        generate_button = page.locator("#new-account-card").get_by_role(
            "button", name=re.compile(r"generate a new id", re.IGNORECASE)
        )
        expect(generate_button).to_be_visible()

        # (2) to use an existing one
        expect(
            page.locator("#returning-user").get_by_role(
                "button", name=re.compile(r"continue", re.IGNORECASE)
            )
        ).to_be_visible()

        # She has never been here before, so she has no account ID.
        # She takes the offer to have one made for her instead
        generate_button.click()

        # The site shows her the ID it just made, in groups of four so she can
        # copy it down, and warns her that losing it loses her lists
        account_id = page.get_by_text(
            re.compile(r"\d{4} \d{4} \d{4} \d{4}")
        )
        expect(account_id).to_be_visible()
        expect(page.get_by_role("alert")).to_contain_text(
            re.compile(r"lose|losing", re.IGNORECASE)
        )

        # She carries on to her lists
        page.get_by_role(
            "link", name=re.compile(r"continue|my lists", re.IGNORECASE)
        ).click()
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
        # the wizard opens on a list of taxa to choose from, with a disabled
        # continue button. In the list of taxa, she sees Norway spruce and
        # clicks on it
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

        # the next step asks which genome the list should be built against.
        # There is only one on offer for Norway spruce, so she takes it
        page.get_by_text(re.compile(r"genome - ", re.IGNORECASE)).click()
        page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()

        # the last step asks her to name the list, now that she knows what is
        # in it. The create button stays disabled until she does
        expect(
            page.get_by_role(
                "button", name=re.compile(r"create list", re.IGNORECASE)
            )
        ).to_be_disabled()
        page.get_by_label(re.compile(r"list name", re.IGNORECASE)).fill(
            "Ada's cold stress genes"
        )
        expect(
            page.get_by_role(
                "button", name=re.compile(r"create list", re.IGNORECASE)
            )
        ).to_be_enabled()

        # and a description, which is optional
        page.get_by_label(re.compile(r"description", re.IGNORECASE)).fill(
            "Known cold stress-related genes found in Norway spruce"
        )
        page.get_by_role(
            "button", name=re.compile(r"create list", re.IGNORECASE)
        ).click()

        # The list is created and she is taken to it.
        expect(
            page.get_by_role("heading", name="Ada's cold stress genes")
        ).to_be_visible()

        # She notices her list has a URL of its own
        assert re.search(r"/lists/.+", page.url)

    def test_returns_to_her_lists_on_the_same_computer(
        self, page: Page, site
    ):
        # Ada already has an account and a list from an earlier visit
        # She navigates to plantgenie on her laptop that she used for the previous visit
        sign_in(page, create_account())
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )

        page.goto(SITE_URL)

        # She is navigated directly to her lists page
        expect(
            page.get_by_role(
                "heading", name=re.compile(r"my lists", re.IGNORECASE)
            )
        ).to_be_visible()

        # She sees the lists she created before
        expect(
            page.get_by_role("link", name="Ada's cold stress genes")
        ).to_be_visible()

    def test_a_bookmarked_list_opens_directly(self, page: Page, site):
        # Ada bookmarks one of her lists
        sign_in(page, create_account())
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )
        bookmarked_list_url = page.url

        # The next day she opens the bookmark directly
        page.goto(bookmarked_list_url)

        # and lands on her list, not back on the list index
        expect(
            page.get_by_role("heading", name="Ada's cold stress genes")
        ).to_be_visible()
        assert page.url == bookmarked_list_url

    def test_signs_in_from_another_computer(
        self, page: Page, browser: Browser, site
    ):
        # Ada makes a list at work, and writes her account ID down
        adas_account_id = create_account()
        sign_in(page, adas_account_id)
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )

        # That evening she opens the site on her laptop at home, which has never
        # been to the site and so has nothing remembered
        laptop = browser.new_context()
        laptop_page = laptop.new_page()
        laptop_page.goto(SITE_URL)

        # She pastes in the ID she wrote down
        laptop_page.get_by_role(
            "textbox", name=re.compile(r"account id", re.IGNORECASE)
        ).fill(adas_account_id)
        laptop_page.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()

        # and her list came with her
        expect(
            laptop_page.get_by_role("link", name="Ada's cold stress genes")
        ).to_be_visible()

        laptop.close()

    def test_a_mistyped_id_is_refused(self, page: Page, site):
        # Ada has an account, and opens the site on a computer that has
        # never been to it
        adas_account_id = create_account()
        page.goto(SITE_URL)

        # She types her ID from memory, but gets the last digit wrong
        mistyped_last_digit = str((int(adas_account_id[-1]) + 1) % 10)
        mistyped_account_id = adas_account_id[:-1] + mistyped_last_digit
        existing_account_card = page.locator("#returning-user")
        existing_account_card.get_by_label(
            re.compile(r"account id", re.IGNORECASE)
        ).fill(mistyped_account_id)
        existing_account_card.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()

        # She is told the ID wasn't recognised
        expect(page.get_by_role("alert")).to_contain_text(
            re.compile(r"recognised", re.IGNORECASE)
        )

        # and she stays where she is, free to try again
        expect(page).not_to_have_url(re.compile(r"/lists"))
        expect(
            existing_account_card.get_by_role(
                "button", name=re.compile(r"continue", re.IGNORECASE)
            )
        ).to_be_visible()

    def test_someone_else_signs_in_on_a_shared_computer(
        self, page: Page, site
    ):
        # Ada uses the lab's shared computer to make a list
        sign_in(page, create_account())
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )

        # Later Bob sits down at the same computer. He has an account of
        # his own, and opens the site
        bobs_account_id = create_account()
        page.goto(SITE_URL)

        # The site drops him into whoever used it last. That is not Bob,
        # so he logs out
        expect(
            page.get_by_role("link", name="Ada's cold stress genes")
        ).to_be_visible()
        page.get_by_role(
            "button", name=re.compile(r"log out", re.IGNORECASE)
        ).click()

        # He pastes in his own ID
        existing_account_card = page.locator("#returning-user")
        existing_account_card.get_by_label(
            re.compile(r"account id", re.IGNORECASE)
        ).fill(bobs_account_id)
        existing_account_card.get_by_role(
            "button", name=re.compile(r"continue", re.IGNORECASE)
        ).click()

        # and sees his own, empty, lists rather than Ada's
        expect(
            page.get_by_role(
                "heading", name=re.compile(r"no lists yet", re.IGNORECASE)
            )
        ).to_be_visible()
        expect(
            page.get_by_role("link", name="Ada's cold stress genes")
        ).to_have_count(0)

    def test_multiple_users_can_keep_their_own_lists(
        self, page: Page, browser: Browser, site
    ):
        # Ada makes herself a list, as before.
        sign_in(page, create_account())
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )

        # Bob is in a different lab and has never met Ada. He has an account of
        # his own, and navigates to the page
        bobs_computer = browser.new_context()
        bobs_page = bobs_computer.new_page()
        sign_in(bobs_page, create_account())
        bobs_page.goto(SITE_URL + "/lists")

        # Another researcher's lists should not be visible as they should be user-specific
        # After navigating to the page, he sees, as expected, no lists have been created yet.
        expect(
            bobs_page.get_by_role(
                "heading", name=re.compile(r"no lists yet", re.IGNORECASE)
            )
        ).to_be_visible()

        bobs_computer.close()

    def test_a_list_url_is_private_to_its_owner(
        self, page: Page, browser: Browser, site
    ):
        # Ada makes herself a list, which lives at its own URL
        sign_in(page, create_account())
        self.start_a_gene_list(
            page,
            "Ada's cold stress genes",
            "Known cold stress-related genes found in Norway spruce",
        )
        adas_list_url = page.url

        # Bob has been using the site on his own computer, with his own account
        bobs_computer = browser.new_context()
        bobs_page = bobs_computer.new_page()
        sign_in(bobs_page, create_account())
        bobs_page.goto(SITE_URL + "/lists")
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
            bobs_page.get_by_role(
                "heading", name="Ada's cold stress genes"
            )
        ).to_have_count(0)

        bobs_computer.close()


SPRUCE_QUERY_HEADER = ">adas-test-sequence"
SPRUCE_QUERY = """\
ATGGAAGATTCACAAATTGGTCTCGTGAAACGGATTGTTCATGATGGAGATAATTTATCAGTAGAAAACA
CGGATCATGGAGTGAAAGATCAACACGAGACCACTCCAGTGAGCTTGAATATAGAAGATGGCCGTAAGGA
GCTGGGTATTTTAGAAGATTTTGATAGCAAAATACCTCCATGGAGGGAGCAGATATCTTTCCGTGGGATT
TTTGTGAGCTTCGTGATAGGAACCGTCTTCAGTATCATTGTTATGAATCTCAATCTCACCACTGGATTGG
CTCCCGCCATGAATGTTTCTGCTGGGCTGCTGGGCTTCGTATTCATGAAATCGTGGAGCAAACTCCTGAT
GAAGTTTGGATTACTGAAAGTTCCTTTCACGAGGCAAGAGAATACTGTAATCCAGACTTGTATTGTGGCG
TGTTACAGCCTTGCATACGGTGGAGGATTTGGATCCTATGTGTTGGGATTGAATAGAAAAACCTATGAGC
GGGCAGGTGTGAACACTCCAGGTAATACGCCCGATACAGTAAAGGAACCCACTATTGCCTGGATGATTGG
ATTTCTGTTTCTAGTTACATTCGTGGGCATTATAGCACTGGTGCCTCTGCGAAAGGTCCTTATCATTGAC
"""


FASTA_QUERY = ">PA_chr01_G000001.mRNA.1\n" + SPRUCE_QUERY


class TestBlastSearch:
    def test_can_blast_a_sequence_against_a_genome(self, page: Page, site):
        # Ada is interested in figuring out which spruce gene sequences are similar
        # to one she has discovered. She found out that PlantGenIE has a BLAST interface,
        # which is a tool that can be used to search a sequence against a database.
        # She navigates to the page https://www.plantgenie.se/blast/
        page.goto(SITE_URL + "/blast/")

        expect(
            page.get_by_role(
                "heading", name=re.compile(r"blast", re.IGNORECASE)
            )
        ).to_be_visible()

        # She sees a dropdown menu with a label - choose database
        database_dropdown = page.get_by_label(
            re.compile(r"choose database", re.IGNORECASE)
        )
        expect(database_dropdown).to_be_enabled()

        # She sees a disabled dropdown with a label - choose program. She reasons
        # it stays that way until the site knows what she means to search
        program_dropdown = page.get_by_label(
            re.compile(r"choose program", re.IGNORECASE)
        )
        expect(program_dropdown).to_be_disabled()

        # She sees a text box with a label "Query", which she safely assumes is the
        # place where she can paste a DNA sequence. There is also a search button
        # underneath which is currently disabled.
        query_box = page.get_by_label(re.compile(r"query", re.IGNORECASE))
        search_button = page.get_by_role(
            "button", name=re.compile(r"search", re.IGNORECASE)
        )
        expect(query_box).to_be_empty()
        expect(search_button).to_be_disabled()

        # She pastes her sequence into the query box
        query_box.fill(SPRUCE_QUERY)

        # She expected that the search button would be enabled, but that did not
        # happen. She does notice that there is a red error message stating that her query
        # must follow FASTA format guidelines exactly
        expect(page.get_by_role("alert")).to_contain_text(
            re.compile(r"fasta", re.IGNORECASE)
        )
        expect(search_button).to_be_disabled()

        # Of course - she forgot the header line. She adds one naming her sequence,
        # and the complaint disappears
        query_box.fill(FASTA_QUERY)
        expect(page.get_by_role("alert")).to_have_count(0)

        # Now she chooses what to search against. The dropdown offers her every
        # genome and annotation PlantGenIE hosts, and she takes the spruce coding
        # sequences, being after genes rather than raw genome
        database_dropdown.select_option("picab-v2.0-cds")

        # Having chosen a nucleotide database, the program dropdown wakes up and
        # offers the programs that can search one. She takes blastn, the
        # nucleotide-against-nucleotide search
        expect(program_dropdown).to_be_enabled()
        program_dropdown.select_option("blastn")

        # Everything the search needs is filled in, so the button comes alive
        expect(search_button).to_be_enabled()
        search_button.click()

        # Searching takes a moment, and she is told the job is running rather than
        # being left staring at an unchanged page
        expect(
            page.get_by_text(
                re.compile(r"running|searching", re.IGNORECASE)
            )
        ).to_be_visible()

        # The hits come back as a table. The best one is the gene her sequence
        # came from, matched along its whole length - so the query and subject
        # columns of that row name the same gene
        best_hit = page.get_by_role("row").filter(
            has=page.get_by_role("cell", name="PA_chr01_G000001.mRNA.1")
        )
        expect(best_hit.first).to_be_visible(timeout=60000)
        expect(
            best_hit.first.get_by_role("cell", name="100.000")
        ).to_be_visible()
