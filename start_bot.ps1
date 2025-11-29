# Script para iniciar el bot y el servidor web simultáneamente

Write-Host "🚀 Iniciando CineStelar Bot con servidor de anuncios..." -ForegroundColor Cyan

# Activar entorno virtual
Write-Host "📦 Activando entorno virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Verificar instalación de dependencias
Write-Host "🔍 Verificando dependencias..." -ForegroundColor Yellow
$packages = pip list
if (-not ($packages -like "*flask*")) {
    Write-Host "⚠️  Flask no instalado. Instalando dependencias..." -ForegroundColor Red
    pip install -r requirements.txt
}

# Iniciar servidor Flask en segundo plano
Write-Host "🌐 Iniciando servidor web en puerto 5000..." -ForegroundColor Green
$flaskJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    .\venv\Scripts\Activate.ps1
    python webapp_server.py
}

# Esperar un momento para que Flask inicie
Start-Sleep -Seconds 3

# Iniciar bot de Telegram
Write-Host "🤖 Iniciando bot de Telegram..." -ForegroundColor Green
Write-Host "`n✅ Ambos servicios corriendo:" -ForegroundColor Cyan
Write-Host "   - Bot de Telegram: Activo" -ForegroundColor White
Write-Host "   - Servidor Web: http://localhost:5000" -ForegroundColor White
Write-Host "`n⚠️  IMPORTANTE: Para usar la Mini App necesitas:" -ForegroundColor Yellow
Write-Host "   1. Hosting público (ngrok, Render, Vercel, etc.)" -ForegroundColor White
Write-Host "   2. Actualizar WEBAPP_URL en .env con tu dominio público" -ForegroundColor White
Write-Host "   3. Configurar el dominio en @BotFather con /setdomain" -ForegroundColor White
Write-Host "`n📝 Para detener ambos servicios presiona Ctrl+C" -ForegroundColor Yellow
Write-Host ""

try {
    python main.py
} finally {
    # Detener servidor Flask al cerrar
    Write-Host "`n🛑 Deteniendo servidor web..." -ForegroundColor Red
    Stop-Job $flaskJob
    Remove-Job $flaskJob
}
