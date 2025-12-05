# start.ps1
param(
    [switch]$Build = $false,
    [switch]$NoCache = $false,
    [switch]$Force = $false,
    [switch]$Logs = $false,
    [switch]$Clean = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AGENT RECOGNITION SYSTEM MANAGER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Проверка Docker
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker is not installed or not running!" -ForegroundColor Red
    exit 1
}

# Очистка (если указан флаг)
if ($Clean) {
    Write-Host "🧹 Cleaning up old containers..." -ForegroundColor Yellow
    docker-compose down -v
    Remove-Item -Path ".\logs" -Recurse -ErrorAction SilentlyContinue
    Write-Host "✅ Cleanup completed" -ForegroundColor Green
    exit 0
}

# Проверка и создание директорий на хосте
Write-Host "📁 Creating host directories..." -ForegroundColor Yellow

$directories = @(
    "D:\storage\AgentRecognition\uploads",
    "D:\storage\AgentRecognition\processed", 
    "D:\storage\AgentRecognition\temp",
    "D:\storage\AgentRecognition\logs",
    "D:\storage\AgentRecognition\database",
    "D:\storage\AgentRecognition\redis_data",
    "D:\storage\AgentRecognition\postgres_data",
    "D:\storage\AgentRecognition\huggingface_cache",
    "D:\storage\AgentRecognition\postgres_backups"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Created: $dir" -ForegroundColor Green
    }
}

# Проверка существования модели
$modelPath = "E:\LLM\Qwen3-VL-OMNI"
if (!(Test-Path $modelPath)) {
    Write-Host "❌ Model directory not found: $modelPath" -ForegroundColor Red
    Write-Host "Please download the model to: E:\LLM\Qwen3-VL-OMNI" -ForegroundColor Yellow
    exit 1
}

# Подсчет файлов модели
$modelFiles = Get-ChildItem -Path $modelPath -Filter *.safetensors
Write-Host "📦 Found $($modelFiles.Count) model files" -ForegroundColor Green

# Проверка GPU
Write-Host "🔍 Checking NVIDIA GPU..." -ForegroundColor Yellow
$gpuInfo = docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ GPU detected: $gpuInfo" -ForegroundColor Green
} else {
    Write-Host "⚠️  No GPU detected or Docker GPU support not configured" -ForegroundColor Yellow
}

# Сборка (если указан флаг)
if ($Build) {
    Write-Host "🏗️  Building Docker images..." -ForegroundColor Yellow
    $buildArgs = @("build")
    if ($NoCache) { $buildArgs += "--no-cache" }
    $buildArgs += "--pull"
    
    docker-compose $buildArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Build completed" -ForegroundColor Green
}

# Запуск контейнеров
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start containers!" -ForegroundColor Red
    exit 1
}

# Ожидание запуска
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверка статуса
Write-Host "📊 Checking service status..." -ForegroundColor Yellow
docker-compose ps

# Логи (если указан флаг)
if ($Logs) {
    Write-Host "📋 Showing logs..." -ForegroundColor Yellow
    docker-compose logs -f
    exit 0
}

# Вывод информации
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "          SERVICES RUNNING" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "🌐 API Server:    http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs:      http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "💻 Web Interface: http://localhost:8000/web" -ForegroundColor Cyan
Write-Host "❤️  Health Check:  http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🗄️  Redis:         localhost:6379" -ForegroundColor Cyan
Write-Host "🗃️  PostgreSQL:    localhost:5432" -ForegroundColor Cyan
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "          MANAGEMENT COMMANDS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "📋 View logs:     .\start.ps1 -Logs" -ForegroundColor Yellow
Write-Host "🔄 Rebuild:       .\start.ps1 -Build" -ForegroundColor Yellow
Write-Host "🧹 Clean:         .\start.ps1 -Clean" -ForegroundColor Yellow
Write-Host "📊 Status:        docker-compose ps" -ForegroundColor Yellow
Write-Host "⏹️  Stop:          docker-compose down" -ForegroundColor Yellow
Write-Host "🐚 Shell:         docker exec -it agent-recognition-api bash" -ForegroundColor Yellow
Write-Host ""

# Автоматическое открытие браузера
$choice = Read-Host "Open API documentation in browser? (Y/n)"
if ($choice -ne "n" -and $choice -ne "N") {
    Start-Process "http://localhost:8000/docs"
}