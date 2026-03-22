import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_utils import analyze_text_advanced, classify_profile, normalize_va

def test_analyze_text_negativo():
    polarity, subjectivity, neg_count = analyze_text_advanced(
        "Me siento muy triste y agotado, estoy desesperado")
    assert polarity < 0, f"Esperaba polaridad negativa, obtuve {polarity}"
    assert neg_count >= 2, f"Esperaba >= 2 palabras negativas, obtuve {neg_count}"
    print(f"✅ test_analyze_text_negativo: polarity={polarity}, neg={neg_count}")

def test_analyze_text_positivo():
    polarity, subjectivity, neg_count = analyze_text_advanced(
        "Me siento feliz y motivado, todo está chévere")
    assert polarity > 0, f"Esperaba polaridad positiva, obtuve {polarity}"
    print(f"✅ test_analyze_text_positivo: polarity={polarity}")

def test_analyze_text_vacio():
    polarity, subjectivity, neg_count = analyze_text_advanced("")
    assert polarity == 0.0
    assert subjectivity == 0.0
    assert neg_count == 0
    print("✅ test_analyze_text_vacio: OK")

def test_normalize_va():
    valence, arousal = normalize_va(1, 1)
    assert valence == -1.0
    assert arousal == 0.0
    valence, arousal = normalize_va(9, 9)
    assert valence == 1.0
    assert arousal == 1.0
    print("✅ test_normalize_va: OK")

def test_classify_profile_resiliente():
    perfil = classify_profile(0.30, 0.5, 0.2, {"vigor":0.7,"fatigue":0.2,"tension":0.2,"depression":0.2}, 0)
    assert perfil == "Resiliente", f"Esperaba Resiliente, obtuve {perfil}"
    print(f"✅ test_classify_profile_resiliente: {perfil}")

def test_classify_profile_estres():
    perfil = classify_profile(0.70, -0.3, 0.4, {"vigor":0.3,"fatigue":0.4,"tension":0.6,"depression":0.3}, 3)
    assert perfil == "Estrés", f"Esperaba Estrés, obtuve {perfil}"
    print(f"✅ test_classify_profile_estres: {perfil}")

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Ejecutando tests del sistema NLP")
    print("=" * 50)
    test_analyze_text_negativo()
    test_analyze_text_positivo()
    test_analyze_text_vacio()
    test_normalize_va()
    test_classify_profile_resiliente()
    test_classify_profile_estres()
    print("=" * 50)
    print("✅ Todos los tests pasaron correctamente")
    print("=" * 50)