#!/bin/bash

# Aguardar o banco estar disponível
echo "Aguardando banco de dados..."
while ! nc -z database 3306; do
  sleep 1
done
echo "Banco de dados disponível!"

# Executar comandos Laravel
echo "Executando composer install..."
composer install --no-dev --optimize-autoloader

echo "Limpando cache..."
php artisan config:clear
php artisan cache:clear
php artisan view:clear
php artisan route:clear

echo "Executando migrações..."
php artisan migrate --force

echo "Criando link para storage..."
rm -f /app/public/storage
php artisan storage:link

echo "Configurando permissões..."
chmod -R 775 /app/storage /app/bootstrap/cache
chown -R www-data:www-data /app/storage /app/bootstrap/cache

echo "Iniciando Apache..."
exec apache2-foreground