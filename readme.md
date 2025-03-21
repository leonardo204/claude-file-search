# 다양한 파일 형식 검색 시스템 (File Search System)

Claude Desktop과 연동하여 자연어로 다양한 파일 형식(PPTX, PDF, DOCX, TXT 등)을 검색할 수 있는 시스템입니다. 이 시스템은 FastMCP를 활용하여 구현되었으며, 사용자가 Claude Desktop에서 자연어로 요청하면 지정된 디렉토리에서 파일 내용을 검색하고 결과를 자연어 응답으로 반환합니다.

## 주요 기능

- 다양한 파일 형식 지원 (PPTX, PDF, DOCX, TXT 등)
- 여러 디렉토리 동시 검색 기능
- 파일 형식별 필터링 기능
- 검색 결과의 관련성 점수 제공
- 진행 상황 실시간 보고
- 자세한 로그 기록

## 시스템 요구사항

- Python 3.8 이상
- Claude Desktop 설치
- FastMCP 라이브러리

## 필요 패키지 설치

### 1. 가상 환경 설정 (권장)

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 가상 환경 활성화 (macOS/Linux)
source venv/bin/activate
```

### 2. 필요 패키지 설치

```bash
# 설정 스크립트로 한 번에 설치
./setup_dev_env.sh

# 또는 수동으로 패키지 설치
pip install -e .
pip install fastmcp python-pptx PyPDF2 python-docx python-dotenv
```

## 설치 및 설정

### 1. MCP 서버 설치

```bash
# 설치 스크립트 실행
python install_mcp_server.py

# 또는 FastMCP CLI 직접 사용
fastmcp install file_search_server.py --name "파일 검색 도구"
```

### 2. 환경 변수 설정 (선택적)

`.env` 파일을 생성하고 다음 환경 변수를 설정할 수 있습니다:

```
FILE_SEARCH_DIRS=/path/to/search/dir1;/path/to/search/dir2
FILE_LOG_DIR=./logs
FILE_LOG_LEVEL=INFO
```

## 사용 방법

1. Claude Desktop을 실행합니다.
2. 다음과 같은 자연어 형식으로 검색 요청을 입력합니다:
   - "키오스크 비용 관련 문서 찾아줘"
   - "프로젝트 폴더에서 API 문서 검색해줘"
   - "PDF에서 계약 관련 내용 찾아줘"

3. Claude가 검색 요청을 처리하고 관련 파일을 찾아 요약 결과를 보여줍니다.

## Claude 프롬프트 템플릿 활용하기

프로젝트에 포함된 `claude-prompt.md` 파일에는 Claude가 파일 검색 도구를 효과적으로 활용할 수 있는 프롬프트 템플릿이 포함되어 있습니다. 이 템플릿을 사용하면 더 효과적인 검색 경험을 제공할 수 있습니다.

### 프롬프트 템플릿 적용 방법

1. Claude Desktop을 실행합니다.
2. 새 대화를 시작하고 다음과 같이 프롬프트 템플릿을 붙여넣습니다:

```
당신은 사용자가 다양한 형식의 파일을 검색할 수 있도록 도와주는 비서입니다. 사용자가 파일을 찾는 것과 관련된 자연어 요청을 할 때, 다음 단계를 따르세요:

1. 사용자의 요청에서 핵심 검색 키워드를 식별하세요.

2. 효율적인 검색을 위해 다음 정보를 단계적으로 파악하세요:
   a. 어떤 폴더에서 검색할지 물어보세요 (전체/특정 폴더/키워드가 포함된 폴더).
   b. 어떤 파일 형식을 검색할지 물어보세요 (문서/프레젠테이션/소스 코드/특정 확장자).

3. 수집한 정보를 바탕으로 '파일 검색 도구'의 search_files_tool 도구를 사용하여 파일을 검색하세요.

4. 검색 결과를 사용자가 이해하기 쉬운 형식으로 요약하세요.

5. 가장 관련성 높은 파일과 해당 섹션을 강조하세요.

가능한 경우, 항상 검색 도구를 사용하여 사용자의 질문에 답하세요. 도구가 사용 가능하지 않은 경우 해당 내용을 사용자에게 알려주세요.
```

3. 이후 파일 검색 요청을 입력하면, Claude는 보다 체계적으로 검색을 수행합니다:
   - 먼저 검색 키워드 파악
   - 검색할 폴더와 파일 형식 확인
   - 검색 도구 실행 및 결과 요약 제공

### 예시 대화 흐름

사용자: "키오스크 비용 관련 문서 좀 검색해줘"

Claude:
```
키오스크 비용 관련 문서를 검색해 드리겠습니다. 더 효율적인 검색을 위해 몇 가지 정보가 필요합니다.

먼저, 어떤 폴더에서 검색할까요?
1. 전체 디렉토리 검색
2. 특정 폴더 지정 (예: Documents, Projects 등)
3. '키오스크'가 포함된 폴더만 검색
```

사용자: "전체 디렉토리에서 검색해줘"

Claude:
```
네, 전체 디렉토리에서 검색하겠습니다. 어떤 유형의 파일을 검색할까요?
1. 모든 파일 형식
2. 문서 파일 (PDF, DOCX, TXT 등)
3. 프레젠테이션 (PPTX)
4. 소스 코드 파일 (Python, Java, JavaScript 등)
5. 특정 확장자만 (원하는 확장자를 알려주세요)
```

사용자: "문서와 프레젠테이션 파일을 검색해줘"

Claude:
```
네, 문서와 프레젠테이션 파일을 대상으로 '키오스크 비용'에 관한 검색을 시작하겠습니다. 잠시만 기다려주세요...

[검색 결과 요약 표시]
```

## 개발 모드로 실행

개발 및 디버깅을 위해 개발 모드로 실행할 수 있습니다:

```bash
# 개발 모드로 실행
python install_mcp_server.py dev

# 또는 FastMCP CLI 직접 사용
fastmcp dev file_search_server.py
```

## 로그 확인

로그 파일은 다음 위치에 저장됩니다:
- 최신 로그: `{LOG_DIR}/file_search_latest.log`
- 날짜별 로그: `{LOG_DIR}/file_search_{날짜}_{시간}.log`

## 파일 핸들러 추가하기

새로운 파일 형식을 지원하려면 다음 단계를 수행하세요:

1. `file_handlers` 디렉토리에 새 파일(예: `excel_handler.py`)을 생성합니다.
2. `FileHandler` 추상 클래스를 상속받는 핸들러 클래스를 구현합니다.
3. `get_supported_extensions()`, `get_type_description()`, `extract_text()` 메서드를 구현합니다.
4. `__init__.py` 파일에 새 핸들러를 등록합니다.
5. `file_search_server.py`에서 핸들러 레지스트리에 새 핸들러를 추가합니다.

예시:
```python
from file_handlers.base import FileHandler

class ExcelHandler(FileHandler):
    """Excel 파일 핸들러"""
    
    def get_supported_extensions(self) -> List[str]:
        return ['.xlsx', '.xls']
    
    def get_type_description(self) -> str:
        return 'Excel'
    
    def extract_text(self, file_path: Path, max_content_sections: int = 10) -> List[Dict[str, Any]]:
        # Excel 파일에서 텍스트 추출 구현
        ...
```

## 문제 해결

### 1. 파일을 찾을 수 없는 경우
- 검색 디렉토리 경로가 올바른지 확인하세요.
- 환경 변수 `FILE_SEARCH_DIRS`가 올바르게 설정되었는지 확인하세요.

### 2. MCP 서버 연결 오류
- Claude Desktop이 실행 중인지 확인하세요.
- MCP 서버가 제대로 설치되었는지 확인하세요 (`fastmcp list` 명령으로 확인).

### 3. 파일 내용을 추출할 수 없는 경우
- 필요한 라이브러리가 모두 설치되었는지 확인하세요.
- 로그 파일에서 상세한 오류 메시지를 확인하세요.

## 참고 자료

- [FastMCP 문서](https://github.com/jlowin/fastmcp)
- [Model Context Protocol(MCP) 설명](https://modelcontextprotocol.io/)
- [Claude Desktop 다운로드](https://claude.ai/download)
- [claude-prompt.md](./claude-prompt.md) - 파일 검색 시스템 활용을 위한 프롬프트 템플릿

## 프로젝트 구조

```
file_search_system/
├── file_handlers/         # 파일 핸들러 모듈
│   ├── __init__.py       # 핸들러 등록
│   ├── base.py           # 추상 클래스 정의
│   ├── pptx_handler.py   # PowerPoint 파일 핸들러
│   ├── pdf_handler.py    # PDF 파일 핸들러
│   ├── docx_handler.py   # Word 파일 핸들러
│   └── text_handler.py   # 텍스트 파일 핸들러
├── file_search_server.py  # 메인 서버 코드
├── install_mcp_server.py  # 설치 스크립트
├── setup_dev_env.sh       # 개발 환경 설정 스크립트
├── setup.py               # 파이썬 패키지 설정
├── claude-prompt.md       # Claude 프롬프트 템플릿
├── implementation-guide.md # 구현 가이드 문서
├── .env                   # 환경 변수 설정 (생성 필요)
└── logs/                  # 로그 디렉토리 (자동 생성)
```

## 라이선스

MIT License

## 기여

버그 신고나 기능 요청은 이슈 트래커를 이용해 주세요.
