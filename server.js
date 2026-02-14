const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execSync } = require('child_process');

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json({ limit: '500mb' }));
app.use(express.static('public'));

const CONFIG_FILE = path.join(__dirname, 'config.json');
const DEFAULT_PARENT = 'repo-files';

const EXCLUDE_PATTERNS = [
  '.git', '.svn', '.hg', '.gitignore', '.gitattributes',
  'node_modules', 'bower_components', 'vendor',
  'target', 'build', 'dist', 'out',
  '__pycache__', '.pytest_cache', '.mypy_cache', '.tox',
  'venv', '.venv', 'env', '.env',
  'bin', 'obj', 'packages',
  '*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.dylib',
  '*.exe', '*.jar', '*.war', '*.ear',
  '*.log', '*.tmp', '*.temp',
  'Thumbs.db', '.DS_Store', 'desktop.ini'
];

function loadConfig() {
  if (fs.existsSync(CONFIG_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf-8'));
    } catch (e) {}
  }
  const username = os.userInfo().username;
  const isNumeric = /^\d+$/.test(username);
  return {
    parent_folder: DEFAULT_PARENT,
    proxy_enabled: false,
    proxy_address: '127.0.0.1',
    proxy_port: 10808,
    proxy_user: '',
    proxy_pass: '',
    download_proxy_enabled: false,
    download_proxy_address: '127.0.0.1',
    download_proxy_port: 10808,
    download_proxy_user: '',
    download_proxy_pass: ''
  };
}

function checkProxy(port) {
  return new Promise((resolve) => {
    const net = require('net');
    const client = new net.Socket();
    
    client.setTimeout(1000);
    
    client.on('connect', () => {
      client.destroy();
      resolve(true);
    });
    
    client.on('timeout', () => {
      client.destroy();
      resolve(false);
    });
    
    client.on('error', () => {
      resolve(false);
    });
    
    client.connect(port, '127.0.0.1');
  });
}

function saveConfig(config) {
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2));
}

function get7zPath() {
  const paths = [
    'C:\\Program Files\\7-Zip\\7z.exe',
    'C:\\Program Files (x86)\\7-Zip\\7z.exe',
    '7z'
  ];
  for (const p of paths) {
    if (p === '7z' || fs.existsSync(p)) return p;
  }
  return '7z';
}

function getFolder(subfolder) {
  const config = loadConfig();
  const parent = config.parent_folder || DEFAULT_PARENT;
  return path.join(parent, subfolder);
}

function ensureFolders() {
  const folders = ['github', 'compress', 'extract', 'download'];
  folders.forEach(f => {
    const dir = getFolder(f);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
}

function shouldExclude(filePath) {
  const name = path.basename(filePath);
  for (const pattern of EXCLUDE_PATTERNS) {
    if (pattern.startsWith('*')) {
      if (name.endsWith(pattern.slice(1))) return true;
    } else if (name === pattern || pattern.includes(name)) {
      return true;
    }
  }
  return false;
}

function runCommand(cmd, cwd) {
  return new Promise((resolve, reject) => {
    exec(cmd, { cwd, windowsHide: true }, (error, stdout, stderr) => {
      if (error) reject(error);
      else resolve({ stdout, stderr });
    });
  });
}

function generateId() {
  return crypto.randomBytes(8).toString('hex');
}

ensureFolders();

app.get('/api/config', (req, res) => {
  res.json(loadConfig());
});

app.get('/api/system-info', (req, res) => {
  const username = os.userInfo().username;
  const isNumeric = /^\d+$/.test(username);
  res.json({
    username: username,
    isNumericUsername: isNumeric
  });
});

app.post('/api/config', (req, res) => {
  saveConfig(req.body);
  ensureFolders();
  res.json({ success: true });
});

app.get('/api/folders', (req, res) => {
  const config = loadConfig();
  const parent = req.query.parent || config.parent_folder || DEFAULT_PARENT;
  res.json({
    github: path.join(parent, 'github'),
    compress: path.join(parent, 'compress'),
    extract: path.join(parent, 'extract'),
    download: path.join(parent, 'download')
  });
});

app.post('/api/github/clone', async (req, res) => {
  const { url } = req.body;
  const config = loadConfig();
  
  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }
  
  const targetDir = getFolder('github');
  let repoName = url.replace(/\.git$/, '').split('/').pop();
  const targetPath = path.join(targetDir, repoName);
  
  if (fs.existsSync(targetPath)) {
    fs.rmSync(targetPath, { recursive: true });
  }
  
  const proxyAddress = config.proxy_address || '127.0.0.1';
  const proxyPort = config.proxy_port || 10808;
  const proxyUser = config.proxy_user || '';
  const proxyPass = config.proxy_pass || '';
  let useProxy = config.proxy_enabled;
  let proxyStatus = 'none';
  
  if (useProxy) {
    const proxyOpen = await checkProxy(proxyPort);
    if (proxyOpen) {
      proxyStatus = 'connected';
    } else {
      proxyStatus = 'not_open';
      return res.status(400).json({ 
        error: `Proxy port ${proxyPort} is not open. Please start your proxy server or disable proxy in settings.`,
        proxyStatus: 'not_open',
        proxyPort
      });
    }
  } else {
    const proxyOpen = await checkProxy(proxyPort);
    if (proxyOpen) {
      proxyStatus = 'available_not_used';
      return res.status(400).json({
        error: `Proxy is available on port ${proxyPort} but not enabled. Enable it in settings to use.`,
        proxyStatus: 'available_not_used',
        proxyPort
      });
    }
  }
  
  try {
    let cmd;
    if (useProxy && proxyStatus === 'connected') {
      if (proxyUser && proxyPass) {
        cmd = `git clone -c http.proxy=http://${proxyUser}:${proxyPass}@${proxyAddress}:${proxyPort} -c https.proxy=http://${proxyUser}:${proxyPass}@${proxyAddress}:${proxyPort} "${url}" "${targetPath}"`;
      } else {
        cmd = `git clone -c http.proxy=http://${proxyAddress}:${proxyPort} -c https.proxy=http://${proxyAddress}:${proxyPort} "${url}" "${targetPath}"`;
      }
    } else {
      cmd = `git clone "${url}" "${targetPath}"`;
    }
    
    await runCommand(cmd, targetDir);
    res.json({ success: true, path: targetPath, proxyStatus });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/compress/zip-base64', async (req, res) => {
  const { sourceFolder, outputFolder } = req.body;
  
  if (!sourceFolder || !fs.existsSync(sourceFolder)) {
    return res.status(400).json({ error: 'Invalid source folder' });
  }
  
  const outDir = outputFolder || getFolder('compress');
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  
  const folderName = path.basename(sourceFolder);
  const tempZip = path.join(os.tmpdir(), `${folderName}_${generateId()}.zip`);
  
  try {
    const excludeArgs = EXCLUDE_PATTERNS.flatMap(p => 
      p.startsWith('*') ? [`-x!${p.slice(1)}`] : [`-x!${p}*`, `-x!${p}\\`]
    );
    
    const cmd = `"${get7zPath()}" a -r -tzip "${tempZip}" "${sourceFolder}\\*" ${excludeArgs.join(' ')}`;
    await runCommand(cmd);
    
    if (!fs.existsSync(tempZip)) {
      throw new Error('Failed to create ZIP');
    }
    
    const zipContent = fs.readFileSync(tempZip);
    const base64Content = zipContent.toString('base64');
    const sizeKB = Math.ceil(zipContent.length / 1024);
    
    const outputFileName = `BS64_${sizeKB}K_${folderName}.txt`;
    const outputPath = path.join(outDir, outputFileName);
    
    fs.writeFileSync(outputPath, base64Content);
    fs.unlinkSync(tempZip);
    
    res.json({ success: true, outputPath });
  } catch (error) {
    if (fs.existsSync(tempZip)) fs.unlinkSync(tempZip);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/compress/txt', async (req, res) => {
  const { sourceFolder, outputFolder } = req.body;
  
  if (!sourceFolder || !fs.existsSync(sourceFolder)) {
    return res.status(400).json({ error: 'Invalid source folder' });
  }
  
  const outDir = outputFolder || getFolder('compress');
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  
  const folderName = path.basename(sourceFolder);
  const outputPath = path.join(outDir, `${folderName}.txt`);
  
  let fileCount = 0;
  let skipCount = 0;
  
  try {
    const writeStream = fs.createWriteStream(outputPath, { encoding: 'utf-8' });
    writeStream.write(`===MERGE_INFO:folder=${folderName}===\n`);
    
    function walkDir(dir) {
      const items = fs.readdirSync(dir, { withFileTypes: true });
      const dirs = items.filter(i => i.isDirectory()).map(i => i.name).sort();
      const files = items.filter(i => i.isFile()).map(i => i.name).sort();
      
      for (const d of dirs) {
        if (!shouldExclude(d)) {
          walkDir(path.join(dir, d));
        }
      }
      
      for (const f of files) {
        const filePath = path.join(dir, f);
        if (shouldExclude(filePath)) {
          skipCount++;
          continue;
        }
        
        const relPath = path.relative(sourceFolder, filePath);
        writeStream.write(`\n===FILE:${relPath}===\n`);
        
        try {
          const content = fs.readFileSync(filePath, 'utf-8');
          writeStream.write(content);
        } catch (e) {
          writeStream.write('[Binary file or read error]');
        }
        
        writeStream.write('\n===END===\n');
        fileCount++;
      }
    }
    
    walkDir(sourceFolder);
    writeStream.end();
    
    await new Promise(resolve => writeStream.on('finish', resolve));
    
    const stats = fs.statSync(outputPath);
    const sizeKB = Math.ceil(stats.size / 1024);
    
    const finalName = `MERGE_${sizeKB}K_${folderName}.txt`;
    const finalPath = path.join(outDir, finalName);
    
    fs.renameSync(outputPath, finalPath);
    
    res.json({ success: true, outputPath: finalPath, fileCount, skipCount });
  } catch (error) {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/extract/zip-base64', async (req, res) => {
  const { inputFile, outputFolder } = req.body;

  if (!inputFile || !fs.existsSync(inputFile)) {
    return res.status(400).json({ error: 'Invalid input file' });
  }

  const baseOutDir = outputFolder || getFolder('extract');
  if (!fs.existsSync(baseOutDir)) {
    fs.mkdirSync(baseOutDir, { recursive: true });
  }

  // Get filename (without extension) as subfolder name
  const fileName = path.basename(inputFile, path.extname(inputFile));
  const outDir = path.join(baseOutDir, fileName);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  try {
    const base64Content = fs.readFileSync(inputFile, 'utf-8');
    const zipBuffer = Buffer.from(base64Content, 'base64');

    const tempZip = path.join(os.tmpdir(), `extract_${generateId()}.zip`);
    fs.writeFileSync(tempZip, zipBuffer);

    await runCommand(`"${get7zPath()}" x -y -o"${outDir}" "${tempZip}"`);

    fs.unlinkSync(tempZip);

    res.json({ success: true, outputPath: outDir });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/extract/txt', async (req, res) => {
  const { inputFile, outputFolder } = req.body;

  if (!inputFile || !fs.existsSync(inputFile)) {
    return res.status(400).json({ error: 'Invalid input file' });
  }

  const baseOutDir = outputFolder || getFolder('extract');
  if (!fs.existsSync(baseOutDir)) {
    fs.mkdirSync(baseOutDir, { recursive: true });
  }

  // Get filename (without extension) as subfolder name
  const fileName = path.basename(inputFile, path.extname(inputFile));
  const outDir = path.join(baseOutDir, fileName);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  try {
    const content = fs.readFileSync(inputFile, 'utf-8');
    const lines = content.split('\n');

    let currentFile = null;
    let currentContent = [];
    let inContent = false;
    let fileCount = 0;

    for (const line of lines) {
      if (line.startsWith('===MERGE_INFO:')) continue;

      if (line.startsWith('===FILE:')) {
        if (currentFile) {
          // Replace backslashes with forward slashes to avoid Windows path issues
          const normalizedFile = currentFile.replace(/\\/g, '/');
          const fullPath = path.join(outDir, normalizedFile);
          fs.mkdirSync(path.dirname(fullPath), { recursive: true });
          fs.writeFileSync(fullPath, currentContent.join('\n'));
          fileCount++;
        }
        // Remove prefix ===FILE: and suffix ===
        currentFile = line.slice(8).replace(/===$/, '').trim();
        currentContent = [];
        inContent = true;
      } else if (line === '===END===') {
        if (currentFile) {
          // Replace backslashes with forward slashes to avoid Windows path issues
          const normalizedFile = currentFile.replace(/\\/g, '/');
          const fullPath = path.join(outDir, normalizedFile);
          fs.mkdirSync(path.dirname(fullPath), { recursive: true });
          fs.writeFileSync(fullPath, currentContent.join('\n'));
          fileCount++;
          currentFile = null;
          currentContent = [];
          inContent = false;
        }
      } else if (inContent && currentFile) {
        currentContent.push(line);
      }
    }

    if (currentFile) {
      // Replace backslashes with forward slashes to avoid Windows path issues
      const normalizedFile = currentFile.replace(/\\/g, '/');
      const fullPath = path.join(outDir, normalizedFile);
      fs.mkdirSync(path.dirname(fullPath), { recursive: true });
      fs.writeFileSync(fullPath, currentContent.join('\n'));
      fileCount++;
    }

    res.json({ success: true, outputPath: outDir, fileCount });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/github/download-file', async (req, res) => {
  const { url } = req.body;
  const config = loadConfig();
  
  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }
  
  let rawUrl = url;
  if (url.includes('github.com') && !url.includes('raw.githubusercontent.com')) {
    rawUrl = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/');
  }
  
  const downloadDir = getFolder('download');
  if (!fs.existsSync(downloadDir)) {
    fs.mkdirSync(downloadDir, { recursive: true });
  }
  
  const fileName = rawUrl.split('/').pop() || 'download';
  const filePath = path.join(downloadDir, fileName);
  
  const proxyPort = config.download_proxy_port || 10808;
  const proxyAddress = config.download_proxy_address || '127.0.0.1';
  const proxyUser = config.download_proxy_user || '';
  const proxyPass = config.download_proxy_pass || '';
  const useProxy = config.download_proxy_enabled;
  
  try {
    let curlCmd;
    if (useProxy) {
      const proxyOpen = await checkProxy(proxyPort);
      if (!proxyOpen) {
        return res.status(400).json({ 
          error: `Proxy port ${proxyPort} is not open. Please start your download proxy server.`,
          proxyPort
        });
      }
      
      if (proxyUser && proxyPass) {
        curlCmd = `curl -x http://${proxyUser}:${proxyPass}@${proxyAddress}:${proxyPort} -L -o "${filePath}" "${rawUrl}"`;
      } else {
        curlCmd = `curl -x http://${proxyAddress}:${proxyPort} -L -o "${filePath}" "${rawUrl}"`;
      }
    } else {
      curlCmd = `curl -L -o "${filePath}" "${rawUrl}"`;
    }
    
    await runCommand(curlCmd);
    
    if (fs.existsSync(filePath)) {
      res.json({ success: true, path: filePath, fileName });
    } else {
      res.status(500).json({ error: 'Download failed' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`DevToolkit running at http://localhost:${PORT}`);

  // Auto open browser
  const url = `http://localhost:${PORT}`;
  const start = (process.platform === 'win32') ? 'start' : 'open';
  execSync(`${start} ${url}`, { stdio: 'ignore', windowsHide: true });
});
