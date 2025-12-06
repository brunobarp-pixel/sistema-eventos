const API_BASE_URL = 'http://localhost:8000/api'; 

/**
 * Função principal para lidar com o envio do formulário de login.
 * @param {Event} event - O evento de submissão do formulário.
 */
function handleLoginSubmit(event) {
    event.preventDefault(); 
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.textContent = ''; 
    
    const loginData = {
        email: email,
        password: password
    };
    
    fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(loginData) 
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Falha na autenticação. Verifique suas credenciais.');
        }
        return response.json(); 
    })
    .then(data => {

        const token = data.token; 
        
        if (token) {
            localStorage.setItem('authToken', token);
            
            window.location.href = 'eventos.html'; 
            
        } else {
            errorMessage.textContent = 'Login bem-sucedido, mas o token não foi recebido.';
        }
    })
    .catch(error => {
        console.error('Erro de Login:', error.message);
        errorMessage.textContent = error.message;
    });
}


/**
 * Função para buscar o token armazenado.
 * @returns {string | null} O token de autenticação ou null.
 */
function getAuthToken() {
    return localStorage.getItem('authToken');
}

/**
 * Exemplo de como fazer uma requisição (GET) autenticada
 * @param {string} endpoint - O endpoint da API
 * @returns {Promise<Object>} A Promise com dados da resposta
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
            'Authorization': `Bearer ${token}` 
        }
    });

    if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
            localStorage.removeItem('authToken'); 
            window.location.href = 'login.html'; 
        }
        throw new Error(`Erro na requisição: ${response.statusText}`);
    }

    return response.json();
}