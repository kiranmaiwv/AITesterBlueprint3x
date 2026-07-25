# =============================================================================
# Playwright Test Automation Framework - Docker Image
# =============================================================================
# Author: Pramod Dutta | The Testing Academy
# Website: https://thetestingacademy.com
# =============================================================================

# Use official Playwright image with all browsers pre-installed
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

# Set working directory
WORKDIR /app

# Set environment variables
ENV CI=true
ENV NODE_ENV=test
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Copy package files first (for better caching)
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Create directory for test results
RUN mkdir -p /app/test-results /app/playwright-report /app/tta-report

# Default command - run all tests
CMD ["npx", "playwright", "test"]

# =============================================================================
# Usage Examples:
# =============================================================================
#
# Build the image:
#   docker build -t playwright-framework .
#
# Run all tests:
#   docker run --rm playwright-framework
#
# Run smoke tests:
#   docker run --rm playwright-framework npx playwright test --grep @Smoke
#
# Run with sharding (shard 1 of 4):
#   docker run --rm playwright-framework npx playwright test --shard=1/4
#
# Run with mounted results directory:
#   docker run --rm -v $(pwd)/results:/app/test-results playwright-framework
#
# Run specific test file:
#   docker run --rm playwright-framework npx playwright test login.spec.ts
#
# =============================================================================

