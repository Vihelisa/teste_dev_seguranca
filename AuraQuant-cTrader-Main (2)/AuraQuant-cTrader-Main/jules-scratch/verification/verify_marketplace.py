from playwright.sync_api import sync_playwright, Page, expect

def verify_marketplace_page(page: Page):
    """
    This test verifies that the marketplace page loads and displays strategy cards.
    """
    # 1. Arrange: Go to the marketplace page.
    # The dev server is running on port 5173.
    page.goto("http://localhost:5173/marketplace")

    # 2. Wait for the heading to be visible.
    heading = page.get_by_role("heading", name="Robôs e Estratégias")
    expect(heading).to_be_visible()

    # 3. Wait for at least one strategy card to be rendered.
    # We can look for the "Ver Detalhes e Ativar" button that is in each card.
    expect(page.get_by_role("button", name="Ver Detalhes e Ativar")).to_have_count.above(0)

    # 4. Screenshot: Capture the final result for visual verification.
    page.screenshot(path="jules-scratch/verification/marketplace.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        verify_marketplace_page(page)
        browser.close()

if __name__ == "__main__":
    main()
