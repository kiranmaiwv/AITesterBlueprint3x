# Deployment & Running Guide

## 🚀 Local Development Setup

### Step 1: Install Dependencies

**Python:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Node.js:**
```bash
npm install
```

### Step 2: Configure Environment

Create `.env` file in project root:
```bash
GROQ_KEY="your_groq_api_key_here"
JIRA_EMAIL="your@email.com"
JIRA_API_TOKEN="your_jira_api_token"
JIRA_URL="https://your-instance.atlassian.net"
```

**Where to get credentials:**
- **GROQ_KEY:** https://console.groq.com/keys (free tier available)
- **JIRA credentials:** Your JIRA Account Settings → Security → API tokens

### Step 3: Run the Application

**Open 2 terminals:**

Terminal 1 - Backend:
```bash
python app.py
```
Server will start at: `http://localhost:5000`

Terminal 2 - Frontend:
```bash
npm run dev
```
Frontend will start at: `http://localhost:3000`

### Step 4: Use the App

1. Navigate to `http://localhost:3000`
2. Enter your JIRA and GROQ credentials in Settings
3. Enter a JIRA issue key (e.g., "KAN-1")
4. Click "Continue to Preview"
5. Click "Fetch Issue" to view details
6. Click "Generate Test Strategy"
7. Download or copy the generated strategy

---

## 📦 Production Deployment

### Option 1: Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim as backend
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY tools/ tools/
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]

FROM node:18-alpine as frontend-build
WORKDIR /app
COPY package*.json .
RUN npm install
COPY src/ src/
COPY index.html vite.config.js .
RUN npm run build

FROM nginx:latest
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY --from=backend /app /backend
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t jira-test-strategy-generator .
docker run -p 80:80 -e GROQ_KEY="..." -e JIRA_EMAIL="..." jira-test-strategy-generator
```

### Option 2: Cloud Platforms

**Heroku:**
```bash
heroku create jira-test-strategy
git push heroku main
```

**AWS (Lambda + S3 + CloudFront):**
- Deploy React to S3 + CloudFront
- Deploy Flask to Lambda with RDS/DynamoDB
- Use API Gateway for backend API

**Azure:**
- Frontend: Static Web Apps
- Backend: Azure Functions or App Service
- Use App Configuration for secrets

---

## ✅ Pre-Deployment Checklist

- [ ] `.env` file configured with real credentials
- [ ] All tests passing
- [ ] No console errors in browser/terminal
- [ ] JIRA API responds within 10s
- [ ] GROQ API responds within 30s
- [ ] Generated strategy contains all 8 sections
- [ ] Download functionality working
- [ ] Responsive on mobile devices
- [ ] Error messages clear and helpful

---

## 🐛 Troubleshooting

### "JIRA API returns 404"
- Verify issue key is correct
- Check JIRA credentials are valid
- Ensure API token has project access

### "GROQ API rate limited (429)"
- Wait 60 seconds and retry
- Check API quota at console.groq.com

### "React app won't connect to backend"
- Ensure Flask is running on port 5000
- Check CORS is enabled in app.py
- Verify no firewall blocking localhost:5000

### "Strategy validation fails"
- Check issue has sufficient description
- Verify GROQ response isn't truncated
- Try a different JIRA issue

---

## 📊 Performance Optimization

**Frontend:**
- Code splitting via Vite
- Lazy load components
- Minify on build: `npm run build`

**Backend:**
- Cache JIRA issue data (Redis optional)
- Batch GROQ requests during high load
- Implement request queuing

**Deployment:**
- Use CDN for static files
- Enable gzip compression
- Set appropriate cache headers

---

## 🔒 Security Best Practices

1. **Never commit .env file**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use environment variables** for production secrets
   ```python
   import os
   groq_key = os.getenv('GROQ_KEY')
   ```

3. **Enable HTTPS** in production
   ```python
   # In app.py for production
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   ```

4. **Rate limiting** (optional)
   ```bash
   pip install flask-limiter
   ```

5. **Input validation** - Already implemented via validator.py

---

## 📈 Monitoring & Maintenance

**Logs to monitor:**
- `.tmp/jira_errors.log` - JIRA fetch failures
- `.tmp/groq_errors.log` - AI generation failures
- `.tmp/validation_errors.log` - Output validation failures
- Flask console output - API errors

**Metrics to track:**
- Generation time (target: <30s)
- Success rate (target: >95%)
- API response times
- Error frequency

---

**Last Updated:** 2026-06-10
