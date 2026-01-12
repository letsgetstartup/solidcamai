import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5173/dashboard.html?dev=1"

def test_dashboard_machine_list(page: Page):
    """Verifies that the dashboard loads and displays the simulated machine."""
    page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
    page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
    
    print(f"Navigating to {BASE_URL}")
    page.goto(BASE_URL)

    # 1. Verify Authentication Bypass and Page Load
    expect(page).to_have_title("SIMCO AI | CNC Management Dashboard")
    expect(page.locator("h2", has_text="CNC Machine Discovery")).to_be_visible()
    
    # Wait for machine list table to be present
    expect(page.locator("table")).to_be_visible()
    
    print("DEBUG: Page content loaded. Waiting for machine...")
    
    # Check if empty state is showing
    empty_state = page.locator("td", has_text="No machines discovered yet")
    if empty_state.is_visible():
        print("DEBUG: Found empty state. Waiting for data update...")
    
    # The '127.0.0.1' text comes from the machine_id
    machine_row = page.locator("tr", has_text="127.0.0.1")
    
    try:
        expect(machine_row).to_be_visible(timeout=30000)
    except AssertionError:
        print("DEBUG: Timed out waiting for machine. Taking screenshot.")
        # Print table text content
        print(f"DEBUG: Table Text: {page.locator('tbody').text_content()}")
        raise

    # 2. Verify Status
    # Status cell contains "ACTIVE", "RUNNING", or "IDLE"
    status_cell = machine_row.locator(".status-cell")
    import re
    expect(status_cell).to_contain_text(re.compile(r"ACTIVE|RUNNING|IDLE"))

    # 3. Verify Pulse
    pulse = status_cell.locator(".pulse.active")
    try:
        expect(pulse).to_be_visible()
    except AssertionError:
        print(f"DEBUG: Status Cell HTML: {status_cell.inner_html()}")
        raise

def test_manage_modal(page: Page):
    """Verifies that clicking 'Manage' opens the modal with data."""
    page.goto(BASE_URL)

    # 1. Find the machine row
    machine_row = page.locator("tr", has_text="127.0.0.1")
    expect(machine_row).to_be_visible(timeout=10000)

    # 2. Click Manage
    manage_btn = machine_row.locator("button.cta-button", has_text="Manage")
    manage_btn.click()

    # 3. Verify Modal Appears
    modal = page.locator("#manage-modal")
    expect(modal).to_be_visible()

    # 4. Verify Content
    modal_title = page.locator("#modal-title")
    expect(modal_title).to_contain_text("Managing 127.0.0.1")

    # Metrics should be loaded
    metrics_card = page.locator(".metrics-card")
    expect(metrics_card).to_contain_text("spindle_load")
    
    # Close modal
    page.locator(".close").click()
    expect(modal).not_to_be_visible()
