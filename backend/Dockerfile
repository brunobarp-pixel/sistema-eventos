FROM php:8.2-apache

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzip-dev \
    git \
    curl \
    wget \
    nano \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Instalar apenas extensões que não vêm por padrão
RUN docker-php-ext-install -j$(nproc) \
    pdo_mysql \
    zip \
    bcmath

# Instalar Redis extension
RUN pecl install redis && docker-php-ext-enable redis

# Habilitar mod_rewrite para Laravel
RUN a2enmod rewrite

# Instalar Composer
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Configurar Apache
RUN echo '<VirtualHost *:80>' > /etc/apache2/sites-available/000-default.conf && \
    echo '    DocumentRoot /app/public' >> /etc/apache2/sites-available/000-default.conf && \
    echo '    <Directory /app/public>' >> /etc/apache2/sites-available/000-default.conf && \
    echo '        AllowOverride All' >> /etc/apache2/sites-available/000-default.conf && \
    echo '        Require all granted' >> /etc/apache2/sites-available/000-default.conf && \
    echo '    </Directory>' >> /etc/apache2/sites-available/000-default.conf && \
    echo '</VirtualHost>' >> /etc/apache2/sites-available/000-default.conf

# Configurar PHP
RUN echo 'memory_limit = 256M' >> /usr/local/etc/php/conf.d/laravel.ini && \
    echo 'max_execution_time = 60' >> /usr/local/etc/php/conf.d/laravel.ini && \
    echo 'upload_max_filesize = 100M' >> /usr/local/etc/php/conf.d/laravel.ini && \
    echo 'post_max_size = 100M' >> /usr/local/etc/php/conf.d/laravel.ini

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos do projeto (incluindo ocultos)
COPY --chown=www-data:www-data . .

# Copiar .env.example como .env
RUN cp .env.example .env && chmod 644 .env

# Definir permissões
RUN chmod -R 775 /app/storage /app/bootstrap/cache

# Instalar dependências do Composer
RUN composer install --no-dev --optimize-autoloader

# Exposar porta
EXPOSE 80

# Script de inicialização
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Iniciar com script personalizado
ENTRYPOINT ["docker-entrypoint.sh"]
