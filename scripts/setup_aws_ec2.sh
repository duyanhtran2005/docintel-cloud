#!/bin/bash
# ==============================================================================
# DocIntel-Cloud: Automatic Setup Script for AWS EC2 (Ubuntu 24.04 LTS - 0 USD)
# ==============================================================================
set -e

echo "🚀 Bắt đầu cấu hình tự động cho máy chủ AWS EC2 Ubuntu..."

# 1. Cập nhật hệ điều hành
echo "📦 Cập nhật gói hệ thống apt..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Cài đặt các công cụ cơ bản
sudo apt-get install -y curl git ca-certificates gnupg lsb-release

# 3. Cài đặt Docker Engine & Docker Compose Plugin
echo "🐳 Đang cài đặt Docker Engine và Docker Compose..."
if ! command -v docker &> /dev/null; then
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Phân quyền cho user ubuntu chạy docker không cần sudo
    sudo usermod -aG docker $USER
    echo "✅ Đã cài đặt Docker thành công!"
else
    echo "✅ Docker đã được cài đặt từ trước."
fi

# 4. Kiểm tra phiên bản Docker Compose
docker compose version

echo "======================================================================"
echo "🎉 HOÀN THÀNH THIẾT LẬP HẠ TẦNG DOCKER TRÊN AWS EC2!"
echo "👉 Anh hãy đăng xuất SSH và đăng nhập lại để quyền 'docker' có hiệu lực."
echo "👉 Tiếp theo chạy: docker compose up -d --build"
echo "======================================================================"
