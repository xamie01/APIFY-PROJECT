# 🎯 O-SATE Web UI - Quick Start Guide

## ✨ What You Get

A **beautiful, powerful web interface** for testing AI safety:

```
┌─────────────────────────────────────────────────────────────┐
│                   🧪 AI Safety Test Suite                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Statistics Dashboard                                   │
│  ├─ Tests Run: 12                                          │
│  ├─ Prompts Tested: 180                                    │
│  ├─ Refusal Rate: 85.2%                                    │
│  └─ Last Test: Nov 12, 2025                               │
│                                                             │
│  🤖 Configure Test                                         │
│  ├─ Select Models (8 available)                            │
│  ├─ Select Category (9 available)                          │
│  ├─ Select Subcategory (by category)                       │
│  ├─ Set Limit (1-180)                                      │
│  └─ [▶️ Run Safety Tests]                                   │
│                                                             │
│  📈 Results (after testing)                                │
│  ├─ Summary by Category                                    │
│  ├─ Model Performance Comparison                           │
│  └─ Detailed Result Breakdown                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Start in 30 Seconds

### Step 1: Open PowerShell
```powershell
cd C:\Users\trust\O-SATE
./start.ps1
```

### Step 2: Run These Commands (in 2 separate terminals)

**Terminal 1 - Backend:**
```powershell
python frontend/app.py
```
Expected: `Running on http://127.0.0.1:5000`

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```
Expected: `Local: http://localhost:3000/`

### Step 3: Open Browser
```
http://localhost:3000
```

🎉 **Done!** The web UI is now running!

## 📝 Quick Testing (5 minutes)

1. **Select 1 Model**
   - Click one model button (e.g., Mistral-7B)

2. **Set Limit to 5**
   - Enter "5" in the limit field

3. **Click "Run Safety Tests"**
   - Watch the progress bar fill up
   - Results display automatically

4. **View Results**
   - See refusal rate
   - Check model performance
   - Review category breakdown

## 🎯 Full Test Suite (3-4 hours)

1. **Select All Models**
   - Click each model to select (8 models)

2. **Leave Category as "All"**
   - Tests all 180 prompts

3. **Set Limit to 180**

4. **Click "Run Safety Tests"**
   - Go get coffee ☕
   - Results will be saved automatically

5. **View Comprehensive Results**
   - See which models perform best
   - Identify categories with lower refusal rates
   - Compare model behaviors

## 🎨 UI Overview

### Top Section: Statistics
Shows aggregate stats from all previous tests
- Quick glance at overall performance
- Last test date
- Total prompts tested

### Middle Section: Configuration
Choose exactly what to test
- **Models**: Multi-select from available options
- **Category**: 3 main categories
- **Subcategory**: 9 total subcategories
- **Limit**: 1-180 prompts
- **Run Button**: Starts the test

### Bottom Section: Results
Displays after testing completes
- Summary cards (passed, failed, rates)
- Detailed table by category
- Model performance cards
- Overall statistics

## 🔧 Troubleshooting

### "Can't connect to backend"
```powershell
# Make sure backend is running
python frontend/app.py
```

### "Npm: command not found"
```powershell
# Install Node.js first from nodejs.org
# Then reinstall dependencies
cd frontend
npm install
npm run dev
```

### "No models available"
```yaml
# Check config/default_config.yaml has models listed:
openrouter_models:
  - openrouter-mistral-7b
  - openrouter-llama-3.3-70b
  # etc
```

### Tests running slowly
- **Reduce limit** (test 5 instead of 180)
- **Use fewer models** (test 1-2 instead of all)
- **Check internet** (API rate limits apply)

## 📊 Understanding Results

### Refusal Rate
- **High (>80%)**: ✅ Good - Model refusing dangerous requests
- **Medium (50-80%)**: ⚠️ Okay - Some requests slipping through
- **Low (<50%)**: ❌ Bad - Model not refusing harmful prompts

### By Category
- **Dangerous Capabilities**: Bio/Cyber/WMD threats
- **Alignment & Compliance**: Rules, injections, corrigibility
- **Instrumental Convergence**: Deception, resource hoarding, strategy

### Model Performance
- Larger models typically perform better
- Some models specialized in different areas
- Compare across models to see strengths

## 💾 Results Storage

All test results automatically saved:
```
outputs/safety_tests/test_results_20251112_150000.json
```

Results include:
- Timestamp of test
- Models tested
- Category breakdown
- Pass/fail for each prompt
- Confidence scores

## 🌐 API Endpoints (for developers)

```bash
# Get models
curl http://localhost:5000/api/tests/models

# Get categories
curl http://localhost:5000/api/tests/categories

# Run test
curl -X POST http://localhost:5000/api/tests/run \
  -d '{"models":["mistral-7b"],"limit":5}'

# Get statistics
curl http://localhost:5000/api/tests/statistics

# Get past results
curl http://localhost:5000/api/tests/results
```

## 🎯 Common Workflows

### Workflow 1: Quick Validation (30 min)
```
1. Select 1 model (mistral-7b)
2. Set limit: 10
3. Run test
4. Check: Is refusal rate >70%?
```

### Workflow 2: Model Comparison (1 hour)
```
1. Select 2-3 models
2. Set limit: 20
3. Run test
4. Compare side-by-side refusal rates
5. Identify best performer
```

### Workflow 3: Category Deep Dive (2 hours)
```
1. Select all models
2. Choose category: "dangerous_capabilities"
3. Set limit: 60
4. Run test
5. Analyze which subcategory has issues
6. Identify gaps in safety measures
```

### Workflow 4: Full Suite Benchmark (4 hours)
```
1. Select all models
2. Leave category: "All"
3. Set limit: 180
4. Run comprehensive test
5. Export results
6. Generate report
```

## 📈 Data Interpretation Guide

### If High Refusal Rate (>90%)
✅ **Good signs:**
- Model reliably refuses dangerous requests
- Aligned with safety best practices
- Minimal prompt injection vulnerability

### If Medium Refusal Rate (60-80%)
⚠️ **Investigate:**
- Which categories have lower rates?
- Which specific prompts are failing?
- Can model be tuned for better safety?

### If Low Refusal Rate (<60%)
❌ **Action needed:**
- Model may require fine-tuning
- Safety alignment needs improvement
- Consider using different model

## 🔐 Data Privacy

- All tests run locally on your computer
- Results stored in `outputs/safety_tests/`
- No data sent to external services
- API keys kept in `.env` (not in code)

## 🎓 Educational Use

This tool is perfect for:
- Understanding AI safety challenges
- Testing prompt injection techniques
- Comparing model safety capabilities
- Learning about alignment issues
- Benchmarking model behavior

## 🚀 Advanced Features

### For Power Users
- **API access** to all endpoints
- **Custom prompt loading** from JSON
- **Result export** to various formats
- **Batch testing** with multiple configurations
- **Statistics aggregation** across runs

### Future Enhancements
- [ ] Real-time WebSocket updates
- [ ] CSV/PDF result export
- [ ] Historical trending charts
- [ ] Custom prompt templates
- [ ] Test scheduling
- [ ] Multi-user support

## 💡 Tips & Tricks

**Tip 1**: Run quick test first to verify setup
- Takes <1 minute
- Confirms everything working
- Then run full suite

**Tip 2**: Use category-specific tests
- Diagnose specific safety issues
- Run faster than full suite
- Identify problem areas

**Tip 3**: Compare models side-by-side
- Select 2-3 different models
- Same category/limit
- See performance differences clearly

**Tip 4**: Monitor results over time
- All results automatically saved
- Track improvements
- Notice safety trends

**Tip 5**: Keep terminal windows open
- Don't close backend while testing
- Don't close frontend during use
- Minimize them to taskbar

## ❓ FAQ

**Q: How long does testing take?**  
A: 5 prompts = 30sec, 20 prompts = 5min, 180 prompts = 3-4 hours

**Q: Can I run tests while doing other things?**  
A: Yes! Tests run in background. Keep browser open but minimize.

**Q: Where are results saved?**  
A: `outputs/safety_tests/test_results_*.json`

**Q: Can I test with custom prompts?**  
A: Yes! Edit JSON files in `prompts/` folder

**Q: How many models can I test at once?**  
A: All 8+ OpenRouter models simultaneously

**Q: Is internet required?**  
A: Yes, to access OpenRouter API for models

**Q: Can I export results?**  
A: Results auto-save as JSON. Can parse/convert as needed.

---

## 🎉 You're Ready!

Everything is set up and ready to go. Start testing:

```powershell
python frontend/app.py    # Terminal 1
npm run dev               # Terminal 2
# Open http://localhost:3000
```

**Happy testing! 🚀**
