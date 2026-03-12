import pathlib

from setuptools import find_packages, setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.txt").read_text(encoding="utf-8") if (HERE / "README.txt").exists() else ""

setup(
	name="codefox",
	version="0.4.0",
	description="CodeFox CLI - code auditing and code review tool",
	long_description=README,
	long_description_content_type="text/plain",
	author="CodeFox",
	packages=find_packages(),
	include_package_data=True,
	install_requires=[
		"qdrant-client>=1.7.0",
		"fastembed>=0.3.0",
		"gitpython==3.1.46",
		"google-genai==1.63.0",
		"numpy>=1.24.0",
		"python-dotenv==1.2.1",
		"pyyaml==6.0.3",
		"rich==14.3.2",
		"typer==0.23.1",
		"openai==2.21.0",
		"ollama==0.6.1",
        "bm25s==0.3.0",
	],
	entry_points={
		"console_scripts": [
			"codefox=codefox.main:cli",
		],
	},
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires=">=3.11",
)

