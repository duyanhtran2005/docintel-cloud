import pytest
from pipelines.chunking import PDFChunker

def test_pdf_chunker_sliding_window():
    chunker = PDFChunker(chunk_size=10, overlap=2)
    sample_text = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10 Word11 Word12 Word13"
    
    chunks = chunker.chunk_text(sample_text)
    
    assert len(chunks) == 2
    assert "Word1" in chunks[0]
    assert "Word10" in chunks[0]
    # Kiểm tra overlap: Word9 và Word10 phải có mặt ở cả chunk 0 và chunk 1
    assert "Word9" in chunks[1]
    assert "Word10" in chunks[1]

def test_clean_text_nul_byte():
    chunker = PDFChunker()
    dirty_text = "DeepSeek\x00-V3.2 \x01Test\x00 String"
    cleaned = chunker.clean_text(dirty_text)
    
    assert "\x00" not in cleaned
    assert "\x01" not in cleaned
    assert cleaned == "DeepSeek-V3.2 Test String"
