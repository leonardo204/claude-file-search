"""
다양한 파일 형식 검색 서버

이 MCP 서버는 지정된 디렉토리에서 다양한 파일 형식(.pptx, .pdf, .docx, .txt 등)을 검색하고 
내용을 추출하는 기능을 제공합니다. 사용자가 Claude Desktop에서 자연어로 요청을 입력하면, 
이 서버가 파일을 검색하고 결과를 반환합니다.
"""

import os
import sys  # 이 줄이 반드시 필요합니다
import re
import json
import math
import logging
import traceback
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator

from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, validator

# 파일 핸들러 모듈 임포트
from file_handlers import FileHandlerRegistry, FileHandler
from file_handlers.pptx_handler import PPTXHandler
from file_handlers.pdf_handler import PDFHandler
from file_handlers.docx_handler import DOCXHandler
from file_handlers.text_handler import TextHandler

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 서버 설정
# SEARCH_DIR = os.environ.get("FILE_SEARCH_DIR", str(Path.home() / "Documents"))
SEARCH_DIRS = os.environ.get("FILE_SEARCH_DIRS", os.environ.get("FILE_SEARCH_DIR", str(Path.home() / "Documents")))
SEARCH_DIRS = [Path(dir_path.strip()) for dir_path in SEARCH_DIRS.split(";") if dir_path.strip()]
if not SEARCH_DIRS:
    SEARCH_DIRS = [Path(str(Path.home() / "Documents"))]
LOG_DIR = os.environ.get("FILE_LOG_DIR", ".")
LOG_LEVEL = os.environ.get("FILE_LOG_LEVEL", "INFO")
DEFAULT_LIMIT = 20  # 한 번에 반환할 기본 파일 개수
MAX_LIMIT = 50      # 한 번에 반환할 최대 파일 개수
MAX_CONTENT_PER_FILE = 10  # 파일당 처리할 최대 섹션 수 (슬라이드, 페이지 등)

# 로그 설정
log_dir = Path(LOG_DIR)
log_dir.mkdir(parents=True, exist_ok=True)  # 로그 디렉토리 자동 생성

log_file = log_dir / f"file_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
latest_log = log_dir / "file_search_latest.log"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.FileHandler(latest_log),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("file_search")

# 파일 핸들러 레지스트리 설정
handler_registry = FileHandlerRegistry()
handler_registry.register_handler(PPTXHandler())
handler_registry.register_handler(PDFHandler())
handler_registry.register_handler(DOCXHandler())
handler_registry.register_handler(TextHandler())

# FastMCP 서버 생성
mcp = FastMCP(
    "파일 검색 도구",
    dependencies=["python-pptx", "pydantic", "PyPDF2", "python-docx"]
)

class SearchResult(BaseModel):
    """검색 결과 모델"""
    filename: str = Field(description="파일 이름")
    file_type: str = Field(description="파일 형식")
    path: str = Field(description="파일 경로")
    content_matches: List[Dict[str, Any]] = Field(description="컨텐츠 매칭 정보")
    match_count: int = Field(description="총 매칭 수")
    
class SearchQuery(BaseModel):
    """검색 쿼리 모델"""
    keywords: str = Field(description="검색 키워드")
    directory: Optional[str] = Field(default=None, description="검색할 디렉토리 (지정하지 않으면 기본 디렉토리 사용)")
    file_type: Optional[str] = Field(default=None, description="검색할 파일 형식 (지정하지 않으면 모든 지원 형식 검색)")
    
    @validator('directory')
    def validate_directory(cls, v):
        # "null" 문자열을 None으로 변환
        if v == "null":
            return None
        return v
        
    @validator('file_type')
    def validate_file_type(cls, v):
        # "null" 문자열을 None으로 변환
        if v == "null":
            return None
        return v

class DirectoryListingQuery(BaseModel):
    """디렉토리 목록 쿼리 모델"""
    path: Optional[str] = Field(default=None, description="검색할 디렉토리 경로")
    page: int = Field(default=1, description="페이지 번호", ge=1)
    limit: int = Field(default=DEFAULT_LIMIT, description="페이지당 결과 수", ge=1, le=MAX_LIMIT)
    file_type: Optional[str] = Field(default=None, description="필터링할 파일 형식")
    
    @validator('path')
    def validate_path(cls, v):
        # "null" 문자열을 None으로 변환
        if v == "null":
            return None
        return v
        
    @validator('file_type')
    def validate_file_type(cls, v):
        # "null" 문자열을 None으로 변환
        if v == "null":
            return None
        return v

def find_files(directory: Path, file_type: Optional[str] = None, recursive: bool = True) -> Generator[Path, None, None]:
    """
    지정된 디렉토리에서 지원되는 파일을 찾아 생성자로 반환합니다.
    
    Args:
        directory: 검색할 디렉토리
        file_type: 찾을 파일 형식 (지정하지 않으면 모든 지원 형식 검색)
        recursive: 하위 디렉토리도 검색할지 여부
        
    Yields:
        찾은 파일 경로
    """
    try:
        if recursive:
            # 메모리 효율적인 방식으로 파일 찾기
            for root, _, files in os.walk(directory):
                root_path = Path(root)
                for file in files:
                    file_path = root_path / file
                    if handler_registry.can_handle_file(file_path, file_type):
                        yield file_path
        else:
            for file in directory.iterdir():
                if file.is_file() and handler_registry.can_handle_file(file, file_type):
                    yield file
    except Exception as e:
        logger.error(f"디렉토리 검색 중 오류 발생: {e}")
        # 예외가 발생해도 생성자는 종료되므로 빈 리스트 반환 없음

def extract_text_from_file(file_path: Path, max_content_sections: int = MAX_CONTENT_PER_FILE) -> List[Dict[str, Any]]:
    """
    파일에서 텍스트를 추출합니다.
    
    Args:
        file_path: 파일 경로
        max_content_sections: 처리할 최대 섹션 수 (슬라이드, 페이지 등)
        
    Returns:
        섹션별 텍스트 정보 리스트
    """
    try:
        logger.info(f"Extracting text from {file_path}")
        
        start_time = time.time()
        handler = handler_registry.get_handler_for_file(file_path)
        
        if handler is None:
            logger.warning(f"No handler found for {file_path}")
            return [{"section_number": 0, "text": "지원되지 않는 파일 형식입니다."}]
        
        content_sections = handler.extract_text(file_path, max_content_sections)
        
        logger.debug(f"Extracted {len(content_sections)} sections from {file_path} in {time.time() - start_time:.2f} seconds")
        return content_sections
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        logger.error(traceback.format_exc())
        return [{"section_number": 0, "text": f"파일 처리 중 오류 발생: {str(e)}"}]

async def search_files(directory: Path, keywords: str, file_type: Optional[str] = None, ctx: Optional[Context] = None) -> List[SearchResult]:
    """
    디렉토리에서 파일을 검색하고 키워드와 일치하는 파일을 찾습니다.
    
    Args:
        directory: 검색할 디렉토리
        keywords: 검색 키워드
        file_type: 검색할 파일 형식 (None이면 모든 지원 형식)
        ctx: MCP 컨텍스트
        
    Returns:
        검색 결과 목록
    """
    logger.info(f"Searching for '{keywords}' in {directory}" + (f" (file type: {file_type})" if file_type else ""))
    if ctx:
        ctx.info(f"'{keywords}' 검색 시작... 디렉토리: {directory}" + (f", 파일 형식: {file_type}" if file_type else ""))
    
    results = []
    keyword_pattern = re.compile(r'\b' + re.escape(keywords) + r'\b', re.IGNORECASE)
    
    # 검색 가능한 총 파일 수 계산
    files = list(find_files(directory, file_type))
    total_files = len(files)
    
    if total_files == 0:
        if ctx:
            ctx.info(f"디렉토리에서 검색할 파일을 찾을 수 없습니다: {directory}")
        return []
    
    # 진행 상황 추적용 변수
    processed_files = 0
    semaphore = asyncio.Semaphore(10)  # 동시에 최대 10개 파일 처리
    
    async def process_file(file_path):
        nonlocal processed_files  # 이 선언이 함수 시작 부분에 있어야 합니다
        
        async with semaphore:
            try:
                # 진행 상황 로깅
                content_sections = extract_text_from_file(file_path)
                handler = handler_registry.get_handler_for_file(file_path)
                file_type_desc = handler.get_type_description() if handler else "Unknown"
                
                content_matches = []
                for section in content_sections:
                    # 키워드 매칭을 위한 섹션 텍스트 준비
                    section_text = section.get("text", "")
                    if not section_text:
                        continue
                        
                    matches = re.findall(keyword_pattern, section_text)
                    if matches:
                        preview = section_text[:200] + "..." if len(section_text) > 200 else section_text
                        content_matches.append({
                            "section_number": section.get("section_number", 0),
                            "match_count": len(matches),
                            "preview": preview
                        })
                
                if content_matches:
                    match_count = sum(match["match_count"] for match in content_matches)
                    result = SearchResult(
                        filename=file_path.name,
                        file_type=file_type_desc,
                        path=str(file_path),
                        content_matches=content_matches,
                        match_count=match_count
                    )
                    results.append(result)
                    
                    # 로그 및 사용자에게 진행 상황 알림
                    if ctx:
                        ctx.info(f"매칭된 파일 발견: {file_path.name} (매칭 수: {match_count})")
                
                # 진행 상황 업데이트
                processed_files += 1
                progress_pct = round((processed_files / total_files) * 100)
                
                if ctx:
                    await ctx.report_progress(processed_files, total_files)
                    if processed_files % 5 == 0 or processed_files == total_files:
                        ctx.info(f"진행 중: {processed_files}/{total_files} 파일 처리 ({progress_pct}%)")
                
                # 검색 결과가 일정 수 이상 발견되면 중간 결과 보고
                if len(results) % 10 == 0 and len(results) > 0 and ctx:
                    # 임시 결과를 매칭 수로 정렬
                    sorted_results = sorted(results, key=lambda x: x.match_count, reverse=True)
                    top_results = sorted_results[:3]  # 상위 3개 결과만
                    
                    if top_results:
                        result_summary = "\n".join([
                            f"- {r.filename} ({r.match_count}개 매칭)" for r in top_results
                        ])
                        ctx.info(f"현재까지 발견된 상위 결과:\n{result_summary}")
            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                logger.error(traceback.format_exc())
                if ctx:
                    ctx.warning(f"파일 처리 중 오류 발생: {file_path} - {str(e)}")
                
                # 진행 상황 업데이트
                processed_files += 1
    
    # 병렬 처리를 위한 태스크 생성 및 실행
    tasks = []
    for file_path in files:
        tasks.append(asyncio.create_task(process_file(file_path)))
    
    # 모든 태스크 완료 대기
    await asyncio.gather(*tasks)
    
    # 매칭 수를 기준으로 결과 정렬
    results.sort(key=lambda x: x.match_count, reverse=True)
    
    logger.info(f"Found {len(results)} matching files out of {total_files} total files")
    if ctx:
        ctx.info(f"검색 완료: 총 {total_files}개 파일 중 {len(results)}개 파일에서 매칭됨")
    
    return results

@mcp.tool()
async def search_files_tool(query: SearchQuery, ctx: Context) -> str:
    """
    다양한 파일 형식에서 키워드를 검색합니다.
    
    Args:
        query: 검색 쿼리 (키워드와 선택적 디렉토리, 파일 형식)
        ctx: MCP 컨텍스트
        
    Returns:
        검색 결과를 JSON 형식으로 반환
    """
    start_time = time.time()
    ctx.info(f"검색 시작: '{query.keywords}'")
    logger.info(f"Search request: keywords='{query.keywords}', directory={query.directory}, file_type={query.file_type}")
    
    try:
        # 디렉토리 경로 검증
        if query.directory:
            search_dirs = [Path(query.directory)]
        else:
            search_dirs = SEARCH_DIRS
            
        # 존재하는 디렉토리만 필터링
        valid_dirs = []
        for dir_path in search_dirs:
            if not dir_path.exists() or not dir_path.is_dir():
                ctx.warning(f"검색 디렉토리가 존재하지 않습니다: {dir_path}")
                logger.warning(f"Directory not found: {dir_path}")
            else:
                valid_dirs.append(dir_path)
                
        if not valid_dirs:
            error_msg = "유효한 검색 디렉토리가 없습니다."
            ctx.error(error_msg)
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)
        
        # 검색하기 전에 검색 범위 정보 제공
        ctx.info(f"총 {len(valid_dirs)}개 디렉토리에서 검색합니다.")
        if len(valid_dirs) > 1:
            dir_list = "\n".join([f"- {d}" for d in valid_dirs])
            ctx.info(f"검색할 디렉토리:\n{dir_list}")
        
        # 모든 유효한 디렉토리에서 검색
        all_results = []
        for i, dir_path in enumerate(valid_dirs):
            ctx.info(f"[{i+1}/{len(valid_dirs)}] 디렉토리 검색 중: {dir_path}")
            dir_results = await search_files(dir_path, query.keywords, query.file_type, ctx)
            all_results.extend(dir_results)
            
            # 디렉토리별 중간 결과 보고
            if dir_results:
                ctx.info(f"'{dir_path}' 디렉토리에서 {len(dir_results)}개 파일 발견")
            else:
                ctx.info(f"'{dir_path}' 디렉토리에서 매칭 결과 없음")
            
        # 매칭 수를 기준으로 전체 결과 재정렬
        all_results.sort(key=lambda x: x.match_count, reverse=True)
        
        # 사용자에게 검색 진행 상황 보고
        elapsed_time = time.time() - start_time
        
        if all_results:
            # 상위 10개 파일만 상세 결과로 표시
            top_results = all_results[:10]
            result_summary = "\n".join([
                f"- {r.filename} (매칭 수: {r.match_count})" for r in top_results
            ])
            
            ctx.info(f"검색 완료! 총 {len(all_results)}개 파일을 찾았습니다. 소요 시간: {elapsed_time:.2f}초")
            if len(all_results) > 10:
                ctx.info(f"상위 10개 검색 결과:\n{result_summary}\n... 그 외 {len(all_results) - 10}개 파일")
            else:
                ctx.info(f"검색 결과:\n{result_summary}")
        else:
            ctx.info(f"'{query.keywords}'에 대한 검색 결과가 없습니다. 소요 시간: {elapsed_time:.2f}초")
        
        logger.info(f"Search completed in {elapsed_time:.2f} seconds")
        
        return json.dumps({
            "query": query.keywords,
            "directories": [str(dir_path) for dir_path in valid_dirs],
            "file_type": query.file_type,
            "result_count": len(all_results),
            "elapsed_time_seconds": round(elapsed_time, 2),
            "results": [result.model_dump() for result in all_results]
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"검색 중 오류 발생: {str(e)}"
        logger.exception(error_msg)
        ctx.error(error_msg)
        return json.dumps({
            "error": error_msg,
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)

@mcp.tool()
async def get_directory_listing(query: DirectoryListingQuery, ctx: Context = None) -> str:
    """
    디렉토리 내의 지원되는 파일 목록을 반환합니다.
    
    Args:
        query: 디렉토리 목록 쿼리 (경로, 페이지, 제한, 파일 형식)
        ctx: MCP 컨텍스트
        
    Returns:
        디렉토리 내 파일 목록을 JSON 형식으로 반환
    """
    start_time = time.time()
    logger.info(f"Directory listing request: path={query.path}, page={query.page}, limit={query.limit}, file_type={query.file_type}")
    
    if ctx:
        ctx.info(f"디렉토리 목록 조회 시작: {query.path or '모든 설정 디렉토리'}")
    
    try:
        if query.path:
            directories = [Path(query.path)]
        else:
            directories = SEARCH_DIRS
        
        # 존재하는 디렉토리만 필터링
        valid_dirs = []
        for dir_path in directories:
            if not dir_path.exists() or not dir_path.is_dir():
                if ctx:
                    ctx.warning(f"디렉토리가 존재하지 않습니다: {dir_path}")
                logger.warning(f"Directory not found: {dir_path}")
            else:
                valid_dirs.append(dir_path)
        
        if not valid_dirs:
            error_msg = "유효한 디렉토리가 없습니다."
            if ctx:
                ctx.error(error_msg)
            logger.error(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)
        
        # 여기서는 첫 번째 디렉토리만 처리
        directory = valid_dirs[0]
        if len(valid_dirs) > 1 and ctx:
            ctx.info(f"총 {len(valid_dirs)}개의 디렉토리 중 첫 번째 디렉토리({directory})의 목록만 표시합니다.")
        
        # 모든 파일을 한 번에 로드하지 않고 생성자를 사용하여 리스트 변환
        files = list(find_files(directory, query.file_type, recursive=False))
        total_files = len(files)
        
        # 페이징 처리
        start_idx = (query.page - 1) * query.limit
        end_idx = min(start_idx + query.limit, total_files)
        
        # 인덱스 범위 검증
        if start_idx >= total_files and total_files > 0:
            page = math.ceil(total_files / query.limit)
            start_idx = (page - 1) * query.limit
            end_idx = total_files
            
        # 페이지에 해당하는 파일만 처리
        current_page_files = files[start_idx:end_idx]
        
        # 각 파일에 대한 메타데이터 수집
        files_metadata = []
        for idx, f in enumerate(current_page_files):
            try:
                handler = handler_registry.get_handler_for_file(f)
                file_type = handler.get_type_description() if handler else "Unknown"
                
                stat = f.stat()
                files_metadata.append({
                    "name": f.name,
                    "path": str(f),
                    "type": file_type,
                    "size_kb": round(stat.st_size / 1024, 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                
                # 비동기 처리를 위해 이벤트 루프에 여유 제공
                if idx % 10 == 0:
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Error getting metadata for {f}: {e}")
                files_metadata.append({
                    "name": f.name,
                    "path": str(f),
                    "error": str(e)
                })
        
        elapsed_time = time.time() - start_time
        result = {
            "directory": str(directory),
            "all_directories": [str(d) for d in valid_dirs],
            "total_files": total_files,
            "page": query.page,
            "limit": query.limit,
            "total_pages": math.ceil(total_files / query.limit) if total_files > 0 else 1,
            "showing_files": len(files_metadata),
            "file_type_filter": query.file_type,
            "elapsed_time_seconds": round(elapsed_time, 2),
            "files": files_metadata
        }
        
        logger.info(f"Directory listing completed in {elapsed_time:.2f} seconds, showing {len(files_metadata)} of {total_files} files")
        if ctx:
            ctx.info(f"디렉토리 목록 조회 완료: 총 {total_files}개 파일 중 {len(files_metadata)}개 표시")
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"디렉토리 목록 조회 중 오류 발생: {str(e)}"
        logger.exception(error_msg)
        if ctx:
            ctx.error(error_msg)
        return json.dumps({
            "error": error_msg,
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)

@mcp.tool()
async def get_supported_file_types(ctx: Context = None) -> str:
    """
    지원되는 파일 형식 목록을 반환합니다.
    
    Args:
        ctx: MCP 컨텍스트
        
    Returns:
        지원되는 파일 형식 목록을 JSON 형식으로 반환
    """
    try:
        file_types = []
        for handler in handler_registry.handlers:
            file_types.append({
                "name": handler.get_type_description(),
                "extensions": handler.get_supported_extensions(),
                "is_enabled": True
            })
            
        result = {
            "supported_file_types": file_types
        }
        
        if ctx:
            ctx.info(f"지원되는 파일 형식 목록 반환: {len(file_types)}개 형식")
            
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        error_msg = f"지원되는 파일 형식 목록 조회 중 오류 발생: {str(e)}"
        logger.exception(error_msg)
        if ctx:
            ctx.error(error_msg)
        return json.dumps({
            "error": error_msg,
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)

@mcp.resource("search-help://guide")
def get_search_guide() -> str:
    """검색 가이드를 제공하는 리소스"""
    return """
# 다양한 파일 형식 검색 가이드

이 도구를 사용하여 다양한 파일 형식(.pptx, .pdf, .docx, .txt 등)을 검색할 수 있습니다.

## 사용 방법
1. "키오스크 비용 관련 문서 찾아줘"와 같이 자연어로 요청하세요.
2. 시스템이 자동으로 키워드를 추출하여 여러 파일 형식에서 검색합니다.
3. 검색 결과는 관련성 순으로 정렬되어 표시됩니다.

## 검색 팁
- 구체적인 키워드를 사용하면 더 정확한 결과를 얻을 수 있습니다.
- 특정 디렉토리를 지정하려면 "마케팅 폴더에서 예산 관련 문서 찾아줘"와 같이 요청하세요.
- 특정 파일 형식을 검색하려면 "PDF에서 계약 관련 내용 찾아줘"와 같이 요청하세요.
- 큰 디렉토리 탐색 시 시간이 오래 걸릴 수 있으니 가능한 구체적인 경로를 지정하세요.

## 지원되는 파일 형식
- PowerPoint (.pptx)
- Word (.docx)
- PDF (.pdf)
- 텍스트 파일 (.txt, .md, .py 등)

## 페이징 기능
디렉토리 목록을 볼 때 결과가 많은 경우, 페이지 번호와 페이지당 결과 수를 지정할 수 있습니다:
- 기본값: 페이지=1, 결과 수=20
- 최대 결과 수: 50
"""

def log_system_info():
    """시스템 정보를 로그에 기록"""
    logger.info("=== 시스템 정보 ===")
    logger.info(f"Python 버전: {sys.version}")
    logger.info(f"OS: {sys.platform}")
    logger.info(f"파일 검색 디렉토리: {SEARCH_DIRS}")
    logger.info(f"로그 디렉토리: {LOG_DIR}")
    logger.info(f"로그 레벨: {LOG_LEVEL}")
    logger.info(f"지원되는 파일 타입: {[h.get_type_description() for h in handler_registry.handlers]}")
    logger.info(f"지원되는 파일 확장자: {[ext for h in handler_registry.handlers for ext in h.get_supported_extensions()]}")
    logger.info("==================")

# 서버 시작 시 실행 코드 수정 (if __name__ == "__main__" 블록)
if __name__ == "__main__":
    log_system_info()
    logger.info(f"Starting File Search Server (PID: {os.getpid()})")
    logger.info(f"Search directories: {[str(d) for d in SEARCH_DIRS]}")
    logger.info(f"Log file: {log_file}")
    
    try:
        mcp.run()
    except Exception as e:
        logger.critical(f"Server crashed: {str(e)}")
        logger.critical(traceback.format_exc())