/**
 * FinanceIQ - JavaScript Global
 * Funciones utilitarias disponibles en toda la aplicación
 */

// ============================================================
// UTILIDADES GLOBALES
// ============================================================

const FinanceIQ = {

    // Formatear número como moneda
    formatCurrency(amount, decimals = 0) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        }).format(amount);
    },

    // Formatear porcentaje
    formatPercent(value, decimals = 1) {
        return `${parseFloat(value).toFixed(decimals)}%`;
    },

    // Obtener cookie CSRF
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return cookieValue;
    },

    // Petición AJAX con CSRF
    async fetchJSON(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
        };
        const mergedOptions = { ...defaultOptions, ...options };
        if (options.headers) {
            mergedOptions.headers = {
                ...defaultOptions.headers,
                ...options.headers,
            };
        }
        const response = await fetch(url, mergedOptions);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    },

    // Mostrar notificación toast
    showToast(message, type = 'info') {
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500',
        };
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️',
        };

        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 z-50 flex items-center gap-3
                          ${colors[type]} text-white px-5 py-3 rounded-xl shadow-lg
                          transform translate-y-0 transition-all duration-300`;
        toast.innerHTML = `
            <span>${icons[type]}</span>
            <span class="font-medium">${message}</span>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    },

    // Confirmar acción con modal personalizado
    confirm(message, onConfirm, onCancel = null) {
        const modal = document.createElement('div');
        modal.className = `fixed inset-0 bg-black bg-opacity-50 z-50
                          flex items-center justify-center p-4`;
        modal.innerHTML = `
            <div class="bg-white rounded-2xl shadow-2xl p-6 max-w-sm w-full">
                <p class="text-lg font-semibold text-gray-800 mb-2">
                    ⚠️ Confirmar acción
                </p>
                <p class="text-gray-600 mb-6">${message}</p>
                <div class="flex gap-3">
                    <button id="confirmBtn"
                        class="flex-1 bg-red-500 hover:bg-red-600 text-white
                               font-medium py-2 px-4 rounded-xl transition-colors">
                        Confirmar
                    </button>
                    <button id="cancelBtn"
                        class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700
                               font-medium py-2 px-4 rounded-xl transition-colors">
                        Cancelar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#confirmBtn').addEventListener('click', () => {
            modal.remove();
            if (onConfirm) onConfirm();
        });

        modal.querySelector('#cancelBtn').addEventListener('click', () => {
            modal.remove();
            if (onCancel) onCancel();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                if (onCancel) onCancel();
            }
        });
    },

    // Formatear fecha
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('es-CO', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    },

    // Calcular días restantes
    daysUntil(dateStr) {
        const today = new Date();
        const target = new Date(dateStr);
        const diff = target - today;
        return Math.ceil(diff / (1000 * 60 * 60 * 24));
    },

    // Debounce
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Mobile sidebar toggle
    initMobileSidebar() {
        const toggleBtn = document.getElementById('mobileSidebarToggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        const mainContent = document.getElementById('mainContent');

        if (!toggleBtn || !sidebar || !overlay || !mainContent) return;

        const toggleSidebar = () => {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
            mainContent.classList.toggle('ml-72');
        };

        toggleBtn.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', toggleSidebar);

        // Close sidebar on nav link click (mobile)
        document.querySelectorAll('#sidebar a[href]').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('active');
                    overlay.classList.remove('active');
                    mainContent.classList.remove('ml-72');
                }
            });
        });

        // Close on resize to desktop
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
                mainContent.classList.remove('ml-72');
            }
        });
    },

    // Inicializar tooltips
    initTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            el.addEventListener('mouseenter', function() {
                const tooltip = document.createElement('div');
                tooltip.className = `absolute z-50 bg-gray-800 text-white text-xs
                                    px-2 py-1 rounded-lg pointer-events-none
                                    transform -translate-x-1/2 -translate-y-full
                                    -mt-2 whitespace-nowrap`;
                tooltip.textContent = this.dataset.tooltip;
                tooltip.id = 'active-tooltip';

                const rect = this.getBoundingClientRect();
                tooltip.style.left = `${rect.left + rect.width / 2}px`;
                tooltip.style.top = `${rect.top + window.scrollY}px`;
                tooltip.style.position = 'absolute';

                document.body.appendChild(tooltip);
            });

            el.addEventListener('mouseleave', () => {
                const tooltip = document.getElementById('active-tooltip');
                if (tooltip) tooltip.remove();
            });
        });
    },

    // Animar números (contador)
    animateNumber(element, start, end, duration = 1000) {
        const startTime = performance.now();
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (end - start) * eased);
            element.textContent = current.toLocaleString('es-CO');
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };
        requestAnimationFrame(update);
    },

    // Inicializar animaciones de números en el dashboard
    initNumberAnimations() {
        document.querySelectorAll('[data-animate-number]').forEach(el => {
            const target = parseFloat(el.dataset.animateNumber);
            this.animateNumber(el, 0, target);
        });
    },
};

// ============================================================
// INICIALIZACIÓN GLOBAL
// ============================================================

document.addEventListener('DOMContentLoaded', function() {

    // Inicializar tooltips
    FinanceIQ.initTooltips();

    // Inicializar animaciones de números
    FinanceIQ.initNumberAnimations();

    // Inicializar sidebar responsive mobile
    FinanceIQ.initMobileSidebar();

    // Interceptar formularios de eliminación para confirmar
    document.querySelectorAll('form[data-confirm]').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = this.dataset.confirm || '¿Estás seguro de esta acción?';
            FinanceIQ.confirm(message, () => {
                this.submit();
            });
        });
    });

    // Auto-cerrar mensajes de Django después de 5 segundos
    document.querySelectorAll('[data-auto-close]').forEach(el => {
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(-10px)';
            el.style.transition = 'all 0.3s ease';
            setTimeout(() => el.remove(), 300);
        }, 5000);
    });

    // Marcar enlace activo en sidebar
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a[href]').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Inicializar selector de período con URL params
    const urlParams = new URLSearchParams(window.location.search);
    const period = urlParams.get('period');
    if (period) {
        document.querySelectorAll(`[data-period="${period}"]`).forEach(el => {
            el.classList.add('active');
        });
    }
});

// ============================================================
// EXPORTAR PARA USO GLOBAL
// ============================================================
window.FinanceIQ = FinanceIQ;