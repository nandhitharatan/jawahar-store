const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

let mainWindow;
let flaskProcess;
const FLASK_PORT = 5000;
const FLASK_URL = `http://127.0.0.1:${FLASK_PORT}`;

// ── Start Flask Backend ────────────────────────────────────────────────────────
function startFlask() {
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
  const backendDir = path.join(__dirname, '..', 'backend');
  const scriptPath = path.join(backendDir, 'run.py');

  flaskProcess = spawn(pythonPath, [scriptPath], {
    cwd: backendDir,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
  });

  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`);
  });
  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask ERR: ${data}`);
  });
  flaskProcess.on('close', (code) => {
    console.log(`Flask exited: ${code}`);
  });
}

// ── Wait for Flask to be ready ────────────────────────────────────────────────
function waitForFlask(callback, retries = 30, delay = 500) {
  http.get(FLASK_URL, (res) => {
    callback();
  }).on('error', () => {
    if (retries > 0) {
      setTimeout(() => waitForFlask(callback, retries - 1, delay), delay);
    } else {
      console.error('Flask failed to start. Giving up.');
      callback(); // open anyway
    }
  });
}

// ── Create Window ─────────────────────────────────────────────────────────────
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'Jawahar Enterprises – Store Management',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'static', 'images', 'icon.png'),
    show: false,
  });

  // Load loading screen first
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));

  waitForFlask(() => {
    mainWindow.loadURL(FLASK_URL);
    mainWindow.show();
  });

  // Open external links in browser, not in-app
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  startFlask();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (flaskProcess) flaskProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (flaskProcess) flaskProcess.kill();
});
