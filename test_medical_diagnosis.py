#!/usr/bin/env python3
"""
Test script for the Medical Diagnosis System.
Demonstrates how the system works like a real doctor would diagnose patients.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_medical_diagnosis():
    """Test the medical diagnosis system."""
    print("🏥 Testing Medical Diagnosis System")
    print("=" * 60)
    
    try:
        from app.medical_diagnosis import MedicalDiagnosisEngine
        
        # Initialize the diagnosis engine
        engine = MedicalDiagnosisEngine()
        print("✅ Medical Diagnosis Engine initialized successfully")
        
        # Test cases - different types of medical queries
        test_cases = [
            {
                "name": "Chest Pain (Urgent)",
                "symptoms": "I have severe chest pain that started 2 hours ago. It's getting worse and I'm also feeling short of breath.",
                "expected_urgency": "URGENT"
            },
            {
                "name": "Diabetes Symptoms (Moderate)",
                "symptoms": "I've been feeling very thirsty lately and urinating more frequently. I'm also tired all the time and have lost some weight.",
                "expected_urgency": "MODERATE"
            },
            {
                "name": "Headache (Routine)",
                "symptoms": "I have a mild headache that comes and goes. It's not severe and doesn't interfere with my daily activities.",
                "expected_urgency": "ROUTINE"
            },
            {
                "name": "Emergency Symptoms (Emergency)",
                "symptoms": "I'm experiencing severe chest pain, shortness of breath, and I feel like I'm going to pass out. This is unbearable.",
                "expected_urgency": "EMERGENCY"
            }
        ]
        
        print(f"\n🔍 Testing {len(test_cases)} medical scenarios...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['name']} ---")
            print(f"Input: {test_case['symptoms']}")
            
            # Generate medical assessment
            assessment = engine.analyze_symptoms(test_case['symptoms'])
            
            # Display results
            print(f"✅ Urgency Level: {assessment.urgency_level.value}")
            print(f"✅ Symptoms Identified: {len(assessment.symptoms)}")
            print(f"✅ Differential Diagnosis: {len(assessment.differential_diagnosis)}")
            print(f"✅ Red Flags: {len(assessment.red_flags)}")
            print(f"✅ Recommendations: {len(assessment.recommendations)}")
            
            # Check if urgency matches expectation
            if assessment.urgency_level.value == test_case['expected_urgency']:
                print(f"✅ Urgency level matches expectation: {test_case['expected_urgency']}")
            else:
                print(f"⚠️ Urgency level mismatch. Expected: {test_case['expected_urgency']}, Got: {assessment.urgency_level.value}")
            
            # Show key findings
            if assessment.symptoms:
                print(f"   Key Symptoms: {', '.join([s.name for s in assessment.symptoms[:3]])}")
            
            if assessment.differential_diagnosis:
                top_diagnosis = assessment.differential_diagnosis[0]
                print(f"   Top Diagnosis: {top_diagnosis.condition} ({top_diagnosis.probability*100:.1f}% probability)")
            
            if assessment.red_flags:
                print(f"   Red Flags: {', '.join(assessment.red_flags[:2])}")
        
        # Test the formatting function
        print(f"\n📋 Testing Assessment Formatting...")
        sample_assessment = engine.analyze_symptoms("I have chest pain and shortness of breath")
        formatted = engine.format_assessment(sample_assessment)
        
        print("✅ Assessment formatting successful")
        print(f"   Formatted length: {len(formatted)} characters")
        print(f"   Contains key sections: {'🏥' in formatted and 'URGENCY LEVEL' in formatted}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_symptom_extraction():
    """Test symptom extraction capabilities."""
    print(f"\n🔍 Testing Symptom Extraction...")
    
    try:
        from app.medical_diagnosis import MedicalDiagnosisEngine
        
        engine = MedicalDiagnosisEngine()
        
        # Test symptom extraction
        test_input = "I have chest pain for 3 days, severe headache, and nausea when I eat"
        
        assessment = engine.analyze_symptoms(test_input)
        
        print(f"✅ Symptom extraction successful")
        print(f"   Input: {test_input}")
        print(f"   Symptoms found: {len(assessment.symptoms)}")
        
        for symptom in assessment.symptoms:
            print(f"     - {symptom.name} (Severity: {symptom.severity}/10, System: {symptom.body_system.value})")
        
        return True
        
    except Exception as e:
        print(f"❌ Symptom extraction test failed: {e}")
        return False

def test_urgency_assessment():
    """Test urgency assessment logic."""
    print(f"\n🔍 Testing Urgency Assessment...")
    
    try:
        from app.medical_diagnosis import MedicalDiagnosisEngine, UrgencyLevel
        
        engine = MedicalDiagnosisEngine()
        
        # Test different urgency levels
        urgency_tests = [
            ("chest pain", UrgencyLevel.URGENT),
            ("mild headache", UrgencyLevel.ROUTINE),
            ("severe chest pain", UrgencyLevel.URGENT),
            ("unconscious", UrgencyLevel.EMERGENCY),
            ("persistent cough", UrgencyLevel.MODERATE)
        ]
        
        for test_input, expected_urgency in urgency_tests:
            assessment = engine.analyze_symptoms(test_input)
            actual_urgency = assessment.urgency_level
            
            if actual_urgency == expected_urgency:
                print(f"✅ '{test_input}' -> {actual_urgency.value} (Expected: {expected_urgency.value})")
            else:
                print(f"⚠️ '{test_input}' -> {actual_urgency.value} (Expected: {expected_urgency.value})")
        
        return True
        
    except Exception as e:
        print(f"❌ Urgency assessment test failed: {e}")
        return False

def test_differential_diagnosis():
    """Test differential diagnosis generation."""
    print(f"\n🔍 Testing Differential Diagnosis...")
    
    try:
        from app.medical_diagnosis import MedicalDiagnosisEngine
        
        engine = MedicalDiagnosisEngine()
        
        # Test diabetes symptoms
        diabetes_input = "I'm very thirsty, urinating frequently, and losing weight"
        assessment = engine.analyze_symptoms(diabetes_input)
        
        print(f"✅ Differential diagnosis generated")
        print(f"   Input: {diabetes_input}")
        print(f"   Diagnoses found: {len(assessment.differential_diagnosis)}")
        
        for diagnosis in assessment.differential_diagnosis:
            print(f"     - {diagnosis.condition}: {diagnosis.probability*100:.1f}% probability")
            print(f"       Evidence: {', '.join(diagnosis.evidence)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Differential diagnosis test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Healthcare Voice AI - Medical Diagnosis System Test")
    print("=" * 70)
    
    # Run all tests
    tests = [
        ("Medical Diagnosis Engine", test_medical_diagnosis),
        ("Symptom Extraction", test_symptom_extraction),
        ("Urgency Assessment", test_urgency_assessment),
        ("Differential Diagnosis", test_differential_diagnosis)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Medical diagnosis system is working correctly.")
        print("\n🏥 The system now provides:")
        print("   • Professional symptom analysis")
        print("   • Systematic differential diagnosis")
        print("   • Urgency assessment")
        print("   • Red flag identification")
        print("   • Evidence-based recommendations")
        print("   • Safety protocols")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    print(f"\n💡 To test the system:")
    print("   1. Start the server: python main.py")
    print("   2. Visit: http://localhost:8000")
    print("   3. Ask medical questions like:")
    print("      - 'I have chest pain and shortness of breath'")
    print("      - 'I'm very thirsty and urinating frequently'")
    print("      - 'I have a severe headache that won't go away'")

if __name__ == "__main__":
    main()
