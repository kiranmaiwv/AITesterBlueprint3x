# 🚀 Phase 4: Quick Start - Run the App

## Prerequisites Check
```bash
# Check Node is installed
node --version  # Should be 16+

# Check Python is installed  
python3 --version  # Should be 3.8+
```

## Step 1: Start Backend (Terminal 1)

```bash
cd /Users/kiranmaiwunnava/AITesterBlueprint3x-main/BlastFrameworkProject

# Run Flask server
python3 app.py
```

**Expected Output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

✅ Backend ready at: `http://localhost:5000`

---

## Step 2: Start Frontend (Terminal 2)

```bash
cd /Users/kiranmaiwunnava/AITesterBlueprint3x-main/BlastFrameworkProject

# Run Vite dev server
npm run dev
```

**Expected Output:**
```
  VITE v4.3.9  ready in XXX ms

  ➜  Local:   http://localhost:5000
  ➜  press h to show help
```

✅ Frontend ready at: `http://localhost:3000`

---

## Step 3: Test the UI

### Page 1: Settings
1. Navigate to `http://localhost:3000`
2. Enter test credentials:
   - **Email:** kiranmaiwv@gmail.com
   - **JIRA Token:** (from .env)
   - **JIRA URL:** https://kiranmaiwv.atlassian.net
   - **GROQ Key:** (from .env)
   - **Issue Key:** KAN-1

3. Click "Continue to Preview"
4. ✅ Should see Settings form with validation

### Page 2: Issue Preview
1. Click "Fetch Issue: KAN-1"
2. ✅ Should either:
   - Show issue details if KAN-1 exists
   - Show error message if KAN-1 not found

### Page 3: Generation (if issue found)
1. App auto-starts generation
2. ✅ Should see loading spinner
3. ✅ Should complete in <30s

### Page 4: Results (if generation succeeds)
1. ✅ See strategy preview
2. ✅ Download, Copy, or Generate New buttons work

---

## 🧪 Phase 4 Testing Tasks

### Quick Testing (5 minutes)
- [ ] App loads without errors
- [ ] Settings form is visible
- [ ] Continue button navigates to preview
- [ ] Back button works
- [ ] Error messages display clearly

### Full Testing (15 minutes)
- [ ] Complete flow from Settings → Results
- [ ] All buttons clickable
- [ ] No console errors
- [ ] Loading states visible
- [ ] Download button works

### Detailed Testing (30+ minutes)
- [ ] Test each error scenario:
  - [ ] Invalid JIRA credentials
  - [ ] Non-existent issue
  - [ ] Missing GROQ key
- [ ] Test on mobile browser
- [ ] Check accessibility (Tab navigation)
- [ ] Verify mobile responsiveness

---

## 🛠️ Debugging Tips

### Backend Issues

**Port 5000 already in use:**
```bash
lsof -i :5000
kill -9 <PID>
```

**Module import error:**
```bash
pip3 install -r requirements.txt --upgrade
```

**JIRA API failing:**
- Check `.env` credentials
- Verify issue key exists
- Run: `python3 tools/verify_kan1.py`

### Frontend Issues

**Port 3000 already in use:**
```bash
lsof -i :3000
kill -9 <PID>
```

**npm install failed:**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Can't connect to backend:**
- Verify Flask server is running
- Check browser console (F12)
- Try `curl http://localhost:5000/health`

---

## 📊 Phase 4 Completion Checklist

### Code Quality
- [ ] No console errors
- [ ] No warnings
- [ ] Clean code without debug logs
- [ ] Comments where needed

### UI/UX
- [ ] All pages render correctly
- [ ] Error messages are clear
- [ ] Loading states visible
- [ ] Buttons are responsive

### Functionality
- [ ] Settings form validates input
- [ ] JIRA fetch works (or shows proper error)
- [ ] Strategy generation works (or shows proper error)
- [ ] Download/copy buttons work

### Responsive Design
- [ ] Desktop (1920x1080) - ✓ Works
- [ ] Tablet (768x1024) - ✓ Works (simulate in DevTools)
- [ ] Mobile (375x812) - ✓ Works (simulate in DevTools)

### Documentation
- [ ] README.md complete
- [ ] DEPLOYMENT.md complete
- [ ] Inline code comments added
- [ ] Error messages are helpful

---

## 📝 Notes for Phase 4

**Known Limitations:**
- KAN-1 may not exist yet in your JIRA (will show proper error)
- GROQ API may have rate limits (will show proper error)
- Some errors are expected to test error handling

**What to Look For:**
- Are error messages helpful?
- Is the flow intuitive?
- Does the UI feel responsive?
- Are there any layout issues?

**Improvements to Make:**
- If you see any UI glitches, note them
- If error messages are confusing, improve them
- If performance is slow, optimize
- If mobile looks weird, fix responsive styles

---

## ✅ Ready? Let's Go!

```bash
# Terminal 1
python3 app.py

# Terminal 2 (in same project)
npm run dev

# Open browser
http://localhost:3000
```

**Report any issues you find!** 🐛

---

**Last Updated:** 2026-06-10
