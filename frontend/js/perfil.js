// perfil.js - Gerenciamento de perfil do usuário

function adicionarBotaoPerfil() {
    const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
    const token = localStorage.getItem('token');
    
    if (!usuario || !token) return;
    
    // Adicionar botão no navbar
    const navbarNav = document.querySelector('.navbar-nav');
    if (!navbarNav) return;
    
    // Verificar se já existe
    if (document.getElementById('btnPerfil')) return;
    
    const perfilItem = document.createElement('li');
    perfilItem.className = 'nav-item';
    perfilItem.innerHTML = `
        <a class="nav-link" href="#" id="btnPerfil" onclick="abrirModalPerfil(); return false;">
            <i class="bi bi-person-circle"></i> ${usuario.nome}
        </a>
    `;
    
    navbarNav.appendChild(perfilItem);
}

function abrirModalPerfil() {
    const usuario = JSON.parse(localStorage.getItem('usuario') || 'null');
    if (!usuario) return;
    
    // Criar modal se não existir
    if (!document.getElementById('modalPerfil')) {
        criarModalPerfil();
    }
    
    // Preencher campos
    document.getElementById('editNome').value = usuario.nome || '';
    document.getElementById('editEmail').value = usuario.email || '';
    document.getElementById('editCpf').value = usuario.cpf || '';
    document.getElementById('editTelefone').value = usuario.telefone || '';
    document.getElementById('editSenha').value = '';
    
    // Abrir modal
    const modal = new bootstrap.Modal(document.getElementById('modalPerfil'));
    modal.show();
}

function criarModalPerfil() {
    const modalHtml = `
        <div class="modal fade" id="modalPerfil" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-person-gear"></i> Editar Perfil
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="formEditarPerfil">
                            <div class="mb-3">
                                <label class="form-label">Nome Completo</label>
                                <input type="text" class="form-control" id="editNome" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="editEmail" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">CPF</label>
                                <input type="text" class="form-control" id="editCpf" 
                                       placeholder="000.000.000-00" maxlength="14">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Telefone</label>
                                <input type="text" class="form-control" id="editTelefone" 
                                       placeholder="(00) 00000-0000">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Nova Senha</label>
                                <input type="password" class="form-control" id="editSenha" 
                                       placeholder="Deixe em branco para não alterar" minlength="6">
                                <small class="text-muted">Mínimo 6 caracteres. Deixe em branco para manter a senha atual.</small>
                            </div>
                        </form>
                        <div id="alertPerfil"></div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                        <button type="button" class="btn btn-primary" onclick="salvarPerfil()">
                            <i class="bi bi-save"></i> Salvar Alterações
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Adicionar máscaras
    const cpfInput = document.getElementById('editCpf');
    cpfInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length <= 11) {
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            e.target.value = value;
        }
    });
    
    const telInput = document.getElementById('editTelefone');
    telInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length <= 11) {
            value = value.replace(/(\d{2})(\d)/, '($1) $2');
            value = value.replace(/(\d{5})(\d)/, '$1-$2');
            e.target.value = value;
        }
    });
}

async function salvarPerfil() {
    const alertDiv = document.getElementById('alertPerfil');
    const usuario = JSON.parse(localStorage.getItem('usuario'));
    const token = localStorage.getItem('token');
    
    // Verificar autenticação
    if (!token || !usuario) {
        alertDiv.innerHTML = '<div class="alert alert-danger">Sessão expirada. Faça login novamente.</div>';
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        return;
    }
    
    const dados = {
        nome: document.getElementById('editNome').value.trim(),
        email: document.getElementById('editEmail').value.trim(),
        cpf: document.getElementById('editCpf').value.trim(),
        telefone: document.getElementById('editTelefone').value.trim()
    };
    
    const senha = document.getElementById('editSenha').value.trim();
    if (senha) {
        if (senha.length < 6) {
            alertDiv.innerHTML = '<div class="alert alert-warning">A senha deve ter no mínimo 6 caracteres</div>';
            return;
        }
        dados.senha = senha;
    }
    
    // Validações
    if (!dados.nome || !dados.email) {
        alertDiv.innerHTML = '<div class="alert alert-warning">Nome e email são obrigatórios</div>';
        return;
    }
    
    // Validar email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(dados.email)) {
        alertDiv.innerHTML = '<div class="alert alert-warning">Email inválido</div>';
        return;
    }
    
    try {
        alertDiv.innerHTML = '<div class="alert alert-info">Salvando alterações...</div>';
        
        const response = await fetch('http://177.44.248.118:8000/api/perfil', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (response.status === 401) {
            alertDiv.innerHTML = '<div class="alert alert-danger">Sessão expirada. Faça login novamente.</div>';
            setTimeout(() => {
                localStorage.removeItem('token');
                localStorage.removeItem('usuario');
                window.location.href = 'login.html';
            }, 2000);
            return;
        }
        
        if (result.success) {
            // Atualizar localStorage
            const usuarioAtualizado = {
                ...usuario,
                nome: result.data.nome,
                email: result.data.email,
                cpf: result.data.cpf,
                telefone: result.data.telefone
            };
            localStorage.setItem('usuario', JSON.stringify(usuarioAtualizado));
            
            alertDiv.innerHTML = '<div class="alert alert-success">Perfil atualizado com sucesso!</div>';
            
            // Atualizar nome no botão
            const btnPerfil = document.getElementById('btnPerfil');
            if (btnPerfil) {
                btnPerfil.innerHTML = `<i class="bi bi-person-circle"></i> ${result.data.nome}`;
            }
            
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalPerfil'));
                modal.hide();
            }, 1500);
        } else {
            const erros = result.errors ? Object.values(result.errors).flat().join('<br>') : result.message;
            alertDiv.innerHTML = `<div class="alert alert-danger">${erros}</div>`;
        }
    } catch (error) {
        console.error('Erro ao atualizar perfil:', error);
        alertDiv.innerHTML = '<div class="alert alert-danger">Erro de conexão. Verifique sua internet e tente novamente.</div>';
    }
}

// Inicializar ao carregar a página
document.addEventListener('DOMContentLoaded', () => {
    adicionarBotaoPerfil();
});
