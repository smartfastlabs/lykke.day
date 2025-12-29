"""Unit tests for printing utility functions."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_generate_pdf_from_page():
    """Test generate_pdf_from_page creates PDF."""
    # TODO: Move import to top if circular import can be resolved
    from planned.infrastructure.utils.printing import generate_pdf_from_page
    
    url = "https://example.com/test"
    
    # Mock playwright
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    mock_browser.new_page.return_value = mock_page
    mock_browser.close = AsyncMock()
    
    with patch("planned.infrastructure.utils.printing.async_playwright") as mock_playwright:
        mock_p = MagicMock()
        mock_p.__aenter__.return_value = mock_p
        mock_p.__aexit__.return_value = None
        mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value = mock_p
        
        with patch("planned.infrastructure.utils.printing.tempfile.NamedTemporaryFile") as mock_tmp:
            mock_tmp_file = MagicMock()
            mock_tmp_file.name = "/tmp/test.pdf"
            mock_tmp_file.close = MagicMock()
            mock_tmp.return_value = mock_tmp_file
            
            result = await generate_pdf_from_page(url)
            
            assert result == "/tmp/test.pdf"
            mock_page.goto.assert_called_once()
            mock_page.pdf.assert_called_once()
            mock_browser.close.assert_called_once()


@pytest.mark.asyncio
async def test_generate_pdf_from_page_with_custom_path():
    """Test generate_pdf_from_page with custom PDF path."""
    # TODO: Move import to top if circular import can be resolved
    from planned.infrastructure.utils.printing import generate_pdf_from_page
    
    url = "https://example.com/test"
    custom_path = "/custom/path/output.pdf"
    
    # Mock playwright
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    mock_browser.new_page.return_value = mock_page
    mock_browser.close = AsyncMock()
    
    with patch("planned.infrastructure.utils.printing.async_playwright") as mock_playwright:
        mock_p = MagicMock()
        mock_p.__aenter__.return_value = mock_p
        mock_p.__aexit__.return_value = None
        mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.return_value = mock_p
        
        result = await generate_pdf_from_page(url, pdf_path=custom_path)
        
        assert result == custom_path
        mock_page.pdf.assert_called_once_with(
            path=custom_path,
            width="3.5in",
            height="5.5in",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )


@pytest.mark.asyncio
async def test_send_pdf_to_printer():
    """Test send_pdf_to_printer sends PDF to printer."""
    # TODO: Move import to top if circular import can be resolved
    from planned.infrastructure.utils.printing import send_pdf_to_printer
    
    pdf_path = "/tmp/test.pdf"
    
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    
    with patch("planned.infrastructure.utils.printing.create_subprocess_exec") as mock_exec:
        mock_exec.return_value = mock_proc
        
        with patch("planned.infrastructure.utils.printing.aiofiles.os.remove") as mock_remove:
            await send_pdf_to_printer(pdf_path, delete_after=True)
            
            mock_exec.assert_called_once()
            mock_proc.wait.assert_called_once()
            mock_remove.assert_called_once_with(pdf_path)


@pytest.mark.asyncio
async def test_send_pdf_to_printer_no_delete():
    """Test send_pdf_to_printer without deleting PDF."""
    # TODO: Move import to top if circular import can be resolved
    from planned.infrastructure.utils.printing import send_pdf_to_printer
    
    pdf_path = "/tmp/test.pdf"
    
    mock_proc = AsyncMock()
    mock_proc.wait = AsyncMock(return_value=0)
    
    with patch("planned.infrastructure.utils.printing.create_subprocess_exec") as mock_exec:
        mock_exec.return_value = mock_proc
        
        with patch("planned.infrastructure.utils.printing.aiofiles.os.remove") as mock_remove:
            await send_pdf_to_printer(pdf_path, delete_after=False)
            
            mock_exec.assert_called_once()
            mock_proc.wait.assert_called_once()
            mock_remove.assert_not_called()

