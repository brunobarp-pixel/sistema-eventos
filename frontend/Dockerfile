# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci

COPY . .

# Build da aplicação (se necessário)
RUN npm run build 2>/dev/null || echo "Nenhuma build configurada"

# Stage 2: Production
FROM nginx:alpine

# Copiar configuração nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Copiar arquivos estáticos
COPY --from=builder /app /usr/share/nginx/html

# Criar diretório de cache
RUN mkdir -p /var/cache/nginx

# Definir permissões
RUN chown -R nginx:nginx /usr/share/nginx/html

# Expor porta
EXPOSE 80 443

# Iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
