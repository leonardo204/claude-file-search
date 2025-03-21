#!/bin/bash
# 개발 환경 설정 스크립트

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 필요한 패키지 설치
pip install -e .
pip install fastmcp python-pptx PyPDF2 python-docx python-dotenv

# 로그 디렉토리 생성
mkdir -p logs

echo "개발 환경이 설정되었습니다. 'source venv/bin/activate'를 실행하여 가상환경을 활성화하세요."