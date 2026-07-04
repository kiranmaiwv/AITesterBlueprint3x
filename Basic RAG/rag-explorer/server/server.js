import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
import dotenv from 'dotenv';
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import { randomUUID } from 'crypto';
import multer from 'multer';
import mammoth from 'mammoth';

const require = createRequire(import.meta.url);
const pdfParse = require('pdf-parse');

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 4000;
const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json());

const dataDir = path.resolve(__dirname, '..', '..', 'data');
const pdfPath = process.env.PDF_PATH || findFirstPdf(dataDir);

function findFirstPdf(dir) {
  if (!fs.existsSync(dir)) return '';
  const entries = fs.readdirSync(dir);
  const pdf = entries.find((entry) => entry.toLowerCase().endsWith('.pdf'));
  return pdf ? path.join(dir, pdf) : '';
}

function stripHtml(value = '') {
  return value
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/\s+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function parseConfluencePageId(confluenceUrl) {
  try {
    const url = new URL(confluenceUrl);
    const match = url.pathname.match(/\/pages\/(\d+)(?:\/|$)/);
    if (match) return match[1];
    const pageId = url.searchParams.get('pageId');
    if (pageId) return pageId;
    const contentId = url.searchParams.get('contentId');
    if (contentId) return contentId;
  } catch {
    return null;
  }
  return null;
}

function getConfluenceBaseUrl(confluenceUrl) {
  const url = new URL(confluenceUrl);
  const basePath = url.pathname.startsWith('/wiki') ? '/wiki' : '';
  return `${url.origin}${basePath}`;
}

async function fetchConfluenceText(confluenceUrl) {
  const pageId = parseConfluencePageId(confluenceUrl);
  if (!pageId) {
    throw new Error('Unable to extract a Confluence page ID from the supplied URL.');
  }

  const baseUrl = getConfluenceBaseUrl(confluenceUrl);
  const username = process.env.CONFLUENCE_USERNAME;
  const apiToken = process.env.CONFLUENCE_API_TOKEN || process.env.CONFLUENCE_TOKEN;
  const headers = { Accept: 'application/json' };

  if (username && apiToken) {
    headers.Authorization = `Basic ${Buffer.from(`${username}:${apiToken}`).toString('base64')}`;
  }

  const response = await fetch(`${baseUrl}/rest/api/content/${pageId}?expand=body.storage,body.view`, { headers });
  if (!response.ok) {
    throw new Error(`Confluence request failed with status ${response.status}`);
  }

  const data = await response.json();
  const rawContent = data.body?.storage?.value || data.body?.view?.value || '';
  const text = stripHtml(rawContent);

  if (!text) {
    throw new Error('Confluence returned no readable content.');
  }

  return { text, sourceName: data.title || 'confluence-page.txt' };
}

async function extractTextFromUpload(file) {
  const extension = path.extname(file.originalname).toLowerCase();

  if (extension === '.pdf') {
    const parsedPdf = await pdfParse(file.buffer);
    return { text: parsedPdf.text, sourceName: file.originalname };
  }

  if (extension === '.doc' || extension === '.docx') {
    const { value } = await mammoth.extractRawText({ buffer: file.buffer });
    return { text: value, sourceName: file.originalname };
  }

  throw new Error('Unsupported file type. Upload a PDF, DOC, or DOCX file.');
}

function writeTempTextFile(text, sourceName) {
  const tempDir = os.tmpdir();
  const safeName = sourceName.replace(/[^a-zA-Z0-9._-]/g, '_');
  const tempPath = path.join(tempDir, `${Date.now()}-${randomUUID()}-${safeName}.txt`);
  fs.writeFileSync(tempPath, text, 'utf8');
  return tempPath;
}

function runPython(args, extraEnv = {}) {
  return new Promise((resolve, reject) => {
    const pythonCommand = process.env.PYTHON_BIN || '/usr/local/bin/python3.14';
    const child = spawn(pythonCommand, ['rag_pipeline.py', ...args], {
      cwd: __dirname,
      env: { ...process.env, ...extraEnv, PDF_PATH: pdfPath },
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr || `Python exited with code ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Failed to parse Python output: ${stdout}`));
      }
    });
  });
}

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', pdfPath });
});

app.post('/api/ingest', upload.single('file'), async (req, res) => {
  try {
    const confluenceUrl = req.body.confluenceUrl || req.body.url || '';
    const sourceType = req.body.sourceType || (req.file ? 'upload' : confluenceUrl ? 'confluence' : 'pdf');

    if (req.file) {
      const { text, sourceName } = await extractTextFromUpload(req.file);
      const tempPath = writeTempTextFile(text, sourceName);

      try {
        const result = await runPython(['--ingest'], {
          SOURCE_TYPE: 'text',
          SOURCE_PATH: tempPath,
          SOURCE_NAME: sourceName,
        });
        res.json(result);
      } finally {
        if (fs.existsSync(tempPath)) {
          fs.unlinkSync(tempPath);
        }
      }
      return;
    }

    if (confluenceUrl) {
      const { text, sourceName } = await fetchConfluenceText(confluenceUrl);
      const tempPath = writeTempTextFile(text, sourceName);

      try {
        const result = await runPython(['--ingest'], {
          SOURCE_TYPE: 'text',
          SOURCE_PATH: tempPath,
          SOURCE_NAME: sourceName,
        });
        res.json(result);
      } finally {
        if (fs.existsSync(tempPath)) {
          fs.unlinkSync(tempPath);
        }
      }
      return;
    }

    if (!pdfPath) {
      return res.status(400).json({ error: 'No PDF found in the data folder.' });
    }

    const result = await runPython(['--ingest'], { SOURCE_TYPE: sourceType });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/query', async (req, res) => {
  try {
    const { query } = req.body;
    if (!query) {
      return res.status(400).json({ error: 'A question is required.' });
    }

    const result = await runPython(['--query', query]);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`RAG server listening on http://localhost:${PORT}`);
  console.log(`PDF path: ${pdfPath || 'not found'}`);
});
