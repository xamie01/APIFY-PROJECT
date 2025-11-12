# Frontend Integration - Safety Testing Web UI

## What's New

A beautiful, easy-to-use web interface for running AI safety tests has been integrated into O-SATE. Users can now:

✅ Select multiple AI models to test  
✅ Choose specific test categories and subcategories  
✅ Run tests with configurable limits  
✅ View real-time test results and statistics  
✅ See refusal rates by category and model  
✅ Track test history and trends  

## Files Added/Modified

### New Files
- `src/testing_api.py` - Flask API endpoints for test management
- `frontend/src/components/SafetyTestPanel.jsx` - React test panel component
- `frontend/src/components/SafetyTestPanel.css` - Professional styling

### Modified Files
- `frontend/app.py` - Added testing API route setup
- `frontend/src/App.jsx` - Integrated SafetyTestPanel component

## How to Run

### 1. **Terminal 1: Start Backend**
```bash
cd C:\Users\trust\O-SATE
python frontend/app.py
```

**Expected Output:**
```
[11/12/25 15:30:00] INFO - Starting O-SATE Web Frontend on 0.0.0.0:5000
[11/12/25 15:30:00] INFO - Debug mode: True
 * Running on http://127.0.0.1:5000
```

### 2. **Terminal 2: Start Frontend**
```bash
cd C:\Users\trust\O-SATE\frontend
npm run dev
```

**Expected Output:**
```
VITE v5.0.0 ready in 234 ms

➜ Local:   http://localhost:3000/
➜ Press h to show help
```

### 3. **Open Browser**
Navigate to: **http://localhost:3000**

## User Interface Tour

### 📊 Statistics Dashboard
At the top, you'll see:
- **Tests Run** - Total number of test sessions
- **Prompts Tested** - Total individual prompts tested
- **Refusal Rate** - Percentage of safely refused prompts
- **Last Test** - Date of most recent test

### 🤖 Configure Test Section

**1. Select Models**
- Click model buttons to toggle selection
- At least one model required to run tests
- Models from `config/default_config.yaml` shown

**2. Select Category**
- Dropdown with all 9 test categories:
  - dangerous_capabilities (60 prompts)
  - alignment_compliance (60 prompts)
  - instrumental_convergence (60 prompts)
- Select "All Categories" to test everything

**3. Select Subcategory**
- Only shown if category selected
- Shows prompt count for each subcategory
- Select specific subcategory or all

**4. Set Limit**
- Enter 1-180 (total available prompts)
- Useful for quick testing (e.g., limit=5)

**5. Run Safety Tests Button**
- Click to start tests
- Shows progress bar while running
- Status updates displayed below

### 📈 Results Dashboard

After testing, you'll see:

**1. Results Summary**
- Total Prompts Tested
- Models Used
- Passed (Safely Refused)
- Failed (Didn't Refuse)

**2. Results by Category**
- Table showing each category's results
- Passed/Failed/Refusal Rate columns
- Visual progress bar for each category

**3. Model Performance**
- Cards showing each model's refusal rate
- Sorted by performance
- Shows test count per model

## API Endpoints

All exposed via Flask `/api/tests/*`:

```
GET  /api/tests/models              → Available models
GET  /api/tests/categories          → All prompt categories
GET  /api/tests/statistics          → Aggregated statistics
POST /api/tests/run                 → Run tests
GET  /api/tests/results             → Recent test results
GET  /api/tests/prompt/<cat>/<subcat>/<id> → Specific prompt details
```

## Example Workflows

### Quick Safety Check (5 minutes)
1. Select 1-2 models
2. Set Limit to 5
3. Click "Run Safety Tests"
4. View results in real-time

### Full Category Test (30 minutes)
1. Select all models
2. Choose specific category (e.g., "dangerous_capabilities")
3. Set Limit to 60
4. Run test
5. Review refusal rates by subcategory

### Comprehensive Suite (2-4 hours)
1. Select all models
2. Leave category as "All"
3. Set Limit to 180
4. Run full test
5. Export/analyze complete results

## Troubleshooting

### Issue: "Failed to load models"
**Solution**: Check if backend is running (`python frontend/app.py`)

### Issue: "Error running tests"
**Solution**: 
1. Check OpenRouter API key in `.env`
2. Verify network connectivity
3. Check backend logs

### Issue: Tests running slowly
**Solution**: 
1. Reduce limit (test 10 instead of 180)
2. Use fewer models (test 1-2 instead of all)
3. Check API rate limits

### Issue: Results not showing
**Solution**:
1. Wait for all prompts to complete
2. Check browser console for errors (F12)
3. Refresh page and try again

## Performance Tips

- **Quick test**: limit=5, 1 model = ~1 minute
- **Batch test**: limit=20, 2 models = ~5 minutes
- **Full suite**: limit=180, 3 models = 3-4 hours
- Results cached in `outputs/safety_tests/`

## Component Architecture

```
App.jsx
├── Header (Logo, nav)
├── SafetyTestPanel
│   ├── Stats Dashboard
│   ├── Test Configuration
│   │   ├── Model Selection
│   │   ├── Category Selection
│   │   ├── Subcategory Selection
│   │   └── Limit Input
│   ├── Run Control
│   └── Results Display
│       ├── Summary Cards
│       ├── Results Table
│       └── Model Performance
├── ModelSelector
├── AIQuery
└── Sandbox
```

## API Response Format

### Run Test Response
```json
{
  "status": "success",
  "summary": {
    "timestamp": "2025-11-12T...",
    "models": ["openrouter-mistral-7b"],
    "category": "dangerous_capabilities",
    "subcategory": "bio_threats",
    "tests_run": 5
  },
  "results": {
    "dangerous_capabilities/bio_threats": {
      "passed": 4,
      "failed": 1
    }
  },
  "test_log": [...]
}
```

### Statistics Response
```json
{
  "status": "success",
  "statistics": {
    "total_tests_run": 12,
    "total_prompts_tested": 180,
    "overall_refusal_rate": 0.85,
    "by_category": {...},
    "by_model": {...}
  }
}
```

## Dark Theme Features

✨ **Professional Design**:
- Dark gradient background (navy to indigo)
- Purple accent colors
- Glassmorphism effects
- Smooth animations and transitions
- Mobile responsive

🎨 **Color Scheme**:
- Primary: #667eea (Purple)
- Secondary: #764ba2 (Violet)
- Success: #4CAF50 (Green)
- Danger: #ff6b6b (Red)
- Background: #1a1a2e (Dark navy)

## Next Steps

1. ✅ Run first test with UI
2. ✅ Review results and statistics
3. ✅ Test different model combinations
4. ✅ Identify patterns in model behavior
5. ✅ Export results for analysis

---

**Need Help?** Check the main README.md or backend logs (`outputs/logs/`)
