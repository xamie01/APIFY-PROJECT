# Apify Actor Configuration

This directory contains the Apify actor configuration files required for deployment to the Apify platform.

## Files

### actor.json
Actor metadata and configuration including:
- Actor name, title, and description
- Environment variables (API keys)
- Dockerfile and README references
- Dataset storage configuration

### INPUT_SCHEMA.json
JSON Schema defining the actor's input parameters:
- `model` or `models`: AI model(s) to test
- `maxPrompts`: Number of safety prompts to run (1-182)
- `categories`: Filter prompts by category
- `concurrency`: Parallel API requests
- `openrouterApiKey`, `openaiApiKey`, `anthropicApiKey`, `geminiApiKey`: Provider API keys (marked as secret)

### INPUT_EXAMPLE.json
Example input configuration demonstrating typical usage.

## Deployment

### Local Testing
```bash
# Install Apify CLI
npm install -g apify-cli

# Login to Apify
apify login

# Test locally (requires API keys in environment)
export OPENROUTER_API_KEY=sk-or-v1-your-key
apify run --purge

# Or test with input file
apify run --purge --input-file .actor/INPUT_EXAMPLE.json
```

### Deploy to Apify Platform
```bash
# Push to Apify platform
apify push

# The actor will be available at:
# https://console.apify.com/actors/<your-actor-id>
```

## Requirements

According to [Apify Python Actor Documentation](https://docs.apify.com/academy/deploying-your-code/python-actors):

1. ✅ `.actor/actor.json` - Actor metadata
2. ✅ `.actor/INPUT_SCHEMA.json` - Input schema definition
3. ✅ `src/__main__.py` - Entry point (`python -m src`)
4. ✅ `Dockerfile` - Docker configuration
5. ✅ `requirements.txt` - Python dependencies

All requirements are met! 🎉
