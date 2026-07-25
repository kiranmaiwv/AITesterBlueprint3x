# 📋 Quick Reference Guide

> **Playwright Test Automation Framework** by [Pramod Dutta](https://thetestingacademy.com)

---

## 🚀 Key Commands

| Command | Description |
|---------|-------------|
| `npm test` | Run all tests |
| `npm run test:headed` | Run with visible browser |
| `npm run test:ui` | Open Playwright UI mode |
| `npm run test:debug` | Debug with inspector |
| `npm run report` | Show HTML report |
| `npx playwright codegen` | Record new tests |
| `npx playwright show-trace` | View trace files |

### Filter Tests

```bash
# Run by tag
npx playwright test --grep "@P0"
npx playwright test --grep "@Login"

# Run specific file
npx playwright test login.spec.ts

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox

# Run headed (visible browser)
npx playwright test --headed
```

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────┐
│  LAYER 3: Tests (*.spec.ts)         │
│  • Test scenarios & assertions      │
│  • Uses Modules only                │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  LAYER 2: Modules (*Module.ts)      │
│  • Business logic & workflows       │
│  • Orchestrates Page actions        │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│  LAYER 1: Pages (*Page.ts)          │
│  • Locators (arrow functions)       │
│  • Simple UI actions only           │
└─────────────────────────────────────┘
```

---

## 📁 Folder Structure

```
src/
├── pages/      → Locators & basic actions
├── modules/    → Business logic
├── tests/      → Test specifications
├── api/        → API testing layer
├── utils/      → Logger, WaitHelper, etc.
├── fixtures/   → Custom Playwright fixtures
├── config/     → Configuration
└── testdata/   → JSON test data
```

---

## ✅ Best Practices Checklist

### Page Class
- [ ] Locators as arrow functions: `btn = () => this.page.locator('#btn')`
- [ ] No business logic or conditionals
- [ ] Private page in constructor
- [ ] Named exports only

### Module Class
- [ ] Uses Page class methods only
- [ ] No direct `page.locator()` calls
- [ ] Logger for step tracking
- [ ] Async/await throughout

### Test Spec
- [ ] Tags: `@P0`, `@Login`, etc.
- [ ] `test.step()` for reporting
- [ ] beforeEach/afterEach cleanup
- [ ] Uses fixtures

---

## 🚫 Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| `page.locator()` in Module | Use `this.loginPage.method()` |
| `if/else` in Page class | Keep logic in Module |
| Missing `test.step()` | Wrap actions in steps |
| `await page.waitForTimeout(5000)` | Use explicit waits |
| Duplicate page instances | Use fixtures |
| `console.log()` | Use Logger |

---

## 🏷️ Test Tags

| Tag | Usage |
|-----|-------|
| `@P0` | Critical priority |
| `@P1` | High priority |
| `@P2` | Medium priority |
| `@Smoke` | Smoke tests |
| `@Regression` | Full regression |
| `@Login` | Feature tag |

### Run by tag:
```bash
npx playwright test --grep "@P0"
npx playwright test --grep "@Smoke"
npx playwright test --grep "@Login"
```

---

## 🔗 Path Aliases

```typescript
import { LoginPage } from '@pages/LoginPage';
import { LoginModule } from '@modules/LoginModule';
import { Logger } from '@utils/Logger';
import { config } from '@config/index';
import usersData from '@testdata/users.json';
```

---

## 📊 Reports

```bash
# View HTML report
npx playwright show-report

# View trace (on failure)
npx playwright show-trace test-results/trace.zip
```

Reports location:
- `playwright-report/` - HTML reports
- `test-results/` - JSON, screenshots, videos

---

## 🔧 Environment Variables

```env
BASE_URL=https://your-app.com
TEST_USERNAME=testuser
TEST_PASSWORD=testpass123
API_TIMEOUT=30000
LOG_LEVEL=INFO
```

---

> 📚 For detailed architecture, see [ARCHITECTURE.html](./ARCHITECTURE.html)

