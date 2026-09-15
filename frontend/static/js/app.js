/**
 * CityFix Core Client Application
 * Dynamic Branding, Session Handling, and Mobile Navigation
 */

const CityFixApp = {
    config: null,
    user: null,
    token: null,

    async init() {
        this.loadSession();
        await this.loadConfig();
        this.updateAuthNav();
        this.bindEvents();
        this.highlightActiveNav();
    },

    loadSession() {
        this.token = localStorage.getItem("cityfix_token");
        const storedUser = localStorage.getItem("cityfix_user");
        if (storedUser) {
            try {
                this.user = JSON.parse(storedUser);
            } catch (e) {
                this.user = null;
            }
        }
    },

    async loadConfig() {
        try {
            const res = await fetch("/api/config");
            if (res.ok) {
                this.config = await res.json();
                this.applyBranding();
            }
        } catch (err) {
            console.warn("Using default branding fallback:", err);
            this.config = {
                app_name: "CityFix",
                app_tagline: "Fix Your City, One Report at a Time."
            };
            this.applyBranding();
        }
    },

    applyBranding() {
        if (!this.config) return;
        document.querySelectorAll("[data-brand-name]").forEach(el => {
            el.textContent = this.config.app_name;
        });
        document.querySelectorAll("[data-brand-tagline]").forEach(el => {
            el.textContent = this.config.app_tagline;
        });
    },

    updateAuthNav() {
        const desktopAuth = document.getElementById("nav-auth-container");
        const mobileAuth = document.getElementById("mobile-auth-container");
        if (desktopAuth) desktopAuth.classList.remove("hidden");
        document.querySelectorAll('nav a[href="/dashboard"]').forEach(link => {
            link.classList.toggle("hidden", !(this.user && this.token));
            link.textContent = "My Dashboard";
        });

        if (this.user && this.token) {
            const authContent = `
                <div class="flex items-center gap-3">
                    <a href="/dashboard" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold transition">
                        <span class="w-2 h-2 rounded-full bg-blue-600"></span>
                        <span>${this.escapeHtml(this.user.full_name || 'Citizen')}</span>
                    </a>
                    <button class="btn-logout text-xs text-rose-600 hover:text-rose-700 font-semibold px-2 py-1 rounded hover:bg-rose-50 transition">
                        Logout
                    </button>
                </div>
            `;
            if (desktopAuth) desktopAuth.innerHTML = authContent;
            if (mobileAuth) mobileAuth.innerHTML = authContent;

            document.querySelectorAll(".btn-logout").forEach(btn => {
                btn.addEventListener("click", () => this.logout());
            });
        } else {
            const guestContent = `
                <div class="flex items-center gap-2">
                    <a href="/login" class="text-sm font-semibold text-slate-700 hover:text-blue-600 px-3 py-2 rounded-lg transition">Login</a>
                    <a href="/login?tab=register" class="text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-xl shadow-md shadow-blue-500/20 transition transform hover:-translate-y-0.5">Sign Up</a>
                </div>
            `;
            if (desktopAuth) desktopAuth.innerHTML = guestContent;
            if (mobileAuth) mobileAuth.innerHTML = guestContent;
        }
    },

    highlightActiveNav() {
        const currentPath = window.location.pathname;
        document.querySelectorAll("nav a").forEach(link => {
            const href = link.getAttribute("href");
            if (href === currentPath || (currentPath === "/" && href === "/")) {
                link.classList.add("text-blue-600", "font-bold");
                link.classList.remove("text-slate-600");
            }
        });
    },

    async logout() {
        localStorage.removeItem("cityfix_token");
        localStorage.removeItem("cityfix_user");
        this.token = null;
        this.user = null;
        try { await fetch("/api/auth/logout", { method: "POST" }); } catch (error) { console.warn("Session cookie cleanup failed", error); }
        window.location.href = "/";
    },

    bindEvents() {
        const menuBtn = document.getElementById("mobile-menu-btn");
        const mobileMenu = document.getElementById("mobile-menu-drawer");
        
        if (menuBtn && mobileMenu) {
            menuBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                mobileMenu.classList.toggle("hidden");
                const icon = menuBtn.querySelector("i");
                if (icon) {
                    if (mobileMenu.classList.contains("hidden")) {
                        icon.setAttribute("data-lucide", "menu");
                    } else {
                        icon.setAttribute("data-lucide", "x");
                    }
                    if (window.lucide) lucide.createIcons();
                }
            });

            // Close on click outside
            document.addEventListener("click", (e) => {
                if (!mobileMenu.contains(e.target) && !menuBtn.contains(e.target)) {
                    mobileMenu.classList.add("hidden");
                    const icon = menuBtn.querySelector("i");
                    if (icon) {
                        icon.setAttribute("data-lucide", "menu");
                        if (window.lucide) lucide.createIcons();
                    }
                }
            });
        }
    },

    escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
};

document.addEventListener("DOMContentLoaded", () => {
    CityFixApp.init();
});
