# Playwright Framework Rules

## Overview
This document defines the rules and patterns for the Playwright Test Automation Framework. AI assistants must follow these guidelines when generating code.

---

## 🏗️ Architecture Rules

### Three-Layer Architecture
The framework follows a strict 3-layer architecture:

```
Tests (Layer 3) → Modules (Layer 2) → Pages (Layer 1)
```

**NEVER** skip layers. Tests should NOT directly use Page objects.

---

## 📄 Page Object Rules

### ✅ DO:
- Define locators as **arrow functions** (not properties)
- Keep actions simple (single UI interaction)
- Use `private page: Page` in constructor
- Export class with named export
- Group locators together, then actions

### ❌ DON'T:
- Add business logic in Pages
- Use conditional statements (if/else)
- Call other Pages from a Page
- Store state in Page objects
- Use hardcoded wait times

### Page Class Template:
```typescript
import { Page } from '@playwright/test';

export class ExamplePage {
    constructor(private page: Page) {}

    // ============ LOCATORS (arrow functions) ============
    submitButton = () => this.page.locator('[data-testid="submit"]');
    inputField = () => this.page.locator('#input-field');
    errorMessage = () => this.page.locator('.error-message');

    // ============ ACTIONS (simple, single interactions) ============
    async navigate(): Promise<void> {
        await this.page.goto('/example');
    }

    async fillInput(value: string): Promise<void> {
        await this.inputField().fill(value);
    }

    async clickSubmit(): Promise<void> {
        await this.submitButton().click();
    }

    // ============ ASSERTIONS ============
    async expectErrorVisible(): Promise<void> {
        await expect(this.errorMessage()).toBeVisible();
    }
}
```

---

## ⚙️ Module Rules

### ✅ DO:
- Orchestrate multiple Page actions
- Contain business logic and workflows
- Use Logger for step tracking
- Handle complex conditions
- Return meaningful results

### ❌ DON'T:
- Define locators in Modules
- Use `page.locator()` directly
- Skip step logging for important actions
- Create overly long methods (break into smaller ones)

### Module Class Template:
```typescript
import { Page } from '@playwright/test';
import { ExamplePage } from '../pages/ExamplePage';
import { Logger } from '../utils/Logger';

export class ExampleModule {
    private page: Page;
    private examplePage: ExamplePage;
    private logger: Logger;

    constructor(page: Page) {
        this.page = page;
        this.examplePage = new ExamplePage(page);
        this.logger = Logger.create('ExampleModule');
    }

    async completeWorkflow(data: WorkflowData): Promise<boolean> {
        this.logger.step(1, 'Navigate to page');
        await this.examplePage.navigate();

        this.logger.step(2, 'Fill form data');
        await this.examplePage.fillInput(data.value);

        this.logger.step(3, 'Submit form');
        await this.examplePage.clickSubmit();

        this.logger.info('Workflow completed successfully');
        return true;
    }
}
```

---

## 📝 Test Specification Rules

### ✅ DO:
- Use `test.describe()` for grouping
- Use `test.step()` for clear reporting
- Add tags for categorization (@P0, @Login, @Smoke)
- Use fixtures for page objects and modules
- Clean up in `afterEach` when needed

### ❌ DON'T:
- Access Page locators directly
- Skip test.step() for important actions
- Use console.log (use Logger instead)
- Hardcode test data (use testdata files)
- Write overly long test cases

### Test Spec Template:
```typescript
import { test, expect } from '../fixtures';
import { ExampleModule } from '../modules/ExampleModule';

test.describe('@P0 @Example Feature Name', () => {
    let exampleModule: ExampleModule;

    test.beforeEach(async ({ page }) => {
        exampleModule = new ExampleModule(page);
    });

    test('should complete workflow successfully', async ({ page }) => {
        await test.step('Execute workflow', async () => {
            await exampleModule.completeWorkflow({ value: 'test' });
        });

        await test.step('Verify result', async () => {
            await expect(page.locator('.success')).toBeVisible();
        });
    });
});
```

---

## 📁 File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Page | `{Feature}Page.ts` | `LoginPage.ts` |
| Module | `{Feature}Module.ts` | `LoginModule.ts` |
| Test | `{feature}.spec.ts` | `login.spec.ts` |
| API | `{Feature}Api.ts` | `AuthApi.ts` |

---

## 🔗 Path Aliases

Always use path aliases for imports:

```typescript
// ✅ CORRECT
import { LoginPage } from '@pages/LoginPage';
import { LoginModule } from '@modules/LoginModule';
import { Logger } from '@utils/Logger';

// ❌ WRONG
import { LoginPage } from '../../../pages/LoginPage';
```

Available aliases:
- `@pages/*` → `src/pages/*`
- `@modules/*` → `src/modules/*`
- `@utils/*` → `src/utils/*`
- `@fixtures/*` → `src/fixtures/*`
- `@api/*` → `src/api/*`
- `@config/*` → `src/config/*`
- `@testdata/*` → `src/testdata/*`

