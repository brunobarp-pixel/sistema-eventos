FROM php:8.4-fpm-alpine

# Instalar extensões PHP necessárias
RUN apk add --no-cache \
    mysql-client \
    zip \
    unzip \
    git \
    curl \
    libzip-dev

# Instalar extensões PHP
RUN docker-php-ext-install pdo pdo_mysql zip

# Instalar Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Definir diretório de trabalho
WORKDIR /var/www/html

# Copiar arquivos de configuração do Composer primeiro
COPY composer.json composer.lock* ./

# Instalar dependências do Composer
RUN composer install --no-dev --optimize-autoloader --no-scripts --no-autoloader

# Copiar resto dos arquivos da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p storage/framework/cache \
    storage/framework/sessions \
    storage/framework/views \
    storage/logs \
    storage/app \
    bootstrap/cache

# Finalizar instalação do Composer
RUN composer dump-autoload --optimize

# Tornar artisan executável
RUN chmod +x artisan

# Copiar .env se não existir
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Gerar chave da aplicação
RUN php artisan key:generate

# Definir permissões
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html
RUN chmod -R 775 storage bootstrap/cache

# Expor porta
EXPOSE 8081

# Comando para iniciar a aplicação
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8081"]