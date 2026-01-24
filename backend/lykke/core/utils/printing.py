import contextlib
import tempfile
from asyncio.subprocess import create_subprocess_exec

import aiofiles.os
from playwright.async_api import async_playwright

APP_URL = "https://master-bedroom.local/day/today/print"
PRINTER_NAME = "HP_OfficeJet_Pro_9010_series_5FB872"
MEDIA_NAME = "Custom.252x396"  # 3.5in x 5.5in (252 x 396 points)


async def generate_pdf_from_page(
    url: str,
    pdf_path: str | None = None,
) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle")
        await page.wait_for_selector("text=Your Agenda (P1)")

        if pdf_path is None:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                pdf_path = tmp_file.name

        # PDF page is exactly 3.5" x 5.5"
        await page.pdf(
            path=pdf_path,
            width="3.5in",
            height="5.5in",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )

        await browser.close()

    return pdf_path


async def send_pdf_to_printer(
    pdf_path: str,
    delete_after: bool = True,
) -> None:
    cmd = [
        "lp",
        "-d",
        PRINTER_NAME,
        "-o",
        f"media={MEDIA_NAME}",
        "-o",
        "scaling=100",  # don't auto-rescale, print at 100%
        pdf_path,
    ]

    proc = await create_subprocess_exec(*cmd)
    await proc.wait()

    if delete_after:
        with contextlib.suppress(FileExistsError):
            await aiofiles.os.remove(pdf_path)
