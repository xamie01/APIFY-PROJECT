# Apify Schema Fix - Deployment Guide

## ✅ What Was Fixed

The INPUT_SCHEMA.json had an invalid nested structure for API keys that violated Apify's schema validation rules.

### Error Message
```
ERROR: Input schema is not valid (Property schema.properties.apiKeys.openrouter.isSecret is not allowed.)
```

### Root Cause
Apify's input schema specification does **not allow** the `isSecret` attribute on nested properties. It must only be used on top-level properties.

### Solution Applied
API keys were moved from a nested object structure to top-level properties:

**Before (Invalid):**
```json
{
  "apiKeys": {
    "type": "object",
    "properties": {
      "openrouter": {
        "isSecret": true  // ❌ Not allowed
      }
    }
  }
}
```

**After (Valid):**
```json
{
  "openrouterApiKey": {
    "type": "string",
    "isSecret": true  // ✅ Allowed
  },
  "openaiApiKey": {
    "type": "string",
    "isSecret": true  // ✅ Allowed
  }
  // ... etc
}
```

## 📝 Files Modified

1. **`.actor/INPUT_SCHEMA.json`**
   - Moved API keys to top-level properties
   - Added `isSecret: true` flag to each key field
   - Now has 11 total input parameters

2. **`src/main.py`**
   - Updated input parsing logic (lines 180-190)
   - Changed from `input_data.get('apiKeys', {})` to reading individual top-level fields
   - Maintains backward compatibility with environment variables

3. **`.actor/INPUT_EXAMPLE.json`**
   - Updated example to use new schema format
   - Changed from `"apiKeys": {"openrouter": "..."}` to `"openrouterApiKey": "..."`

4. **`DEPLOYMENT_FIX_SUMMARY.md`**
   - Added section documenting this fix
   - Updated API key field names in documentation

## ✅ Verification Completed

All local validation checks passed:

- ✅ JSON syntax is valid
- ✅ No nested `isSecret` properties
- ✅ All 4 API key fields properly configured
- ✅ Input parsing logic correctly extracts keys
- ✅ Apify deployment verification script passes (5/5 checks)
- ✅ Example input matches new schema

## 🚀 Next Steps - Deploy to Apify

Since this environment doesn't have Apify authentication, you'll need to deploy from your local machine:

### 1. Pull the Latest Changes
```bash
git pull origin <your-branch-name>
```

### 2. Verify Locally (Optional)
```bash
python scripts/verify_apify_deployment.py
```

Expected output: `🎉 SUCCESS! All Apify deployment requirements are met.`

### 3. Deploy to Apify
```bash
# Make sure you're logged in
apify login

# Push to Apify platform
apify push
```

### 4. Expected Result
The build should now succeed without the schema validation error. You should see:
```
Info: Deploying Actor 'o-sate-ai-safety-tester' to Apify.
Run: Updated version 1.0 for Actor o-sate-ai-safety-tester.
Run: Building Actor o-sate-ai-safety-tester
...
✅ Build succeeded!
```

## 📋 How Users Will Provide API Keys

Users can now provide API keys in two ways:

### Option 1: Via Apify Actor UI (Recommended)
When running the actor on Apify, users will see these input fields:
- **OpenRouter API Key** (marked as secret 🔒)
- **OpenAI API Key** (marked as secret 🔒)
- **Anthropic API Key** (marked as secret 🔒)
- **Gemini API Key** (marked as secret 🔒)

These fields are optional. If not provided, the actor will fall back to environment variables.

### Option 2: Via Environment Variables
Set in the Apify actor configuration:
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`

## 🔍 Testing After Deployment

1. Go to your actor page on Apify
2. Click "Try it" or "Start"
3. You should see the new API key input fields
4. Verify they are marked as secret (password-style input)
5. Test with a single model run to ensure keys work correctly

## ⚠️ Important Notes

- **No breaking changes**: Environment variables still work as before
- **User keys only**: No personal API keys are bundled in the code
- **Backward compatible**: Old environment-based configuration still works
- **Schema compliant**: Follows Apify's input schema specification

## 🐛 If You Still Get Errors

If you encounter any other schema validation errors:

1. Check the error message carefully
2. Verify the property causing the issue
3. Consult [Apify Input Schema Documentation](https://docs.apify.com/platform/actors/development/actor-definition/input-schema)
4. Common issues:
   - Invalid `editor` values
   - Missing required properties
   - Invalid JSON syntax
   - Unsupported schema features

## 📚 References

- [Apify Input Schema Specification](https://docs.apify.com/platform/actors/development/actor-definition/input-schema)
- [Apify Actor Configuration](https://docs.apify.com/platform/actors/development/actor-definition/actor-json)
- [Apify Python Actors Guide](https://docs.apify.com/academy/deploying-your-code/python-actors)
