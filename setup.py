import pathlib

from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8") if (HERE / "README.md").exists() else ""

setup(
	name="codefox",
	version="0.4.6",
	description="CodeFox CLI - code auditing and code review tool",
	long_description=README,
	long_description_content_type="text/markdown",
	author="CodeFox",
	license="MIT",
	url="https://github.com/URLbug/CodeFox-CLI",
	project_urls={
		"Documentation": "https://github.com/codefox-lab/CodeFox-CLI/wiki",
		"Source": "https://github.com/URLbug/CodeFox-CLI",
		"Issues": "https://github.com/URLbug/CodeFox-CLI/issues",
		"Security": "https://github.com/URLbug/CodeFox-CLI/blob/main/SECURITY.md",
	},
	keywords=[
		"ai",
		"code review",
		"cli",
		"static analysis",
		"ollama",
		"openrouter",
		"gemini",
	],
	packages=find_packages(),
	include_package_data=True,
	install_requires=[
		"bm25s==0.3.0",
		"qdrant-client>=1.7.0",
		"fastembed>=0.3.0",
		"gitpython==3.1.46",
		"google-genai==1.63.0",
		"nltk==3.9.3",
		"numpy>=1.24.0",
		"ollama==0.6.1",
		"openai==2.21.0",
		"python-dotenv==1.2.1",
		"pyyaml==6.0.3",
		"requests>=2.28.0",
		"rich==14.3.2",
		"typer==0.23.1",
		"tree-sitter-language-pack==0.13.0",
		"psutil==7.2.2",
		"PyGithub==2.8.1",
		"pygments==2.19.2",
        "python-gitlab==8.1.0",
	],
	entry_points={
		"console_scripts": [
			"codefox=codefox.main:cli",
		],
	},
	classifiers=[
		"Development Status :: 4 - Beta",
		"Environment :: Console",
		"Intended Audience :: Developers",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.11",
		"Programming Language :: Python :: 3.12",
		"Programming Language :: Python :: 3.13",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
		"Topic :: Software Development",
		"Topic :: Software Development :: Quality Assurance",
		"Topic :: Utilities",
	],
	python_requires=">=3.11",
)
