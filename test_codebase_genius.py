"""
Test Script for Codebase Genius
Comprehensive testing suite for the documentation generation system
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

# Configuration
JAC_SERVER_URL = "http://localhost:8000"
TEST_REPO = "https://github.com/navdeep-G/samplemod"

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def test_server_connection():
    """Test if Jac server is running"""
    print_header("Test 1: Server Connection")
    
    try:
        response = requests.get(f"{JAC_SERVER_URL}/docs", timeout=5)
        if response.status_code == 200:
            print_success("Server is running and accessible")
            print_info(f"Server URL: {JAC_SERVER_URL}")
            return True
        else:
            print_warning(f"Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server")
        print_info("Make sure to run: jac serve main.jac")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_environment_setup():
    """Test environment configuration"""
    print_header("Test 2: Environment Configuration")
    
    # Check for .env file
    if os.path.exists('.env'):
        print_success(".env file found")
    else:
        print_warning(".env file not found")
        print_info("Create .env from .env.example")
    
    # Check for API keys
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('GEMINI_API_KEY')
    if api_key:
        print_success("API key configured")
        key_type = "OpenAI" if os.getenv('OPENAI_API_KEY') else "Gemini"
        print_info(f"Using {key_type} API")
    else:
        print_warning("No API key found in environment")
        print_info("Set OPENAI_API_KEY or GEMINI_API_KEY in .env")
    
    # Check output directory
    if os.path.exists('outputs'):
        print_success("Output directory exists")
    else:
        print_info("Output directory will be created automatically")
    
    return True

def test_documentation_generation(github_url):
    """Test documentation generation for a repository"""
    print_header("Test 3: Documentation Generation")
    
    print_info(f"Repository: {github_url}")
    print_info("This may take 1-5 minutes...")
    
    try:
        start_time = time.time()
        
        # Make API request
        response = requests.post(
            f"{JAC_SERVER_URL}/walker/DocumentRepository",
            json={
                "github_url": github_url,
                "output_dir": "./outputs"
            },
            timeout=300
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_info(f"Request completed in {duration:.1f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            
            print_success("API request successful")
            print(f"\n{Colors.BOLD}Results:{Colors.END}")
            print(json.dumps(result, indent=2))
            
            if result.get("status") == "completed":
                print_success("Documentation generated successfully")
                
                output_path = result.get("output_path")
                if output_path and os.path.exists(output_path):
                    print_success(f"Documentation file created: {output_path}")
                    
                    # Check file size
                    file_size = os.path.getsize(output_path)
                    print_info(f"File size: {file_size / 1024:.1f} KB")
                    
                    # Preview first few lines
                    print(f"\n{Colors.BOLD}Preview (first 10 lines):{Colors.END}")
                    with open(output_path, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if i >= 10:
                                break
                            print(f"  {line.rstrip()}")
                    
                    return True
                else:
                    print_error("Documentation file not found")
                    return False
            else:
                print_error(f"Generation failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print_error(f"Server returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        print_info("Try with a smaller repository")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_query_ccg():
    """Test Code Context Graph query functionality"""
    print_header("Test 4: Query Code Context Graph")
    
    try:
        response = requests.post(
            f"{JAC_SERVER_URL}/walker/QueryCCG",
            json={
                "query_type": "structure",
                "entity_name": ""
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success("CCG query successful")
            print(f"\n{Colors.BOLD}Structure:{Colors.END}")
            print(json.dumps(result, indent=2)[:500] + "...")
            return True
        else:
            print_warning(f"Query returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error querying CCG: {e}")
        return False

def test_output_validation(output_path="./outputs"):
    """Validate generated output"""
    print_header("Test 5: Output Validation")
    
    output_dir = Path(output_path)
    
    if not output_dir.exists():
        print_warning("Output directory doesn't exist yet")
        return False
    
    # Find documentation files
    doc_files = list(output_dir.rglob("*.md"))
    
    if not doc_files:
        print_warning("No documentation files found")
        return False
    
    print_success(f"Found {len(doc_files)} documentation file(s)")
    
    for doc_file in doc_files:
        print(f"\n{Colors.BOLD}Validating: {doc_file}{Colors.END}")
        
        # Check file size
        size = doc_file.stat().st_size
        if size > 0:
            print_success(f"File size: {size / 1024:.1f} KB")
        else:
            print_error("File is empty")
            continue
        
        # Check content
        with open(doc_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate sections
        required_sections = ["Overview", "Installation", "Architecture"]
        found_sections = []
        
        for section in required_sections:
            if section.lower() in content.lower():
                found_sections.append(section)
        
        print_info(f"Found sections: {', '.join(found_sections)}")
        
        # Check for diagrams
        if "```mermaid" in content:
            print_success("Contains Mermaid diagrams")
        else:
            print_info("No Mermaid diagrams found")
        
        # Check for API reference
        if "API Reference" in content or "api reference" in content:
            print_success("Contains API reference")
        else:
            print_info("No API reference section found")
    
    return True

def run_all_tests():
    """Run all tests"""
    print_header("🧠 Codebase Genius - Test Suite")
    
    print(f"{Colors.BOLD}Running comprehensive tests...{Colors.END}\n")
    
    results = {}
    
    # Test 1: Server Connection
    results['server'] = test_server_connection()
    
    if not results['server']:
        print_error("\n❌ Server connection failed. Please start the server first.")
        print_info("Run: jac serve main.jac")
        sys.exit(1)
    
    # Test 2: Environment
    results['environment'] = test_environment_setup()
    
    # Test 3: Documentation Generation
    repo_url = sys.argv[1] if len(sys.argv) > 1 else TEST_REPO
    results['generation'] = test_documentation_generation(repo_url)
    
    # Test 4: CCG Query (optional)
    # results['ccg'] = test_query_ccg()
    
    # Test 5: Output Validation
    results['validation'] = test_output_validation()
    
    # Summary
    print_header("Test Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    print(f"{Colors.BOLD}Total Tests: {total_tests}{Colors.END}")
    print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
    print(f"{Colors.RED}Failed: {total_tests - passed_tests}{Colors.END}")
    
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.END}")
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"  {test_name.capitalize()}: {status}")
    
    if passed_tests == total_tests:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ All tests passed!{Colors.END}")
        print_header("Next Steps")
        print("1. Check the generated documentation in ./outputs/")
        print("2. Run the Streamlit UI: streamlit run app.py")
        print("3. Try with your own repositories!")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ Some tests failed{Colors.END}")
        print("\nCheck the error messages above and:")
        print("1. Ensure the Jac server is running")
        print("2. Verify your API keys are set")
        print("3. Check the logs for detailed errors")
    
    return passed_tests == total_tests

def main():
    """Main test function"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()