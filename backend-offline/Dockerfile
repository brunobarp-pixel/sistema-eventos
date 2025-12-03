FROM php:8.2-fpm-alpine

# Instalar extensões PHP necessárias
RUN apk add --no-cache \
    mysql-client \
    zip \
    unzip \
    git \
    curl \
    nginx

# Instalar extensões PHP
RUN docker-php-ext-install pdo pdo_mysql

# Instalar Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Definir diretório de trabalho
WORKDIR /var/www/html

# Copiar arquivos da aplicação
COPY . .

# Instalar dependências
RUN composer install --no-dev --optimize-autoloader

# Copiar .env se não existir
RUN if [ ! -f .env ]; then cp .env.example .env; fi

# Gerar chave da aplicação
RUN php artisan key:generate

# Definir permissões
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html

# Expor porta
EXPOSE 8081

# Comando para iniciar a aplicação
CMD ["php", "artisan", "serve", "--host=0.0.0.0", "--port=8081"]