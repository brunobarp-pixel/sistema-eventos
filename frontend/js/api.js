// Constante para a URL base da sua API
// *IMPORTANTE: Altere esta URL se o seu backend estiver em um local diferente.*
const API_BASE_URL = 'http://177.44.248.118:8000/api';

/**
 * Função principal para lidar com o envio do formulário de login.
 * @param {Event} event - O evento de submissão do formulário.
 */
function handleLoginSubmit(event) {
    // Impede o comportamento padrão de recarregar a página
    event.preventDefault(); 
    
    // 1. Coletar dados do formulário
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');

    // Limpa mensagens de erro anteriores
    errorMessage.textContent = ''; 
    
    // 2. Montar o objeto de dados
    const loginData = {
        email: email,
        password: password
    };
    
    // 3. Fazer a chamada para a API
    fetch(`${API_BASE_URL}/login-laravel`, {
        method: 'POST', // Método POST para envio de credenciais
        headers: {
            'Content-Type': 'application/json' // Informa que estamos enviando JSON
        },
        body: JSON.stringify(loginData) // Converte o objeto JS para JSON string
    })
    .then(response => {
        // Verifica se a resposta foi bem-sucedida (status 200-299)
        if (!response.ok) {
            // Se for erro (ex: 401 Unauthorized), lança um erro para o bloco .catch
            throw new Error('Falha na autenticação. Verifique suas credenciais.');
        }
        return response.json(); // Converte a resposta JSON para objeto JS
    })
    .then(data => {
        // 4. Se o login foi um sucesso
        // **ESTE É O PASSO MAIS IMPORTANTE: ARMAZENAR O TOKEN**
        
        // Assumindo que o Laravel retorna o token em data.token
        const token = data.token; 
        
        if (token) {
            // Salva o token no armazenamento local (localStorage) para uso futuro
            localStorage.setItem('authToken', token);
            console.log('Login bem-sucedido! Token armazenado.');
            
            // 5. Redirecionar para a página principal (ex: eventos.html)
            window.location.href = 'eventos.html'; 
            
        } else {
            // Caso a API retorne sucesso, mas o token esteja faltando
            errorMessage.textContent = 'Login bem-sucedido, mas o token não foi recebido.';
        }
    })
    .catch(error => {
        // 6. Tratar erros de rede ou de autenticação (401)
        console.error('Erro de Login:', error.message);
        errorMessage.textContent = error.message;
    });
}

// -----------------------------------------------------------
// **Função de utilidade para requisições autenticadas**
// Você usará esta função para o EventoController, InscricaoController, etc.
// -----------------------------------------------------------

/**
 * Função para buscar o token armazenado.
 * @returns {string | null} O token de autenticação ou null.
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Exemplo de como fazer uma requisição (GET) autenticada
 * @param {string} endpoint - O endpoint da API (ex: '/eventos').
 * @returns {Promise<Object>} A Promise com os dados da resposta.
 */
async function fetchAuthenticated(endpoint) {
    const token = getAuthToken();
    if (!token) {
        console.error('Usuário não autenticado. Redirecionando para login.');
        window.location.href = 'login.html';
        return;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            // **ENVIO DO TOKEN NO HEADER "Authorization"**
            'Authorization': `Bearer ${token}` 
        }
    });

    if (!response.ok) {
        // Trata a expiração do token ou erro de permissão
        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('authToken'); // Limpa o token inválido
            window.location.href = 'login.html'; // Redireciona para o login
        }
        throw new Error(`Erro na requisição: ${response.statusText}`);
    }

    return response.json();
}
