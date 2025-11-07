"""
Basic usage examples for O-SATE
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sandbox_manager import SandboxManager
from src.target_ai_wrapper import TargetAIWrapper
from src.logger import get_logger
from src.utils import load_env_variables, load_config

logger = get_logger(__name__)


def example_sandbox_usage():
    """Example: Using the sandbox manager"""
    print("\n" + "="*50)
    print("EXAMPLE 1: Sandbox Manager")
    print("="*50 + "\n")
    
    try:
        with SandboxManager() as manager:
            # Create a sandbox
            logger.info("Creating sandbox...")
            container = manager.create_sandbox("example-sandbox")
            
            # Execute a command
            logger.info("Executing command...")
            result = manager.execute_in_sandbox(
                container, 
                "python -c 'print(\"Hello from O-SATE sandbox!\")'"
            )
            
            print(f"Command output: {result['stdout']}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            print(f"Success: {result['success']}")
            
            # Get stats
            stats = manager.get_container_stats("example-sandbox")
            if stats:
                print(f"\nResource Usage:")
                print(f"  CPU: {stats.get('cpu_percent', 0):.2f}%")
                print(f"  Memory: {stats.get('memory_usage_mb', 0):.2f} MB")
    
    except Exception as e:
        logger.error(f"Sandbox example failed: {e}")


def example_ai_wrapper_usage():
    """Example: Using the AI wrapper (requires API key)"""
    print("\n" + "="*50)
    print("EXAMPLE 2: AI Wrapper")
    print("="*50 + "\n")
    
    # Load environment variables and configuration
    load_env_variables()
    cfg = load_config()
    
    try:
        # Initialize wrapper using configured default provider (supports OpenRouter)
        logger.info("Initializing AI wrapper...")
        default_provider = cfg.get('target_ai', {}).get('default_provider', 'openai')

        # Interactive model selection for OpenRouter
        if default_provider == 'openrouter':
            openrouter_models = cfg.get('target_ai', {}).get('openrouter_models', [])
            if not openrouter_models:
                target = cfg.get('target_ai', {}).get('fallback_model', 'openrouter-llama-3b')
            else:
                # Show interactive menu
                print("\nAvailable OpenRouter models:")
                for i, model in enumerate(openrouter_models, start=1):
                    print(f"  {i}. {model}")
                print(f"  0. Use default (first in list)")
                
                try:
                    choice = input("\nSelect model number [default 0]: ").strip()
                    if not choice or choice == '0':
                        target = openrouter_models[0]
                        print(f"Using default: {target}")
                    elif choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(openrouter_models):
                            target = openrouter_models[idx]
                            print(f"Selected: {target}")
                        else:
                            print(f"Invalid choice, using default: {openrouter_models[0]}")
                            target = openrouter_models[0]
                    else:
                        print(f"Invalid input, using default: {openrouter_models[0]}")
                        target = openrouter_models[0]
                except (EOFError, KeyboardInterrupt):
                    print(f"\nNo selection made, using default: {openrouter_models[0]}")
                    target = openrouter_models[0]
        else:
            # Use configured provider string directly (e.g., 'openai-gpt3.5')
            target = default_provider

        wrapper = TargetAIWrapper(target)
        
        # Send a query
        logger.info("Sending query...")
        response = wrapper.query("What is AI safety in one sentence?")
        
        print(f"Response: {response}")
        
        # Get metrics
        metrics = wrapper.get_metrics()
        print(f"\nMetrics:")
        print(f"  Total requests: {metrics['total_requests']}")
        print(f"  Avg response time: {metrics['average_response_time']:.2f}s")
    
    except ValueError as e:
        print(f"Error: {e}")
        print("Note: Add your API key to .env file to use this example")
    except Exception as e:
        logger.error(f"AI wrapper example failed: {e}")


def main():
    """Run all examples"""
    print("\n" + "="*50)
    print("O-SATE USAGE EXAMPLES")
    print("="*50)
    
    # Example 1: Sandbox
    example_sandbox_usage()
    
    # Example 2: AI Wrapper (will fail without API key)
    example_ai_wrapper_usage()
    
    print("\n" + "="*50)
    print("Examples complete!")
    print("="*50 + "\n")


if __name__ == "__main__":
    main()
