const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let backendProcess = null;

function startBackend() {
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  
  if (isDev) {
    console.log('Modo desarrollo: Backend debe ejecutarse manualmente');
    return;
  }
  
  try {
    console.log('Iniciando backend en modo producción...');
    
    // TEMPORALMENTE: Usar batch script con ventana visible para diagnóstico
    const batchPath = path.join(process.resourcesPath, 'start-backend.bat');
    
    if (require('fs').existsSync(batchPath)) {
      console.log('Ejecutando script batch VISIBLE para diagnóstico...');
      
      // FORZAR ventana visible - usar START para crear nueva ventana CMD con comillas para rutas con espacios
      backendProcess = spawn('cmd', ['/c', 'start', 'cmd', '/k', `"${batchPath}"`], {
        cwd: process.resourcesPath,
        stdio: 'ignore',
        detached: true,
        shell: true
      });
      
      console.log('Script de backend ejecutado con ventana CMD FORZADA para diagnóstico');
      
    } else {
      console.error('Script batch de backend no encontrado:', batchPath);
      
      // Fallback: usar VBScript si el batch no existe
      const vbsPath = path.join(process.resourcesPath, 'start-backend.vbs');
      if (require('fs').existsSync(vbsPath)) {
        console.log('Usando VBScript como fallback...');
        backendProcess = spawn('cscript', ['/nologo', vbsPath], {
          cwd: process.resourcesPath,
          stdio: ['ignore', 'ignore', 'ignore'],
          detached: true,
          windowsHide: true
        });
        backendProcess.unref();
      }
    }
    
  } catch (error) {
    console.error('Error al iniciar backend:', error);
  }
}

function stopBackend() {
  if (backendProcess) {
    try {
      backendProcess.kill();
      backendProcess = null;
      console.log('Backend detenido');
    } catch (error) {
      console.log('Error al detener backend:', error);
    }
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    icon: path.join(__dirname, '../public/icon.ico'), // Icono para la ventana de la aplicación
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true,
      contextIsolation: false,
    },
    show: false
  });
  
  // Determinar si estamos en desarrollo o producción
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  
  if (isDev) {
    win.loadURL('http://localhost:5173');
    win.webContents.openDevTools(); // Abrir DevTools en desarrollo
  } else {
    // En producción, cargar el archivo HTML estático
    win.loadFile(path.join(__dirname, '../dist/index.html'));
  }
  
  win.once('ready-to-show', () => win.show());
  
  return win;
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
