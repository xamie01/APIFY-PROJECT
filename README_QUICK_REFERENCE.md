# Quick Reference Guide - Updated README Features

## 📖 What Changed in README.md

### New Sections (Read These First!)

1. **🧪 Safety Testing with 180+ Prompts** (Lines 57-159)
   - Complete testing workflow
   - 180 prompt organization explained
   - Test command examples
   - Results format example
   - Analysis instructions

2. **🔧 Managing Safety Test Prompts** (Lines 365-410)
   - Adding custom prompts
   - Using 3 prompt generators
   - Editing metadata after testing

3. **📚 Project Structure** (Lines 412-455)
   - Visual directory tree
   - Key directories table
   - File organization reference

### Enhanced Sections

4. **🤖 Interactive Model Selection** (Lines 161-220)
   - Still there, now with context about testing

5. **💡 Usage Examples** (Lines 261-350)
   - **NEW**: Test Safety Prompts (bash commands)
   - **NEW**: Programmatic Safety Testing (Python)
   - Original examples preserved

### Reference Information

6. **🚀 Development Roadmap** (Lines 456-550)
   - Renamed from "Week 1-4 Guide"
   - Clearer structure

## 🎯 Where to Start

### If you want to...

**Run tests immediately:**
→ Go to "🧪 Safety Testing with 180+ Prompts"
→ Scroll to "Quick Start: Run Safety Tests"
→ Copy the first command

**Understand the prompts:**
→ Go to "Safety Test Structure"
→ See all 9 categories and what they test

**Write custom prompts:**
→ Go to "🔧 Managing Safety Test Prompts"
→ See "Adding Custom Prompts"

**Understand project layout:**
→ Go to "📚 Project Structure"
→ See visual directory tree

**Use Python to test:**
→ Go to "💡 Usage Examples"
→ Look at "Test Safety Prompts (bash commands)" and "Programmatic Safety Testing"

## 📊 Key Stats

| Item | Count |
|------|-------|
| New README sections | 3 |
| Lines added | ~250 |
| Command examples | 8+ |
| Code examples | 3+ |
| Tables added | 3 |
| Coverage | All new testing features |

## 🚀 Quick Commands (From README)

```bash
# Test 5 prompts with Mistral
python scripts/run_safety_tests.py --limit 5 --category dangerous_capabilities --subcategory bio_threats --models openrouter-mistral-7b

# Test all with multiple models
python scripts/run_safety_tests.py --models openrouter-mistral-7b openrouter-llama-3.3-70b

# Test specific category
python scripts/run_safety_tests.py --category alignment_compliance --limit 20
```

## 📁 Prompt Organization (From README)

```
prompts/
├── dangerous_capabilities/   (Stage 1: 60 prompts)
│   ├── bio_threats/         (20 prompts: DAN-0001-0039)
│   ├── cyber_threats/       (20 prompts: DAN-0041-0079)
│   └── wmd_threats/         (20 prompts: DAN-0081-0119)
├── alignment_compliance/     (Stage 2: 60 prompts)
│   ├── rule_violations/     (20 prompts: ALN-0061-0099)
│   ├── indirect_injections/ (20 prompts: ALN-0101-0139)
│   └── corrigibility/       (20 prompts: ALN-0141-0179)
└── instrumental_convergence/ (Stage 3: 60 prompts)
    ├── resource_hoarding/   (20 prompts: INS-0021-0059)
    ├── deception/           (20 prompts: INS-0061-0099)
    └── strategic_behavior/  (20 prompts: INS-0101-0139)
```

## ✨ Highlights

### Most Important Addition
**"🧪 Safety Testing with 180+ Prompts"** - Complete guide to using the new testing system

### Most Useful Feature Explained
**"Test Results"** - Shows exactly what test output looks like

### Best for Learning
**"Project Structure"** - Visual tree makes it easy to understand where everything is

### Best for Quick Starts
**"Quick Start: Run Safety Tests"** - Copy-paste ready commands

## 🔄 What Wasn't Changed

✅ All original sections intact
✅ Quick Start section unchanged  
✅ Installation instructions same
✅ Model selection guide preserved
✅ Sandbox documentation untouched
✅ Configuration guide same
✅ Troubleshooting section expanded
✅ Contributing guidelines unchanged

## 📚 Related Documents

- `TESTING_COMPLETE_SUMMARY.md` - Overall testing status and achievements
- `README_UPDATE_SUMMARY.md` - Detailed list of all changes
- `PROMPT_CONVERSION_SUMMARY.md` - How the 180 prompts were created
- `prompts/*/` - The actual 180 test prompts

## 🎓 Learning Path

**Beginner** (10 min)
1. Read "🧪 Safety Testing with 180+ Prompts" intro
2. Run: `python scripts/run_safety_tests.py --limit 5`
3. Check: `outputs/safety_tests/test_results_*.json`

**Intermediate** (30 min)
1. Read entire "🧪 Safety Testing" section
2. Read "💡 Usage Examples" - Test Safety Prompts
3. Run tests on different categories
4. Analyze results in `outputs/safety_tests/`

**Advanced** (1-2 hours)
1. Read "🔧 Managing Safety Test Prompts"
2. Create custom prompts using generator scripts
3. Run full test suite: `python scripts/run_safety_tests.py`
4. Update metadata in JSON files with results

## 🎯 Success Indicators

You'll know you've mastered the new features when:
- [ ] You can run a test with 1 command
- [ ] You understand the 3 stages and 9 categories
- [ ] You can interpret test result JSON files
- [ ] You know how to add custom prompts
- [ ] You can update metadata after testing

---

**Last Updated**: 2025-11-12  
**README Lines**: ~900  
**Changes**: 5 new sections, 3 enhanced sections  
**Status**: ✅ Complete and tested
