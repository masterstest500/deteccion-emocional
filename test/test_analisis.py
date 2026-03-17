# tests/test_analysis.py
import pytest
from app import preprocess_text, analyze_text_advanced

def test_preprocess_text_empty():
    assert preprocess_text("") == ""

def test_preprocess_text_basic():
    text = "Estoy muy cansado y triste"
    cleaned = preprocess_text(text)
    assert isinstance(cleaned, str)
    assert "triste" in cleaned or "cansad" in cleaned or cleaned != ""

def test_analyze_text_advanced_empty():
    polarity, subj, neg = analyze_text_advanced("")
    assert polarity == 0.0
    assert subj == 0.0
    assert neg == 0

def test_analyze_text_advanced_negative():
    text = "Me siento muy triste y ansioso"
    polarity, subj, neg = analyze_text_advanced(text)
    assert neg >= 1
    assert isinstance(polarity, float)
    assert isinstance(subj, float)
