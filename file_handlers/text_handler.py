"""
텍스트 파일 핸들러

이 모듈은 다양한 텍스트 파일에서 내용을 추출하는 기능을 제공합니다.
"""

import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any

from file_handlers.base import FileHandler

logger = logging.getLogger("file_search.text_handler")

class TextHandler(FileHandler):
    """텍스트 파일 핸들러"""
    
    def get_supported_extensions(self) -> List[str]:
        """
        지원하는 파일 확장자 목록을 반환합니다.
        
        Returns:
            지원하는 파일 확장자 목록
        """
        return ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv', '.ini', '.conf', '.log']
    
    def get_type_description(self) -> str:
        """
        파일 형식에 대한 설명을 반환합니다.
        
        Returns:
            파일 형식 설명
        """
        return 'Text'
    
    def extract_text(self, file_path: Path, max_content_sections: int = 10) -> List[Dict[str, Any]]:
        """
        텍스트 파일에서 내용을 추출합니다.
        
        Args:
            file_path: 파일 경로
            max_content_sections: 처리할 최대 섹션 수 (여기서는 줄 그룹 단위로 분리)
            
        Returns:
            줄 그룹별 텍스트 정보 리스트
        """
        try:
            logger.info(f"Extracting text from text file: {file_path}")
            
            # 여러 인코딩 시도
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    content = file_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return [{"section_number": 0, "section_type": "error", "text": "텍스트 파일 인코딩을 판단할 수 없습니다."}]
            
            lines = content.splitlines()
            total_lines = len(lines)
            
            # 최대 줄 수 제한 (섹션당 적절한 줄 수 계산)
            lines_per_section = max(20, total_lines // max_content_sections)
            sections = []
            
            for i in range(0, min(total_lines, max_content_sections * lines_per_section), lines_per_section):
                end_idx = min(i + lines_per_section, total_lines)
                section_text = '\n'.join(lines[i:end_idx])
                
                sections.append({
                    "section_number": (i // lines_per_section) + 1,
                    "section_type": "text_chunk",
                    "text": section_text
                })
            
            if total_lines > max_content_sections * lines_per_section:
                sections.append({
                    "section_number": len(sections) + 1,
                    "section_type": "text_chunk",
                    "text": f"... 추가 내용 있음 (총 {total_lines}줄 중 {max_content_sections * lines_per_section}줄까지만 처리) ..."
                })
            
            return sections
        except Exception as e:
            logger.error(f"Error extracting text from text file {file_path}: {e}")
            logger.error(traceback.format_exc())
            return [{"section_number": 0, "section_type": "error", "text": f"텍스트 파일 처리 중 오류 발생: {str(e)}"}]