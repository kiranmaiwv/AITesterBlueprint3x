#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const args = process.argv.slice(2);
const configArg = args.find((arg) => arg.startsWith('--config='));
const configPath = configArg ? configArg.split('=')[1] : 'rules/framework-rule-engine.json';
const checkStaged = args.includes('--staged');
const checkChanged = args.includes('--changed');

const repoRoot = process.cwd();
const absoluteConfigPath = path.resolve(repoRoot, configPath);

if (!fs.existsSync(absoluteConfigPath)) {
    console.error(`Rule config not found: ${absoluteConfigPath}`);
    process.exit(1);
}

const config = JSON.parse(fs.readFileSync(absoluteConfigPath, 'utf8'));

function toPosix(inputPath) {
    return inputPath.split(path.sep).join('/');
}

function isInsideFolder(filePath, folder) {
    const normalizedFile = toPosix(filePath);
    const normalizedFolder = toPosix(folder).replace(/\/$/, '');
    return normalizedFile === normalizedFolder || normalizedFile.startsWith(`${normalizedFolder}/`);
}

function listFilesRecursively(dirPath, results = []) {
    if (!fs.existsSync(dirPath)) {
        return results;
    }

    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        if (entry.isDirectory()) {
            listFilesRecursively(fullPath, results);
            continue;
        }

        if (entry.isFile() && fullPath.endsWith('.ts')) {
            results.push(fullPath);
        }
    }

    return results;
}

function listGitFiles(command) {
    try {
        const output = execSync(command, { encoding: 'utf8' }).trim();
        if (!output) {
            return [];
        }

        return output
            .split('\n')
            .map((file) => file.trim())
            .filter(Boolean)
            .filter((file) => file.endsWith('.ts'))
            .filter((file) => fs.existsSync(path.resolve(repoRoot, file)));
    } catch {
        return [];
    }
}

function collectCandidateFiles() {
    if (checkStaged) {
        return listGitFiles('git diff --cached --name-only --diff-filter=ACMR');
    }

    if (checkChanged) {
        const changedFiles = listGitFiles('git diff --name-only --diff-filter=ACMR HEAD');
        if (changedFiles.length > 0) {
            return changedFiles;
        }
        return listGitFiles('git ls-files');
    }

    const sourceRoots = config.sourceRoots || [];
    const files = sourceRoots.flatMap((root) => {
        const absoluteRoot = path.resolve(repoRoot, root);
        return listFilesRecursively(absoluteRoot).map((file) => toPosix(path.relative(repoRoot, file)));
    });

    return Array.from(new Set(files));
}

function firstMatchLine(content, regexText) {
    const regex = new RegExp(regexText, 'm');
    const match = regex.exec(content);
    if (!match || typeof match.index !== 'number') {
        return 1;
    }

    return content.slice(0, match.index).split('\n').length;
}

function basenameMatches(regexText, filePath) {
    const regex = new RegExp(regexText);
    return regex.test(path.basename(filePath));
}

function checkPlacementRules(filePath, issues) {
    for (const rule of config.placementRules || []) {
        if (!basenameMatches(rule.fileRegex, filePath)) {
            continue;
        }

        if (!isInsideFolder(filePath, rule.mustBeUnder)) {
            issues.push({
                severity: 'error',
                ruleId: rule.id,
                filePath,
                line: 1,
                message: `${rule.message}. Expected folder: ${rule.mustBeUnder}`,
            });
        }
    }
}

function checkFolderNamingRules(filePath, issues) {
    const fileName = path.basename(filePath);

    for (const rule of config.folderNamingRules || []) {
        if (!isInsideFolder(filePath, rule.folder)) {
            continue;
        }

        const allowed = (rule.allowedFileRegex || []).some((regexText) => new RegExp(regexText).test(fileName));
        if (!allowed) {
            issues.push({
                severity: 'error',
                ruleId: rule.id,
                filePath,
                line: 1,
                message: `${rule.message}. Found: ${fileName}`,
            });
        }
    }
}

function checkContentRule(filePath, content, rule, severity, issues) {
    if (!isInsideFolder(filePath, rule.folder)) {
        return;
    }

    if (rule.fileRegex && !basenameMatches(rule.fileRegex, filePath)) {
        return;
    }

    for (const regexText of rule.requireRegex || []) {
        const regex = new RegExp(regexText, 'm');
        if (!regex.test(content)) {
            issues.push({
                severity,
                ruleId: rule.id,
                filePath,
                line: 1,
                message: rule.message,
            });
        }
    }

    for (const regexText of rule.forbidRegex || []) {
        const regex = new RegExp(regexText, 'm');
        if (regex.test(content)) {
            issues.push({
                severity,
                ruleId: rule.id,
                filePath,
                line: firstMatchLine(content, regexText),
                message: rule.message,
            });
        }
    }
}

function runChecks() {
    const files = collectCandidateFiles();

    if (files.length === 0) {
        console.log('No TypeScript files found for rule validation.');
        return { errors: [], warnings: [] };
    }

    const issues = [];

    for (const filePath of files) {
        const absolutePath = path.resolve(repoRoot, filePath);
        const content = fs.readFileSync(absolutePath, 'utf8');

        checkPlacementRules(filePath, issues);
        checkFolderNamingRules(filePath, issues);

        for (const rule of config.contentRules || []) {
            checkContentRule(filePath, content, rule, 'error', issues);
        }

        for (const rule of config.warningRules || []) {
            checkContentRule(filePath, content, rule, 'warning', issues);
        }
    }

    const errors = issues.filter((issue) => issue.severity === 'error');
    const warnings = issues.filter((issue) => issue.severity === 'warning');

    console.log(`Rule engine checked ${files.length} file(s).`);

    for (const error of errors) {
        console.error(`ERROR   [${error.ruleId}] ${error.filePath}:${error.line} ${error.message}`);
    }

    for (const warning of warnings) {
        console.warn(`WARNING [${warning.ruleId}] ${warning.filePath}:${warning.line} ${warning.message}`);
    }

    if (errors.length === 0) {
        console.log(`Rule validation passed with ${warnings.length} warning(s).`);
    } else {
        console.error(`Rule validation failed with ${errors.length} error(s) and ${warnings.length} warning(s).`);
    }

    return { errors, warnings };
}

const result = runChecks();
process.exit(result.errors.length > 0 ? 1 : 0);
