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
    
    const batchPath = path.join(process.resourcesPath, 'start-backend.bat');
    
    if (require('fs').existsSync(batchPath)) {
      console.log('Ejecutando script optimizado de backend...');
      
      // Ejecutar el script en segundo plano, detached y sin bloquear la aplicación
      backendProcess = spawn('cmd', ['/c', batchPath], {
        cwd: process.resourcesPath,
        stdio: ['ignore', 'ignore', 'ignore'], // Ignorar toda la salida para no bloquear
        detached: true, // Ejecutar independientemente
        windowsHide: true
      });
      
      // Desasociar para que no bloquee el cierre de la aplicación
      backendProcess.unref();
      
      console.log('Script de backend ejecutado en segundo plano');
      
    } else {
      console.error('Script de backend no encontrado:', batchPath);
    }
    
  } catch (error) {
    console.error('Error al iniciar backend:', error);
  }
}
    }
    
    // Configurar listeners comunes
    if (backendProcess) {
      backendProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
      });
      
      backendProcess.stderr.on('data', (data) => {
        console.log(`Backend stderr: ${data}`);
      });
      
      backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
        backendProcess = null;
      });
      
      backendProcess.on('error', (error) => {
        console.error('Backend process error:', error);
        
        // Mostrar mensaje al usuario
        const { dialog } = require('electron');
        dialog.showErrorBox(
          'Error del Backend',
          `No se pudo iniciar el backend de Calyx AI.\n\nError: ${error.message}\n\nPor favor asegúrate de tener Python 3.9+ instalado.`
        );
      });
    }
    
  } catch (error) {
    console.error('Error general al iniciar el backend:', error);
    
    // Mostrar mensaje de error al usuario
    const { dialog } = require('electron');
    dialog.showErrorBox(
      'Error de Inicialización',
      `Error al inicializar Calyx AI: ${error.message}\n\nPor favor reinstala la aplicación o contacta soporte.`
    );
  }
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
    console.log('Backend detenido');
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
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
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});
