#!/usr/bin/env python3
"""
Healthcare Voice AI Assistant
A comprehensive voice-enabled AI assistant for healthcare information and support.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get version from config
def get_version():
    version_file = os.path.join("config", "settings.py")
    with open(version_file, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("VERSION"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="healthcare-voice-ai",
    version=get_version(),
    author="Healthcare Voice AI Team",
    author_email="team@healthcare-voice-ai.com",
    description="A comprehensive voice-enabled AI assistant for healthcare information and support",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/healthcare-voice-ai/healthcare-voice-ai",
    project_urls={
        "Bug Reports": "https://github.com/healthcare-voice-ai/healthcare-voice-ai/issues",
        "Source": "https://github.com/healthcare-voice-ai/healthcare-voice-ai",
        "Documentation": "https://healthcare-voice-ai.readthedocs.io/",
    },
    packages=find_packages(exclude=["tests*", "docs*", "scripts*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Healthcare",
        "Framework :: FastAPI",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-asyncio>=0.18.0",
            "pytest-mock>=3.6.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.950",
            "pre-commit>=2.15",
            "coverage>=6.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
            "myst-parser>=0.17.0",
            "sphinx-autodoc-typehints>=1.12",
        ],
        "deploy": [
            "gunicorn>=20.0",
            "uvicorn[standard]>=0.17.0",
            "supervisor>=4.0",
        ],
        "monitoring": [
            "prometheus-client>=0.12.0",
            "grafana-api>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "healthcare-voice-ai=main:main",
            "ingest-docs=scripts.ingest:main",
            "voice-ai-cli=scripts.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "*.txt",
            "*.md",
            "*.yml",
            "*.yaml",
            "*.json",
            "*.html",
            "*.css",
            "*.js",
            "*.png",
            "*.jpg",
            "*.ico",
        ],
    },
    data_files=[
        ("config", ["config/settings.py", "config/paths.py"]),
        ("prompts", [
            "config/prompts/audit_prompt.txt",
            "config/prompts/base_prompt.txt",
            "config/prompts/chat_prompt.txt",
            "config/prompts/safety_prompt.txt"
        ]),
        ("frontend/static", [
            "frontend/static/index.html",
            "frontend/static/styles.css",
            "frontend/static/script.js"
        ]),
        ("sample_documents", [
            "data/sample_documents/diabetes_management.md",
            "data/sample_documents/heart_health_guide.md"
        ]),
    ],
    zip_safe=False,
    keywords=[
        "healthcare",
        "voice",
        "ai",
        "assistant",
        "rag",
        "speech-to-text",
        "text-to-speech",
        "llm",
        "openai",
        "fastapi",
        "python",
    ],
    platforms=["any"],
    license="MIT",
    maintainer="Healthcare Voice AI Team",
    maintainer_email="team@healthcare-voice-ai.com",
    download_url="https://github.com/healthcare-voice-ai/healthcare-voice-ai/archive/refs/tags/v{}.tar.gz".format(get_version()),
    provides=["healthcare_voice_ai"],
    obsoletes=[],
    requires_python=">=3.8",
    setup_requires=[
        "setuptools>=45",
        "wheel",
        "setuptools_scm[toml]>=6.2",
    ],
    use_scm_version=False,
    cmdclass={},
    options={
        "bdist_wheel": {
            "universal": True,
        },
    },
)
