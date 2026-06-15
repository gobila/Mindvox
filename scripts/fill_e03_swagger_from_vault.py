#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prepare_e03_raw_text_from_vault import (  # noqa: E402
    DEFAULT_NOTE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_VAULT_PATH,
    PreparedTranscript,
    prepare_transcript,
)


DEFAULT_SWAGGER_URL = "http://127.0.0.1:8000/docs"
DEFAULT_TOKEN = "dev-token"


def fill_swagger_from_prepared_transcript(
    *,
    prepared: PreparedTranscript,
    swagger_url: str = DEFAULT_SWAGGER_URL,
    token: str = DEFAULT_TOKEN,
    headless: bool = False,
    hold_seconds: int = 24 * 60 * 60,
) -> None:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed in this uv environment. Run: "
            "uv add --dev playwright && uv run playwright install chromium"
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(swagger_url, wait_until="networkidle")

        _authorize_swagger(page=page, token=token)
        operation = _open_e03_operation(page)
        _activate_try_it_out(operation)
        _fill_e03_form(operation=operation, prepared=prepared)

        print("")
        print("Swagger E03 preenchido visualmente.")
        print("Revise os campos na tela HTTP e clique em Execute quando quiser processar.")
        if hold_seconds > 0:
            print("A janela permanecera aberta. Para encerrar o script, pressione Ctrl+C.")
        try:
            page.wait_for_timeout(max(0, hold_seconds) * 1000)
        except KeyboardInterrupt:
            pass
        except PlaywrightTimeoutError:
            pass
        finally:
            browser.close()


def _authorize_swagger(*, page, token: str) -> None:
    authorize_button = page.get_by_role("button", name="Authorize").first
    if authorize_button.count() == 0:
        return

    authorize_button.click()
    value_input = page.locator('.modal-ux input[aria-label="auth-bearer-value"]')
    value_input.wait_for(state="visible", timeout=5000)
    value_input.fill(token)
    page.locator(".modal-ux button.authorize").click()
    page.get_by_role("button", name="Close").click()
    page.locator(".modal-ux").wait_for(state="hidden", timeout=5000)


def _open_e03_operation(page):
    operation = page.locator(".opblock").filter(
        has_text="/processed-transcriptions/v1.0.0"
    ).first
    operation.wait_for(state="visible", timeout=10000)
    try_button = operation.get_by_role("button", name="Try it out")
    if try_button.count() == 0 or not try_button.first.is_visible():
        operation.locator(".opblock-summary").click()
    operation.get_by_role("button", name="Try it out").wait_for(
        state="visible",
        timeout=5000,
    )
    return operation


def _activate_try_it_out(operation) -> None:
    button = operation.get_by_role("button", name="Try it out")
    if button.count() > 0 and button.first.is_visible():
        button.first.click()
    operation.locator("select").first.wait_for(
        state="visible",
        timeout=5000,
    )


def _fill_e03_form(*, operation, prepared: PreparedTranscript) -> None:
    _select_option_by_value(operation, "raw_text_file")

    raw_text_file_input = operation.locator('input[type="file"]').nth(1)
    raw_text_file_input.set_input_files(str(prepared.output_path.resolve()))
    raw_text_file_row = raw_text_file_input.locator("xpath=ancestor::tr[1]")
    _uncheck_send_empty_value(raw_text_file_row)

    for field_name, value in prepared.e03_form_metadata.items():
        if field_name == "input_type":
            continue
        field = operation.locator(f'input[placeholder="{field_name}"]')
        field.fill(str(value or ""))
        row = field.locator("xpath=ancestor::tr[1]")
        _uncheck_send_empty_value(row)


def _uncheck_send_empty_value(row) -> None:
    checkbox = row.locator('input[type="checkbox"]').first
    if checkbox.count() and checkbox.is_enabled() and checkbox.is_checked():
        checkbox.uncheck()


def _select_option_by_value(operation, value: str) -> None:
    selects = operation.locator("select")
    for index in range(selects.count()):
        select = selects.nth(index)
        option_values = select.locator("option").evaluate_all(
            "(options) => options.map((option) => option.value)"
        )
        if value in option_values:
            select.select_option(value)
            return
    raise RuntimeError(f"Swagger select option not found: {value}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare a transcript from the Obsidian Vault and fill the E03 "
            "Swagger form visually, without clicking Execute."
        )
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=DEFAULT_VAULT_PATH,
        help="Path to the Obsidian vault.",
    )
    parser.add_argument(
        "--note",
        type=Path,
        default=DEFAULT_NOTE,
        help="Note path relative to the vault, or an absolute note path.",
    )
    parser.add_argument(
        "--section",
        type=int,
        required=True,
        help="Capture section number inside _captura-rapida.md, for example 1.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the prepared .txt will be written.",
    )
    parser.add_argument(
        "--output-name",
        help="Optional output filename. Defaults to metadata-based filename.",
    )
    parser.add_argument(
        "--swagger-url",
        default=DEFAULT_SWAGGER_URL,
        help=f"Swagger UI URL. Default: {DEFAULT_SWAGGER_URL}",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("MINDVOX_API_TOKEN", "").strip() or DEFAULT_TOKEN,
        help="Bearer token to fill in Swagger Authorize. Default: MINDVOX_API_TOKEN or dev-token.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode. Useful only for automated checks.",
    )
    parser.add_argument(
        "--hold-seconds",
        type=int,
        default=24 * 60 * 60,
        help="How long to keep the filled browser open. Default: 86400.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    note_path = args.note if args.note.is_absolute() else args.vault / args.note

    try:
        prepared = prepare_transcript(
            note_path=note_path,
            section=args.section,
            output_dir=args.output_dir,
            output_name=args.output_name,
        )
        print(f"Arquivo preparado: {prepared.output_path}")
        print(f"Caminho absoluto: {prepared.output_path.resolve()}")
        print(f"Metadados E03: {prepared.metadata_path}")
        print(f"Caracteres: {prepared.char_count}")
        fill_swagger_from_prepared_transcript(
            prepared=prepared,
            swagger_url=args.swagger_url,
            token=args.token,
            headless=args.headless,
            hold_seconds=args.hold_seconds,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
