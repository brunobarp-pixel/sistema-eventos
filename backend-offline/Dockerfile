FROM php:8.2-fpm-alpine

# Instalar extensões PHP necessárias
RUN apk add --no-cache \
    mysql-client \
    zip \
    unzip \
    git \
    curl

# Instalar extensões PHP
RUN docker-php-ext-install pdo pdo_mysql

# Instalar Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Definir diretório de trabalho
WORKDIR /var/www/html

# Copiar composer.json primeiro para melhor cache do Docker
COPY composer.json ./

# Instalar dependências
RUN composer install --no-dev --optimize-autoloader --no-scripts

# Copiar resto dos arquivos da aplicação
COPY . .

# Criar diretórios necessários se não existirem
RUN mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views storage/logs storage/app

# Executar scripts do composer agora que todos os arquivos estão presentes
RUN composer dump-autoload --optimize

# Copiar .env se não existir
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Tornar artisan executável
RUN chmod +x artisan

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