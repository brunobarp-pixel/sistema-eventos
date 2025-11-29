"""
Serviço de Autenticação com Laravel API
Gerencia tokens Sanctum automaticamente
"""

import requests
import json
import os
from datetime import datetime, timedelta

LARAVEL_API = 'http://backend-laravel/api'
TOKEN_FILE = 'data/laravel_token.json'

class LaravelAuth:
    def __init__(self):
        self.token = None
        self.token_expiry = None
        self.user_data = None
        self.load_token()
    
    def load_token(self):
        """Carrega token salvo (se existir e não estiver expirado)"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.token_expiry = datetime.fromisoformat(data.get('expiry'))
                    self.user_data = data.get('user')
                    
                    # Verificar se ainda é válido
                    if datetime.now() < self.token_expiry:
                        print(f"✅ Token carregado: {self.user_data.get('email')}")
                        return True
                    else:
                        print("⚠️ Token expirado, novo login necessário")
                        self.token = None
        except Exception as e:
            print(f"⚠️ Erro ao carregar token: {str(e)}")
        
        return False
    
    def save_token(self):
        """Salva token em arquivo"""
        try:
            # Criar pasta data se não existir
            os.makedirs('data', exist_ok=True)
            
            data = {
                'token': self.token,
                'expiry': self.token_expiry.isoformat(),
                'user': self.user_data
            }
            
            with open(TOKEN_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"💾 Token salvo: {self.user_data.get('email')}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar token: {str(e)}")
    
    def login(self, email, senha):
        """Faz login no Laravel e obtém token"""
        try:
            response = requests.post(f'{LARAVEL_API}/auth', json={
                'email': email,
                'senha': senha
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data['data']['token']
                    self.user_data = data['data']['usuario']
                    # Token expira em 24 horas
                    self.token_expiry = datetime.now() + timedelta(hours=24)
                    
                    self.save_token()
                    
                    print(f"✅ Login realizado: {self.user_data['nome']}")
                    return True
            
            print(f"❌ Erro no login: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Erro na conexão: {str(e)}")
            return False
    
    def logout(self):
        """Faz logout e revoga token"""
        try:
            if self.token:
                response = requests.post(
                    f'{LARAVEL_API}/logout',
                    headers=self.get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("✅ Logout realizado")
        except:
            pass
        
        # Limpar dados locais
        self.token = None
        self.user_data = None
        self.token_expiry = None
        
        # Deletar arquivo
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
    
    def get_headers(self):
        """Retorna headers com token de autenticação"""
        if not self.token:
            raise Exception("Não autenticado! Faça login primeiro.")
        
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def is_authenticated(self):
        """Verifica se está autenticado"""
        if not self.token:
            return False
        
        # Verificar se token expirou
        if datetime.now() >= self.token_expiry:
            print("⚠️ Token expirado")
            self.token = None
            return False
        
        return True
    
    def ensure_authenticated(self):
        """Garante que está autenticado (faz login automático se necessário)"""
        if self.is_authenticated():
            return True
        
        # Tentar fazer login automático com credenciais padrão
        # (você pode configurar isso no .env ou pedir credenciais)
        print("⚠️ Não autenticado. Tentando login automático...")
        
        # OPÇÃO 1: Login com usuário padrão do sistema
        return self.login('sistema@eventos.com', 'senha_sistema_2025')
        
        # OPÇÃO 2: Pedir credenciais (descomente se preferir)
        # email = input("Email: ")
        # senha = input("Senha: ")
        # return self.login(email, senha)
    
    def request(self, method, endpoint, **kwargs):
        """
        Faz requisição autenticada para o Laravel
        
        Uso:
            auth.request('GET', '/inscricoes')
            auth.request('POST', '/inscricoes', json={'usuario_id': 1, 'evento_id': 2})
        """
        # Garantir autenticação
        if not self.ensure_authenticated():
            raise Exception("Falha na autenticação")
        
        # Adicionar headers
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self.get_headers())
        
        # Fazer requisição
        url = f"{LARAVEL_API}{endpoint}"
        response = requests.request(method, url, timeout=10, **kwargs)
        
        return response


# ==========================================
# INSTÂNCIA GLOBAL
# ==========================================

laravel_auth = LaravelAuth()


# ==========================================
# FUNÇÕES DE CONVENIÊNCIA
# ==========================================

def laravel_get(endpoint):
    """GET autenticado"""
    return laravel_auth.request('GET', endpoint)

def laravel_post(endpoint, data):
    """POST autenticado"""
    return laravel_auth.request('POST', endpoint, json=data)

def laravel_put(endpoint, data):
    """PUT autenticado"""
    return laravel_auth.request('PUT', endpoint, json=data)

def laravel_delete(endpoint):
    """DELETE autenticado"""
    return laravel_auth.request('DELETE', endpoint)


# ==========================================
# TESTE
# ==========================================

if __name__ == '__main__':
    print("🧪 Testando autenticação Laravel...\n")
    
    # Teste 1: Login
    print("1️⃣ Fazendo login...")
    if laravel_auth.login('alonso@gmail.com', 'senha123'):
        print(f"   ✅ Usuário: {laravel_auth.user_data['nome']}\n")
        
        # Teste 2: Requisição autenticada
        print("2️⃣ Buscando inscrições...")
        try:
            response = laravel_get('/inscricoes')
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {len(data.get('data', []))} inscrições encontradas\n")
            else:
                print(f"   ❌ Erro: {response.status_code}\n")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}\n")
        
        # Teste 3: Verificar dados do usuário
        print("3️⃣ Verificando dados do usuário...")
        try:
            response = laravel_get('/me')
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Dados: {data['data']['nome']}\n")
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}\n")
    
    print("✅ Testes concluídos!")
