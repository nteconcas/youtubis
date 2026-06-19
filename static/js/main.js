/**
 * TubeDL - Main JavaScript
 * Funcionalidades interativas do frontend
 */

// ───────────────────────────────────────────────
// LOADING OVERLAY
// ───────────────────────────────────────────────

function showLoading(text = 'Processando...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    if (overlay && loadingText) {
        loadingText.textContent = text;
        overlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// ───────────────────────────────────────────────
// TOAST NOTIFICATIONS
// ───────────────────────────────────────────────

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ───────────────────────────────────────────────
// URL VALIDATION
// ───────────────────────────────────────────────

function isValidYouTubeUrl(url) {
    const patterns = [
        /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/playlist\?list=[\w-]+/,
        /^https?:\/\/youtu\.be\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/shorts\/[\w-]+/,
        /^https?:\/\/(www\.)?youtube\.com\/live\/[\w-]+/,
        /^https?:\/\/music\.youtube\.com\/watch\?v=[\w-]+/,
    ];
    return patterns.some(pattern => pattern.test(url.trim()));
}

// ───────────────────────────────────────────────
// FORM HANDLING
// ───────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // URL input validation on paste
    const urlInputs = document.querySelectorAll('input[type="url"], input[name="url"]');
    urlInputs.forEach(input => {
        input.addEventListener('paste', function(e) {
            setTimeout(() => {
                const url = this.value.trim();
                if (url && !isValidYouTubeUrl(url)) {
                    this.classList.add('border-red-500', 'ring-2', 'ring-red-200');
                    showToast('URL inválida. Use um link do YouTube.', 'error');
                } else {
                    this.classList.remove('border-red-500', 'ring-2', 'ring-red-200');
                }
            }, 10);
        });

        input.addEventListener('input', function() {
            this.classList.remove('border-red-500', 'ring-2', 'ring-red-200');
        });
    });

    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const urlInput = this.querySelector('input[name="url"]');
            if (urlInput && !isValidYouTubeUrl(urlInput.value)) {
                e.preventDefault();
                urlInput.classList.add('border-red-500', 'ring-2', 'ring-red-200');
                showToast('Por favor, insira um link válido do YouTube', 'error');
                urlInput.focus();
                return false;
            }
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});

// ───────────────────────────────────────────────
// AJAX DOWNLOAD (opcional - para futura implementação)
// ───────────────────────────────────────────────

async function downloadAsync(url, mode, options = {}) {
    showLoading(mode === 'video' ? 'Baixando vídeo...' : 'Baixando áudio...');

    const formData = new FormData();
    formData.append('url', url);
    formData.append('mode', mode);
    if (options.quality) formData.append('quality', options.quality);
    if (options.audio_format) formData.append('audio_format', options.audio_format);

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        });

        const data = await response.json();
        hideLoading();

        if (data.success) {
            showToast('Download concluído com sucesso!', 'success');
            // Trigger file download
            if (data.data && data.data.filename) {
                window.location.href = `/download-file/${encodeURIComponent(data.data.filename)}`;
            }
        } else {
            showToast(data.error || 'Erro no download', 'error');
        }
    } catch (error) {
        hideLoading();
        showToast('Erro de conexão. Tente novamente.', 'error');
        console.error(error);
    }
}

// ───────────────────────────────────────────────
// KEYBOARD SHORTCUTS
// ───────────────────────────────────────────────

document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus URL input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const urlInput = document.querySelector('input[name="url"]');
        if (urlInput) {
            urlInput.focus();
            urlInput.select();
        }
    }

    // Escape to close loading overlay
    if (e.key === 'Escape') {
        hideLoading();
    }
});

// ───────────────────────────────────────────────
// PROGRESS BAR SIMULATION (para futura implementação com WebSocket)
// ───────────────────────────────────────────────

function updateProgress(percent, text = '') {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;

    // Pode ser expandido para mostrar progresso real via WebSocket
    const loadingText = document.getElementById('loading-text');
    if (loadingText && text) {
        loadingText.textContent = text;
    }
}

// ───────────────────────────────────────────────
// HISTORY FUNCTIONS
// ───────────────────────────────────────────────

function deleteHistoryItem(id) {
    if (!confirm('Remover este item do histórico?')) return;

    fetch(`/api/delete-file/${id}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                const item = document.getElementById(`history-item-${id}`);
                if (item) {
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(100px)';
                    setTimeout(() => item.remove(), 300);
                }
                showToast('Item removido com sucesso', 'success');
            } else {
                showToast('Erro ao remover item', 'error');
            }
        })
        .catch(() => showToast('Erro de conexão', 'error'));
}

function clearAllHistory() {
    if (!confirm('Limpar todo o histórico e remover todos os arquivos? Esta ação não pode ser desfeita.')) return;

    fetch('/api/clear-history', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast('Histórico limpo com sucesso', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast('Erro ao limpar histórico', 'error');
            }
        })
        .catch(() => showToast('Erro de conexão', 'error'));
}

// ───────────────────────────────────────────────
// UTILITY FUNCTIONS
// ───────────────────────────────────────────────

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copiado para a área de transferência!', 'success');
    }).catch(() => {
        showToast('Erro ao copiar', 'error');
    });
}

function formatFileSize(bytes) {
    if (!bytes) return 'N/A';
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    for (const unit of units) {
        if (size < 1024) return `${size.toFixed(1)} ${unit}`;
        size /= 1024;
    }
    return `${size.toFixed(1)} TB`;
}

function formatDuration(seconds) {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    if (hours > 0) {
        return `${hours}:${String(remainingMins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${mins}:${String(secs).padStart(2, '0')}`;
}

console.log('🎬 TubeDL loaded successfully!');
