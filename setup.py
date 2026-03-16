"""Setup script for GrammarBuddy."""

from setuptools import setup, find_packages

setup(
    name="grammarbuddy",
    version="1.0.0",
    description="Svensk grammatikträning med AI för SFI-nivå och lättläst svenska",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="GrammarBuddy Team",
    license="MIT",
    url="https://github.com/yeager/GrammarBuddy",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "PyGObject>=3.42.0",
    ],
    extras_require={
        "ai": ["openai>=1.0"],
    },
    entry_points={
        "console_scripts": [
            "grammarbuddy=grammarbuddy.app:main",
        ],
    },
    data_files=[
        ("share/applications", ["data/se.grammarbuddy.app.desktop"]),
        ("share/locale/sv/LC_MESSAGES", ["po/sv/LC_MESSAGES/grammarbuddy.po"]),
        ("share/locale/en/LC_MESSAGES", ["po/en/LC_MESSAGES/grammarbuddy.po"]),
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Swedish",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
    ],
)
