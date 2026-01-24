import asyncio
import tempfile
from asyncio.subprocess import create_subprocess_exec

from playwright.async_api import async_playwright

APP_URL = "http://localhost:3000/day/print"
PRINTER_NAME = "HP_OfficeJet_Pro_9010_series"
MEDIA_NAME = "Custom.252x396"  # 3.5in x 5.5in (252 x 396 points)


async def generate_pdf_from_page(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle")
        await page.wait_for_selector("text=Ready")

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


async def send_pdf_to_printer(pdf_path: str):
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

    # os.remove(pdf_path)


async def main():
    pdf_path = await generate_pdf_from_page(APP_URL)
    print("PDF Saved At: ", pdf_path)
    await send_pdf_to_printer(pdf_path)


if __name__ == "__main__":
    asyncio.run(main())
