# Apify Deployment Fix - Summary

## Problem
The repository was missing required Apify actor configuration files, preventing successful deployment to the Apify platform.

## Root Cause
According to [Apify Python Actor Documentation](https://docs.apify.com/academy/deploying-your-code/python-actors), Python actors require:
1. `.actor/actor.json` - Actor metadata and configuration
2. `.actor/INPUT_SCHEMA.json` - Input parameter schema
3. `src/__main__.py` - Entry point module
4. `Dockerfile` with correct CMD
5. `requirements.txt` with apify SDK

The repository was missing items 1, 2, and 3.

## Changes Made

### 1. Created `.actor/` Directory Structure
```
.actor/
├── actor.json          # Actor metadata
├── INPUT_SCHEMA.json   # Input parameter schema
├── INPUT_EXAMPLE.json  # Example usage
└── README.md          # Deployment guide
```

### 2. Created Actor Configuration (`.actor/actor.json`)
- Defined actor name: `o-sate-ai-safety-tester`
- Configured environment variables for API keys
- Set up dataset storage for results
- Referenced Dockerfile and input schema

### 3. Created Input Schema (`.actor/INPUT_SCHEMA.json`)
Defined 8 input parameters:
- `model` / `models`: AI model selection
- `maxPrompts`: Number of prompts (1-182)
- `categories`: Prompt category filters
- `concurrency`: Parallel requests
- `retryAttempts`: Retry configuration
- `timeoutSeconds`: Request timeout
- `apiKeys`: Provider API key overrides

### 4. Created Entry Point (`src/__main__.py`)
Simple entry point that imports and runs the main function:
```python
import asyncio
from src.main import main

if __name__ == '__main__':
    asyncio.run(main())
```

### 5. Updated `.gitignore`
Added exception to include `.actor/*.json` files (they were being ignored due to `*.json` rule)

### 6. Created `.dockerignore`
Optimized Docker builds by excluding:
- Git files
- Python cache
- Virtual environments
- IDE files
- Test files
- Documentation (except README.md)

### 7. Added Deployment Verification Script
Created `scripts/verify_apify_deployment.py` to check all requirements are met.

## Verification

✅ All required files present
✅ JSON files are valid
✅ Entry point imports correctly
✅ Dockerfile has correct CMD
✅ All pytest tests pass (11 passed, 1 skipped)
✅ No critical linting errors
✅ 182 safety prompts loaded correctly

## Deployment Instructions

```bash
# 1. Install Apify CLI
npm install -g apify-cli

# 2. Login to Apify
apify login

# 3. Test locally (optional)
export OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
apify run --purge

# 4. Deploy to Apify platform
apify push
```

## Testing the Fix

### API Keys (user-provided)
- No provider keys are bundled. Users must supply their own via:
    - Apify Actor UI input `apiKeys.openrouter` / `apiKeys.openai` / `apiKeys.anthropic` / `apiKeys.gemini`, or
    - Environment variables `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` set in the Apify actor.
- Default model now reads from config/.env; if unset, provide a model in the actor input.

Run the verification script:
```bash
python scripts/verify_apify_deployment.py
```

Expected output: `🎉 SUCCESS! All Apify deployment requirements are met.`

## References
- [Apify Python Actors Documentation](https://docs.apify.com/academy/deploying-your-code/python-actors)
- [Apify Actor Configuration](https://docs.apify.com/platform/actors/development/actor-definition/actor-json)
- [Apify Input Schema](https://docs.apify.com/platform/actors/development/actor-definition/input-schema)
