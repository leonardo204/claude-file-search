from setuptools import setup, find_packages

setup(
    name="file_search_system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastmcp",
        "python-pptx",
        "PyPDF2",
        "python-docx",
        "python-dotenv"
    ],
)