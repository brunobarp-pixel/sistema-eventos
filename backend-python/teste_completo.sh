#!/bin/bash

echo "🧪 TESTANDO SISTEMA..."

# 1. Status
echo -e "\n1️⃣ Laravel Status:"
curl -s http://127.0.0.1:8000/api/status | jq

echo -e "\n2️⃣ Python Status:"
curl -s http://127.0.0.1:5000/status | jq

# 2. Login
echo -e "\n3️⃣ Fazendo login..."
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth \
  -H "Content-Type: application/json" \
  -d '{"email":"sistema@eventos.com","senha":"senha_sistema_2025"}' \
  | jq -r '.data.token')

echo "Token: $TOKEN"

# 3. Buscar inscrições (com autenticação)
echo -e "\n4️⃣ Buscando inscrições:"
curl -s http://127.0.0.1:8000/api/inscricoes \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n✅ Testes concluídos!"
