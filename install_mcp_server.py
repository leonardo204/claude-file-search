"""
MCP 파일 검색 서버 설치 스크립트

이 스크립트는 FastMCP를 사용하여 파일 검색 서버를 Claude Desktop에 설치합니다.
"""
import subprocess
import sys
from pathlib import Path

# 스크립트 경로 확인
script_path = Path(__file__).parent.absolute() / "file_search_server.py"

def install_server():
    """MCP 서버를 Claude Desktop에 설치합니다."""
    try:
        # 가상환경 활성화 확인
        subprocess.run([
            "fastmcp", "install", 
            str(script_path), 
            "--name", "파일 검색 도구", 
            "--env-file", ".env", 
            "--with", "python-pptx", 
            "--with", "PyPDF2", 
            "--with", "python-docx",
            "--with", "python-dotenv"
        ], check=True)
        print("MCP 서버가 성공적으로 설치되었습니다!")
    except subprocess.CalledProcessError as e:
        print(f"MCP 서버 설치 실패: {e}")
        sys.exit(1)

def run_dev_server():
    """개발 모드로 MCP 서버를 실행합니다."""
    try:
        subprocess.run([
            "fastmcp", "dev", 
            str(script_path), 
            "--with", "python-pptx", 
            "--with", "PyPDF2", 
            "--with", "python-docx",
            "--with", "python-dotenv"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"개발 서버 실행 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 명령행 인수에 따라 설치 또는 개발 모드로 실행
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        run_dev_server()
    else:
        install_server()