#!/usr/bin/env python3
"""
Diagnostic script that replicates the exact demo.py execution flow
to identify where the hanging occurs.
"""

import time
import signal
import traceback
from pathlib import Path

from src.core.decision_tree_generator import DecisionTreeGenerator
from src.demo.orchestrator import DemoOrchestrator
from src.agents.criteria_parser_agent import CriteriaParserAgent
from src.agents.tree_structure_agent import TreeStructureAgent
from src.agents.validation_agent import ValidationAgent
from src.agents.refinement_agent import RefinementAgent


class TimeoutHandler:
    """Context manager for handling timeouts in tests."""
    
    def __init__(self, timeout_seconds):
        self.timeout_seconds = timeout_seconds
        self.timed_out = False
    
    def timeout_handler(self, signum, frame):
        self.timed_out = True
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")
    
    def __enter__(self):
        self.old_handler = signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.timeout_seconds)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)  # Cancel alarm
        signal.signal(signal.SIGALRM, self.old_handler)  # Restore handler


def test_individual_agents():
    """Test each agent individually with Jardiance content."""
    print("=== Testing Individual Agents ===")
    
    # Load Jardiance content
    jardiance_path = Path("examples/jardiance_criteria.txt")
    if not jardiance_path.exists():
        print("❌ Jardiance criteria file not found")
        return False
    
    with open(jardiance_path, 'r') as f:
        content = f.read()
    
    print(f"Content length: {len(content)} characters")
    
    # Test 1: Criteria Parser Agent
    print("\n1. Testing CriteriaParserAgent...")
    try:
        with TimeoutHandler(30) as timeout:
            start_time = time.time()
            parser = CriteriaParserAgent()
            parsed_result = parser.parse(content)
            elapsed = time.time() - start_time
            
            if timeout.timed_out:
                print(f"❌ CriteriaParserAgent timed out after 30s")
                return False
            else:
                print(f"✅ CriteriaParserAgent completed in {elapsed:.2f}s")
                print(f"   Result keys: {list(parsed_result.keys())}")
    except Exception as e:
        print(f"❌ CriteriaParserAgent failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Tree Structure Agent
    print("\n2. Testing TreeStructureAgent...")
    try:
        with TimeoutHandler(30) as timeout:
            start_time = time.time()
            structure_agent = TreeStructureAgent()
            tree_result = structure_agent.create_tree(parsed_result)
            elapsed = time.time() - start_time
            
            if timeout.timed_out:
                print(f"❌ TreeStructureAgent timed out after 30s")
                return False
            else:
                print(f"✅ TreeStructureAgent completed in {elapsed:.2f}s")
                print(f"   Result keys: {list(tree_result.keys())}")
    except Exception as e:
        print(f"❌ TreeStructureAgent failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Validation Agent
    print("\n3. Testing ValidationAgent...")
    try:
        with TimeoutHandler(30) as timeout:
            start_time = time.time()
            validation_agent = ValidationAgent()
            validation_result = validation_agent.validate(tree_result)
            elapsed = time.time() - start_time
            
            if timeout.timed_out:
                print(f"❌ ValidationAgent timed out after 30s")
                return False
            else:
                print(f"✅ ValidationAgent completed in {elapsed:.2f}s")
                print(f"   Issues found: {len(validation_result.issues) if hasattr(validation_result, 'issues') else 'Unknown'}")
    except Exception as e:
        print(f"❌ ValidationAgent failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Refinement Agent
    print("\n4. Testing RefinementAgent...")
    try:
        with TimeoutHandler(30) as timeout:
            start_time = time.time()
            refinement_agent = RefinementAgent()
            final_result = refinement_agent.refine(tree_result, validation_result)
            elapsed = time.time() - start_time
            
            if timeout.timed_out:
                print(f"❌ RefinementAgent timed out after 30s")
                return False
            else:
                print(f"✅ RefinementAgent completed in {elapsed:.2f}s")
    except Exception as e:
        print(f"❌ RefinementAgent failed: {e}")
        traceback.print_exc()
        return False
    
    print("\n✅ All individual agents completed successfully!")
    return True


def test_decision_tree_generator():
    """Test the full DecisionTreeGenerator pipeline."""
    print("\n=== Testing DecisionTreeGenerator Pipeline ===")
    
    jardiance_path = Path("examples/jardiance_criteria.txt")
    with open(jardiance_path, 'r') as f:
        content = f.read()
    
    try:
        with TimeoutHandler(60) as timeout:
            start_time = time.time()
            generator = DecisionTreeGenerator()
            
            print("Starting full pipeline...")
            result = generator.generate_decision_tree(content)
            elapsed = time.time() - start_time
            
            if timeout.timed_out:
                print(f"❌ DecisionTreeGenerator timed out after 60s")
                return False
            else:
                print(f"✅ DecisionTreeGenerator completed in {elapsed:.2f}s")
                print(f"   Result type: {type(result)}")
                if isinstance(result, dict):
                    print(f"   Result keys: {list(result.keys())}")
                return True
                
    except Exception as e:
        print(f"❌ DecisionTreeGenerator failed: {e}")
        traceback.print_exc()
        return False


def test_orchestrator():
    """Test the DemoOrchestrator process_document method."""
    print("\n=== Testing DemoOrchestrator ===")
    
    jardiance_path = Path("examples/jardiance_criteria.txt")
    
    try:
        with TimeoutHandler(90) as timeout:
            start_time = time.time()
            orchestrator = DemoOrchestrator(output_dir="debug_outputs")
            
            print("Starting orchestrator.process_document...")
            result = orchestrator.process_document(str(jardiance_path))
            elapsed = time.time() - start_time
            
            if timeout.timed_out:
                print(f"❌ DemoOrchestrator timed out after 90s")
                return False
            else:
                print(f"✅ DemoOrchestrator completed in {elapsed:.2f}s")
                print(f"   Success: {result.success}")
                print(f"   Processing time: {result.processing_time:.2f}s")
                if not result.success:
                    print(f"   Error: {result.error}")
                return result.success
                
    except Exception as e:
        print(f"❌ DemoOrchestrator failed: {e}")
        traceback.print_exc()
        return False


def test_step_by_step_with_timing():
    """Test each step with detailed timing to identify bottlenecks."""
    print("\n=== Step-by-Step Timing Analysis ===")
    
    jardiance_path = Path("examples/jardiance_criteria.txt")
    with open(jardiance_path, 'r') as f:
        content = f.read()
    
    print(f"Document size: {len(content)} characters")
    
    # Initialize all components
    parser = CriteriaParserAgent()
    structure_agent = TreeStructureAgent()
    validation_agent = ValidationAgent()
    refinement_agent = RefinementAgent()
    
    timings = {}
    
    # Step 1: Parse criteria
    print("\nStep 1: Parsing criteria...")
    try:
        with TimeoutHandler(45) as timeout:
            start = time.time()
            parsed_criteria = parser.parse(content)
            timings['parse'] = time.time() - start
            
            if timeout.timed_out:
                print("❌ Parsing timed out")
                return False
            print(f"✅ Parsing completed in {timings['parse']:.2f}s")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        return False
    
    # Step 2: Create tree structure
    print("\nStep 2: Creating tree structure...")
    try:
        with TimeoutHandler(45) as timeout:
            start = time.time()
            initial_tree = structure_agent.create_tree(parsed_criteria)
            timings['structure'] = time.time() - start
            
            if timeout.timed_out:
                print("❌ Tree structure timed out")
                return False
            print(f"✅ Tree structure completed in {timings['structure']:.2f}s")
    except Exception as e:
        print(f"❌ Tree structure failed: {e}")
        return False
    
    # Step 3: Validate tree
    print("\nStep 3: Validating tree...")
    try:
        with TimeoutHandler(30) as timeout:
            start = time.time()
            validation_results = validation_agent.validate(initial_tree)
            timings['validation'] = time.time() - start
            
            if timeout.timed_out:
                print("❌ Validation timed out")
                return False
            print(f"✅ Validation completed in {timings['validation']:.2f}s")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False
    
    # Step 4: Refine tree
    print("\nStep 4: Refining tree...")
    try:
        with TimeoutHandler(30) as timeout:
            start = time.time()
            final_tree = refinement_agent.refine(initial_tree, validation_results)
            timings['refinement'] = time.time() - start
            
            if timeout.timed_out:
                print("❌ Refinement timed out")
                return False
            print(f"✅ Refinement completed in {timings['refinement']:.2f}s")
    except Exception as e:
        print(f"❌ Refinement failed: {e}")
        return False
    
    # Summary
    total_time = sum(timings.values())
    print(f"\n📊 Timing Summary:")
    print(f"   Parse:      {timings['parse']:.2f}s ({timings['parse']/total_time*100:.1f}%)")
    print(f"   Structure:  {timings['structure']:.2f}s ({timings['structure']/total_time*100:.1f}%)")
    print(f"   Validation: {timings['validation']:.2f}s ({timings['validation']/total_time*100:.1f}%)")
    print(f"   Refinement: {timings['refinement']:.2f}s ({timings['refinement']/total_time*100:.1f}%)")
    print(f"   TOTAL:      {total_time:.2f}s")
    
    return True


def main():
    """Run all diagnostic tests."""
    print("🔍 Demo Flow Diagnostic Tests")
    print("=" * 50)
    
    tests = [
        ("Individual Agents", test_individual_agents),
        ("Step-by-Step Timing", test_step_by_step_with_timing),
        ("DecisionTreeGenerator", test_decision_tree_generator),
        ("DemoOrchestrator", test_orchestrator),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            start_time = time.time()
            result = test_func()
            elapsed = time.time() - start_time
            results[test_name] = result
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{status} {test_name} ({elapsed:.2f}s total)")
            
        except KeyboardInterrupt:
            print(f"\n🛑 {test_name} interrupted by user")
            results[test_name] = False
            break
        except Exception as e:
            print(f"\n💥 {test_name} crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 Demo Flow Test Results")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed_count = sum(1 for result in results.values() if result is True)
    total_count = len(results)
    print(f"\nOverall: {passed_count}/{total_count} tests passed")


if __name__ == "__main__":
    main()