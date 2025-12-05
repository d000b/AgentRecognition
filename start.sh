#!/bin/bash
# start.sh - Linux/Mac version

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}"
    echo "========================================"
    echo "   AGENT RECOGNITION SYSTEM MANAGER"
    echo "========================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

print_info() {
    echo -e "${YELLOW}$1${NC}"
}

# Парсинг аргументов
BUILD=false
NO_CACHE=false
LOGS=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --logs)
            LOGS=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_header

# Проверка Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    exit 1
fi

# Очистка
if [ "$CLEAN" = true ]; then
    print_info "Cleaning up old containers..."
    docker-compose down -v
    rm -rf ./logs 2>/dev/null || true
    print_success "Cleanup completed"
    exit 0
fi

# Проверка директорий
print_info "Checking host directories..."

# Для Linux/Mac пути будут другие
# Вам нужно будет изменить эти пути под свою систему
MODEL_PATH="$HOME/models/Qwen3-VL-OMNI"
STORAGE_PATH="$HOME/storage/AgentRecognition"

mkdir -p "$STORAGE_PATH"/{uploads,processed,temp,logs,database,redis_data,postgres_data,huggingface_cache,postgres_backups}

# Проверка модели
if [ ! -d "$MODEL_PATH" ]; then
    print_error "Model directory not found: $MODEL_PATH"
    print_info "Please download the model or update the path in docker-compose.yml"
    exit 1
fi

MODEL_FILES=$(find "$MODEL_PATH" -name "*.safetensors" | wc -l)
print_info "Found $MODEL_FILES model files"

# Проверка GPU
print_info "Checking NVIDIA GPU..."
if docker run --rm --gpus all nvidia/cuda:12.1-base nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null; then
    print_success "GPU detected"
else
    print_info "No GPU detected or Docker GPU support not configured"
fi

# Сборка
if [ "$BUILD" = true ]; then
    print_info "Building Docker images..."
    BUILD_CMD="docker-compose build"
    if [ "$NO_CACHE" = true ]; then
        BUILD_CMD="$BUILD_CMD --no-cache"
    fi
    $BUILD_CMD
    if [ $? -ne 0 ]; then
        print_error "Build failed!"
        exit 1
    fi
    print_success "Build completed"
fi

# Запуск
print_info "Starting containers..."
docker-compose up -d

if [ $? -ne 0 ]; then
    print_error "Failed to start containers!"
    exit 1
fi

# Ожидание
print_info "Waiting for services to start..."
sleep 10

# Статус
print_info "Checking service status..."
docker-compose ps

# Логи
if [ "$LOGS" = true ]; then
    print_info "Showing logs..."
    docker-compose logs -f
    exit 0
fi

# Вывод информации
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}          SERVICES RUNNING${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${CYAN}🌐 API Server:    http://localhost:8000${NC}"
echo -e "${CYAN}📚 API Docs:      http://localhost:8000/docs${NC}"
echo -e "${CYAN}💻 Web Interface: http://localhost:8000/web${NC}"
echo -e "${CYAN}❤️  Health Check:  http://localhost:8000/health${NC}"
echo -e "${CYAN}🗄️  Redis:         localhost:6379${NC}"
echo -e "${CYAN}🗃️  PostgreSQL:    localhost:5432${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}          MANAGEMENT COMMANDS${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}📋 View logs:     ./start.sh --logs${NC}"
echo -e "${YELLOW}🔄 Rebuild:       ./start.sh --build${NC}"
echo -e "${YELLOW}🧹 Clean:         ./start.sh --clean${NC}"
echo -e "${YELLOW}📊 Status:        docker-compose ps${NC}"
echo -e "${YELLOW}⏹️  Stop:          docker-compose down${NC}"
echo -e "${YELLOW}🐚 Shell:         docker exec -it agent-recognition-api bash${NC}"
echo ""

# Автоматическое открытие браузера
read -p "Open API documentation in browser? (Y/n): " choice
if [[ "$choice" != "n" && "$choice" != "N" ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:8000/docs"
    elif command -v open &> /dev/null; then
        open "http://localhost:8000/docs"
    fi
fi