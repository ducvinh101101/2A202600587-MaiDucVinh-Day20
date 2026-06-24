.PHONY: install test run-baseline run-multi benchmark benchmark-questions clean

install:
	pip install -e ".[dev,llm]"

test:
	pytest

run-baseline:
	python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"

run-multi:
	python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"

benchmark:
	python -m multi_agent_research_lab.cli benchmark --query "Research GraphRAG state-of-the-art and write a 500-word summary"

benchmark-questions:
	python -m multi_agent_research_lab.cli benchmark-questions --file Question.md

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build *.egg-info
