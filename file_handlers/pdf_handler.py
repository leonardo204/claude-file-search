"""
PDF 파일 핸들러

이 모듈은 PDF 파일에서 텍스트를 추출하는 기능을 제공합니다.
"""

import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any

from file_handlers.base import FileHandler

logger = logging.getLogger("file_search.pdf_handler")

class PDFHandler(FileHandler):
    """PDF 파일 핸들러"""
    
    def get_supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자 목록을 반환합니다.
        
        Returns:
            지원하는 파일 확장자 목록
        """
        return ['.pdf']
    
    def get_type_description(self) -> str:
        """
        파일 형식에 대한 설명을 반환합니다.
        
        Returns:
            파일 형식 설명
        """
        return 'PDF'
    
    def extract_text(self, file_path: Path, max_content_sections: int = 10) -> List[Dict[str, Any]]:
        """
        PDF 파일에서 텍스트를 추출합니다.
        
        Args:
            file_path: 파일 경로
            max_content_sections: 처리할 최대 페이지 수
            
        Returns:
            페이지별 텍스트 정보 리스트
        """
        try:
            import PyPDF2
            
            logger.info(f"Extracting text from PDF file: {file_path}")
            
            pages = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                
                # 최대 페이지 수 제한
                for i in range(min(total_pages, max_content_sections)):
                    page = reader.pages[i]
                    text = page.extract_text()
                    
                    pages.append({
                        "section_number": i + 1,
                        "section_type": "page",
                        "text": text.strip() if text else ""
                    })
                
                if total_pages > max_content_sections:
                    pages.append({
                        "section_number": max_content_sections + 1,
                        "section_type": "page",
                        "text": f"... 추가 페이지 있음 (총 {total_pages}페이지 중 {max_content_sections}페이지까지만 처리) ..."
                    })
            
            return pages
        except Exception as e:
            logger.error(f"Error extracting text from PDF file {file_path}: {e}")
            logger.error(traceback.format_exc())
            return [{"section_number": 0, "section_type": "error", "text": f"PDF 파일 처리 중 오류 발생: {str(e)}"}]