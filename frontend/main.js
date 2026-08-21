const { app, BrowserWindow, shell, dialog } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const http = require('http');

let mainWindow;
let flaskProcess;
const FLASK_PORT = 5000;
const FLASK_URL = `http://127.0.0.1:${FLASK_PORT}`;

// ── Start Flask Backend ────────────────────────────────────────────────────────
function startFlask() {
  const userDataPath = app.getPath('userData');
  const env = { ...process.env, JAWAHAR_STORE_DATA_DIR: userDataPath };

  if (app.isPackaged) {
    // In packaged app: spawn compiled backend.exe from resourcesPath
    const backendExe = path.join(process.resourcesPath, 'backend.exe');
    console.log(`Launching packaged backend: ${backendExe}`);

    flaskProcess = spawn(backendExe, [], {
      cwd: process.resourcesPath,
      env: env,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
  } else {
    // In dev mode: spawn python run.py
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    const backendDir = path.join(__dirname, '..', 'backend');
    const scriptPath = path.join(backendDir, 'run.py');
    console.log(`Launching dev backend script: ${scriptPath}`);

    flaskProcess = spawn(pythonPath, [scriptPath], {
      cwd: backendDir,
      env: env,
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    });
  }

  flaskProcess.stdout.on('data', (data) => {
    console.log(`Flask: ${data}`);
  });
  flaskProcess.stderr.on('data', (data) => {
    console.error(`Flask ERR: ${data}`);
  });
  flaskProcess.on('close', (code) => {
    console.log(`Flask process exited with code ${code}`);
  });
  flaskProcess.on('error', (err) => {
    console.error('Failed to spawn Flask backend process:', err);
  });
}

// ── Wait for Flask Server ─────────────────────────────────────────────────────
function waitForFlask(callback, onError, retries = 40, delay = 500) {
  http.get(FLASK_URL, (res) => {
    callback();
  }).on('error', () => {
    if (retries > 0) {
      setTimeout(() => waitForFlask(callback, onError, retries - 1, delay), delay);
    } else {
      console.error('Flask server failed to start within retry limit.');
      onError();
    }
  });
}

// ── Kill Backend Process ──────────────────────────────────────────────────────
function stopFlask() {
  if (flaskProcess) {
    const pid = flaskProcess.pid;
    if (process.platform === 'win32' && pid) {
      exec(`taskkill /pid ${pid} /T /F`, (err) => {
        if (err) console.log('Taskkill notice (process may have already terminated):', err.message);
      });
    } else {
      flaskProcess.kill();
    }
    flaskProcess = null;
  }
}

// ── Create Main Window ────────────────────────────────────────────────────────
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
    icon: path.join(__dirname, 'static', 'images', 'icon-512.png'),
    show: false,
  });

  // Display loading splash screen initially
  mainWindow.loadFile(path.join(__dirname, 'loading.html'));
  mainWindow.show();

  waitForFlask(
    () => {
      // Backend is ready, load main app
      mainWindow.loadURL(FLASK_URL);
    },
    () => {
      // Backend startup failure callback
      dialog.showErrorBox(
        'Backend Initialization Error',
        'Failed to start the local store backend server.\n\nPlease verify local file permissions and try restarting the application.'
      );
    }
  );

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ── App Lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  startFlask();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  stopFlask();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopFlask();
});
