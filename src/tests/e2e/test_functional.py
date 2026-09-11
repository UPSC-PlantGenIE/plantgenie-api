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

    def test_can_start_a_gene_list(self, page: Page, site):
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
        self, page: Page, browser: Browser, site
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
        self, page: Page, browser: Browser, site
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
    def test_can_blast_a_sequence_against_a_genome(
        self, page: Page, site
    ):
        # Ada is interested in figuring out which spruce gene sequences are similar
        # to one she has discovered. She found out that PlantGenIE has a BLAST interface,
        # which is a tool that can be used to search a sequence against a database.
        # She navigates to the page https://www.plantgenie.se/blast/
        page.goto(SITE_URL + "/blast/")

        expect(
            page.get_by_role("heading", name=re.compile(r"blast", re.IGNORECASE))
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
            page.get_by_text(re.compile(r"running|searching", re.IGNORECASE))
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
