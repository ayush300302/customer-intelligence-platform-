import pytest
import os
from src.rag.retrieve import ComplaintRetriever

def test_retriever_initialization():
    retriever = ComplaintRetriever()
    # Should initialize even if files are missing (prints warning)
    assert retriever is not None

def test_retriever_empty_handling():
    retriever = ComplaintRetriever()
    if retriever.index is None:
        # If files are not generated yet, retrieve should return empty list
        results = retriever.retrieve("billing error")
        assert results == []
