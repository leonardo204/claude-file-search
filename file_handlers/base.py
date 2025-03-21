"""
파일 핸들러 추상 클래스 정의

이 모듈은 다양한 파일 형식을 처리하기 위한 추상 클래스와 레지스트리를 제공합니다.
각 파일 형식별 핸들러는 이 추상 클래스를 상속하여 구현합니다.
"""

import abc
from pathlib import Path
from typing import List, Dict, Any, Optional

class FileHandler(abc.ABC):
    """파일 핸들러 추상 클래스"""
    
    @abc.abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        이 핸들러가 지원하는 파일 확장자 목록을 반환합니다.
        
        Returns:
            지원하는 파일 확장자 목록 (예: ['.pptx', '.ppt'])
        """
        pass
    
    @abc.abstractmethod
    def get_type_description(self) -> str:
        """
        이 핸들러가 처리하는 파일 형식에 대한 설명을 반환합니다.
        
        Returns:
            파일 형식 설명 (예: 'PowerPoint')
        """
        pass
    
    @abc.abstractmethod
    def extract_text(self, file_path: Path, max_content_sections: int = 10) -> List[Dict[str, Any]]:
        """
        파일에서 텍스트를 추출합니다.
        
        Args:
            file_path: 파일 경로
            max_content_sections: 처리할 최대 섹션 수 (슬라이드, 페이지 등)
            
        Returns:
            섹션별 텍스트 정보 리스트 (예: [{'section_number': 1, 'text': '내용...'}])
        """
        pass
    
    def can_handle(self, file_path: Path) -> bool:
        """
        이 핸들러가 지정된 파일을 처리할 수 있는지 확인합니다.
        
        Args:
            file_path: 확인할 파일 경로
            
        Returns:
            처리 가능 여부
        """
        return file_path.suffix.lower() in self.get_supported_extensions()

class FileHandlerRegistry:
    """파일 핸들러 레지스트리"""
    
    def __init__(self):
        self.handlers = []
    
    def register_handler(self, handler: FileHandler) -> None:
        """
        핸들러를 레지스트리에 등록합니다.
        
        Args:
            handler: 등록할 파일 핸들러
        """
        self.handlers.append(handler)
    
    def get_handler_for_file(self, file_path: Path) -> Optional[FileHandler]:
        """
        지정된 파일을 처리할 수 있는 핸들러를 반환합니다.
        
        Args:
            file_path: 처리할 파일 경로
            
        Returns:
            파일을 처리할 수 있는 핸들러 또는 None
        """
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler
        return None
    
    def can_handle_file(self, file_path: Path, file_type: Optional[str] = None) -> bool:
        """
        레지스트리에 등록된 핸들러 중 하나가 지정된 파일을 처리할 수 있는지 확인합니다.
        
        Args:
            file_path: 확인할 파일 경로
            file_type: 필터링할 파일 형식 (지정된 경우 해당 형식만 처리)
            
        Returns:
            처리 가능 여부
        """
        for handler in self.handlers:
            if handler.can_handle(file_path):
                if file_type is None:
                    return True
                elif file_type.lower() in handler.get_type_description().lower():
                    return True
        return False