// License Manager Frontend Application
class LicenseManager {
    constructor() {
        this.apiBase = 'http://localhost:5000';
        this.currentUser = null;
        this.currentRole = null;
        this.users = [];
        this.licenses = [];
        this.licenseTypes = [];
        this.admins = [];
        this.auditLogs = [];
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkAuth();
    }

    setupEventListeners() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });

        // Change password
        document.getElementById('changePasswordBtn').addEventListener('click', () => {
            this.showChangePasswordModal();
        });

        // Tab navigation
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                this.handleTabChange(e.target.getAttribute('data-bs-target'));
            });
        });

        // Search and filter
        document.getElementById('userSearch').addEventListener('input', (e) => {
            this.filterUsers();
        });

        document.getElementById('departmentFilter').addEventListener('change', () => {
            this.filterUsers();
        });

        document.getElementById('licenseFilter').addEventListener('change', () => {
            this.filterUsers();
        });

        // Add buttons
        document.getElementById('addUserBtn').addEventListener('click', () => {
            this.showUserModal();
        });

        document.getElementById('assignLicenseBtn').addEventListener('click', () => {
            this.showAssignLicenseModal();
        });

        document.getElementById('addLicenseTypeBtn').addEventListener('click', () => {
            this.showLicenseTypeModal();
        });

        document.getElementById('createAdminBtn').addEventListener('click', () => {
            this.showCreateAdminModal();
        });

        // Form submissions
        document.getElementById('saveUserBtn').addEventListener('click', () => {
            this.saveUser();
        });

        document.getElementById('saveLicenseBtn').addEventListener('click', () => {
            this.assignLicense();
        });

        document.getElementById('saveLicenseTypeBtn').addEventListener('click', () => {
            this.saveLicenseType();
        });

        document.getElementById('saveAdminBtn').addEventListener('click', () => {
            this.createAdmin();
        });

        document.getElementById('savePasswordBtn').addEventListener('click', () => {
            this.changePassword();
        });

        // Transfer ownership
        document.getElementById('transferOwnershipBtn').addEventListener('click', () => {
            this.transferOwnership();
        });

        // Icon preview
        document.getElementById('licenseTypeIcon').addEventListener('change', (e) => {
            this.previewIcon(e.target.files[0]);
        });

        // Auto logout timer
        this.setupAutoLogout();
    }

    async checkAuth() {
        try {
            const response = await fetch(`${this.apiBase}/auth/me`, {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user.username;
                this.currentRole = data.user.role;
                this.showMainApp();
                await this.loadInitialData();
            } else {
                this.showLoginScreen();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.showLoginScreen();
        }
    }

    async login() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorDiv = document.getElementById('loginError');

        try {
            const response = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentUser = data.user.username;
                this.currentRole = data.user.role;
                this.showMainApp();
                await this.loadInitialData();
                this.showToast('Login successful!', 'success');
            } else {
                errorDiv.textContent = data.error || 'Login failed';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Network error. Please try again.';
            errorDiv.style.display = 'block';
        }
    }

    async logout() {
        try {
            await fetch(`${this.apiBase}/logout`, {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.currentUser = null;
            this.currentRole = null;
            this.showLoginScreen();
            this.showToast('Logged out successfully', 'info');
        }
    }

    showLoginScreen() {
        document.getElementById('loginScreen').style.display = 'flex';
        document.getElementById('mainApp').style.display = 'none';
        document.getElementById('loginError').style.display = 'none';
    }

    showMainApp() {
        document.getElementById('loginScreen').style.display = 'none';
        document.getElementById('mainApp').style.display = 'block';
        
        // Update user info
        document.getElementById('currentUser').textContent = this.currentUser;
        document.getElementById('userRole').textContent = this.currentRole;
        document.getElementById('userRole').className = `badge bg-light text-dark ms-1 role-${this.currentRole}`;

        // Show/hide admin tab
        if (this.currentRole === 'owner') {
            document.getElementById('adminTab').style.display = 'block';
        } else {
            document.getElementById('adminTab').style.display = 'none';
        }

        // Show/hide action buttons based on role
        const canEdit = this.currentRole === 'admin' || this.currentRole === 'owner';
        document.getElementById('addUserBtn').style.display = canEdit ? 'block' : 'none';
        document.getElementById('assignLicenseBtn').style.display = canEdit ? 'block' : 'none';
        document.getElementById('addLicenseTypeBtn').style.display = canEdit ? 'block' : 'none';
    }

    async loadInitialData() {
        await Promise.all([
            this.loadUsers(),
            this.loadLicenses(),
            this.loadLicenseTypes()
        ]);

        if (this.currentRole === 'owner') {
            await Promise.all([
                this.loadAdmins(),
                this.loadAuditLogs()
            ]);
        }
    }

    async loadUsers() {
        try {
            const response = await fetch(`${this.apiBase}/users`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.users = data.users;
                this.renderUsers();
                this.populateFilters();
            }
        } catch (error) {
            console.error('Failed to load users:', error);
            this.showToast('Failed to load users', 'error');
        }
    }

    async loadLicenses() {
        try {
            const response = await fetch(`${this.apiBase}/licenses`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.licenses = data.licenses;
                this.renderLicenses();
            }
        } catch (error) {
            console.error('Failed to load licenses:', error);
            this.showToast('Failed to load licenses', 'error');
        }
    }

    async loadLicenseTypes() {
        try {
            const response = await fetch(`${this.apiBase}/license-types`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.licenseTypes = data.license_types;
                this.renderLicenseTypes();
                this.populateLicenseTypeSelects();
            }
        } catch (error) {
            console.error('Failed to load license types:', error);
            this.showToast('Failed to load license types', 'error');
        }
    }

    async loadAdmins() {
        try {
            const response = await fetch(`${this.apiBase}/auth/admins`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.admins = data.admins;
                this.renderAdmins();
                this.populateNewOwnerSelect();
            }
        } catch (error) {
            console.error('Failed to load admins:', error);
            this.showToast('Failed to load admins', 'error');
        }
    }

    async loadAuditLogs() {
        try {
            const response = await fetch(`${this.apiBase}/audit/logs`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.auditLogs = data.logs;
                this.renderAuditLogs();
            }
        } catch (error) {
            console.error('Failed to load audit logs:', error);
            this.showToast('Failed to load audit logs', 'error');
        }
    }

    renderUsers() {
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = '';

        this.users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="d-flex align-items-center">
                        <div class="user-avatar me-2">${user.name.charAt(0)}</div>
                        <div>
                            <div class="fw-bold">${user.name}</div>
                            <small class="text-muted">${user.email}</small>
                        </div>
                    </div>
                </td>
                <td>${user.title || '-'}</td>
                <td>${user.department || '-'}</td>
                <td>${user.manager || '-'}</td>
                <td>
                    ${user.licenses.map(license => `
                        <span class="license-badge">
                            ${license.icon_url ? `<img src="${this.apiBase}${license.icon_url}" alt="${license.software_name}">` : ''}
                            ${license.software_name}
                        </span>
                    `).join('')}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-sm" onclick="app.viewUser(${user.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${(this.currentRole === 'admin' || this.currentRole === 'owner') ? `
                            <button class="btn btn-outline-warning btn-sm" onclick="app.editUser(${user.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="app.deleteUser(${user.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    renderLicenses() {
        const tbody = document.getElementById('licensesTableBody');
        tbody.innerHTML = '';

        this.licenses.forEach(license => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${license.user_name}</td>
                <td>${license.software_name}</td>
                <td>
                    ${license.icon_url ? `<img src="${this.apiBase}${license.icon_url}" alt="${license.license_type_name}" style="width: 20px; height: 20px; margin-right: 5px;">` : ''}
                    ${license.license_type_name || license.software_name}
                </td>
                <td><span class="badge bg-success">${license.status}</span></td>
                <td>${new Date(license.assigned_date).toLocaleDateString()}</td>
                <td>
                    ${(this.currentRole === 'admin' || this.currentRole === 'owner') ? `
                        <button class="btn btn-outline-danger btn-sm" onclick="app.revokeLicense(${license.id})">
                            <i class="fas fa-times"></i> Revoke
                        </button>
                    ` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    renderLicenseTypes() {
        const grid = document.getElementById('licenseTypesGrid');
        grid.innerHTML = '';

        this.licenseTypes.forEach(licenseType => {
            const col = document.createElement('div');
            col.className = 'col-md-3 col-sm-6 mb-3';
            col.innerHTML = `
                <div class="license-type-card">
                    <div class="license-type-icon">
                        ${licenseType.icon_url ? 
                            `<img src="${this.apiBase}${licenseType.icon_url}" alt="${licenseType.name}">` : 
                            '<i class="fas fa-tag"></i>'
                        }
                    </div>
                    <div class="license-type-name">${licenseType.name}</div>
                    <div class="license-type-actions">
                        ${(this.currentRole === 'admin' || this.currentRole === 'owner') ? `
                            <button class="btn btn-outline-danger btn-sm" onclick="app.deleteLicenseType(${licenseType.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
            grid.appendChild(col);
        });
    }

    renderAdmins() {
        const tbody = document.getElementById('adminsTableBody');
        tbody.innerHTML = '';

        this.admins.forEach(admin => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${admin.username}</td>
                <td><span class="badge role-${admin.role}">${admin.role}</span></td>
                <td>${new Date(admin.created_at).toLocaleDateString()}</td>
                <td>
                    ${admin.role !== 'owner' ? `
                        <button class="btn btn-outline-danger btn-sm" onclick="app.deleteAdmin(${admin.id})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    ` : ''}
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    renderAuditLogs() {
        const tbody = document.getElementById('auditLogsTableBody');
        tbody.innerHTML = '';

        this.auditLogs.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${new Date(log.timestamp).toLocaleString()}</td>
                <td><span class="badge bg-info">${log.action_type}</span></td>
                <td>${log.performed_by}</td>
                <td>${log.target || '-'}</td>
                <td>${log.details ? JSON.stringify(log.details) : '-'}</td>
            `;
            tbody.appendChild(row);
        });
    }

    populateFilters() {
        const departments = [...new Set(this.users.map(u => u.department).filter(d => d))];
        const licenseTypes = [...new Set(this.licenseTypes.map(lt => lt.name))];

        const deptSelect = document.getElementById('departmentFilter');
        const licenseSelect = document.getElementById('licenseFilter');

        deptSelect.innerHTML = '<option value="">All Departments</option>';
        departments.forEach(dept => {
            deptSelect.innerHTML += `<option value="${dept}">${dept}</option>`;
        });

        licenseSelect.innerHTML = '<option value="">All License Types</option>';
        licenseTypes.forEach(type => {
            licenseSelect.innerHTML += `<option value="${type}">${type}</option>`;
        });
    }

    populateLicenseTypeSelects() {
        const selects = [
            document.getElementById('licenseTypeSelect')
        ];

        selects.forEach(select => {
            if (select) {
                select.innerHTML = '<option value="">Select license type...</option>';
                this.licenseTypes.forEach(type => {
                    select.innerHTML += `<option value="${type.id}">${type.name}</option>`;
                });
            }
        });
    }

    populateNewOwnerSelect() {
        const select = document.getElementById('newOwnerSelect');
        select.innerHTML = '<option value="">Select admin user...</option>';
        
        this.admins.forEach(admin => {
            if (admin.role === 'admin') {
                select.innerHTML += `<option value="${admin.username}">${admin.username}</option>`;
            }
        });
    }

    filterUsers() {
        const searchTerm = document.getElementById('userSearch').value.toLowerCase();
        const departmentFilter = document.getElementById('departmentFilter').value;
        const licenseFilter = document.getElementById('licenseFilter').value;

        const filteredUsers = this.users.filter(user => {
            const matchesSearch = user.name.toLowerCase().includes(searchTerm) ||
                                user.email.toLowerCase().includes(searchTerm) ||
                                (user.title && user.title.toLowerCase().includes(searchTerm));

            const matchesDepartment = !departmentFilter || user.department === departmentFilter;

            const matchesLicense = !licenseFilter || 
                user.licenses.some(license => 
                    license.software_name === licenseFilter || 
                    license.license_type_name === licenseFilter
                );

            return matchesSearch && matchesDepartment && matchesLicense;
        });

        this.renderFilteredUsers(filteredUsers);
    }

    renderFilteredUsers(users) {
        const tbody = document.getElementById('usersTableBody');
        tbody.innerHTML = '';

        users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <div class="d-flex align-items-center">
                        <div class="user-avatar me-2">${user.name.charAt(0)}</div>
                        <div>
                            <div class="fw-bold">${user.name}</div>
                            <small class="text-muted">${user.email}</small>
                        </div>
                    </div>
                </td>
                <td>${user.title || '-'}</td>
                <td>${user.department || '-'}</td>
                <td>${user.manager || '-'}</td>
                <td>
                    ${user.licenses.map(license => `
                        <span class="license-badge">
                            ${license.icon_url ? `<img src="${this.apiBase}${license.icon_url}" alt="${license.software_name}">` : ''}
                            ${license.software_name}
                        </span>
                    `).join('')}
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary btn-sm" onclick="app.viewUser(${user.id})">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${(this.currentRole === 'admin' || this.currentRole === 'owner') ? `
                            <button class="btn btn-outline-warning btn-sm" onclick="app.editUser(${user.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger btn-sm" onclick="app.deleteUser(${user.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    handleTabChange(tabId) {
        switch (tabId) {
            case '#users':
                this.loadUsers();
                break;
            case '#licenses':
                this.loadLicenses();
                break;
            case '#license-types':
                this.loadLicenseTypes();
                break;
            case '#admin':
                if (this.currentRole === 'owner') {
                    this.loadAdmins();
                    this.loadAuditLogs();
                }
                break;
        }
    }

    // User Management
    showUserModal(user = null) {
        const modal = new bootstrap.Modal(document.getElementById('userModal'));
        const title = document.getElementById('userModalTitle');
        const form = document.getElementById('userForm');

        if (user) {
            title.textContent = 'Edit User';
            document.getElementById('userId').value = user.id;
            document.getElementById('userName').value = user.name;
            document.getElementById('userEmail').value = user.email;
            document.getElementById('userDepartment').value = user.department || '';
            document.getElementById('userManager').value = user.manager || '';
            document.getElementById('userTitle').value = user.title || '';
        } else {
            title.textContent = 'Add User';
            form.reset();
            document.getElementById('userId').value = '';
        }

        modal.show();
    }

    async saveUser() {
        const userId = document.getElementById('userId').value;
        const userData = {
            name: document.getElementById('userName').value,
            email: document.getElementById('userEmail').value,
            department: document.getElementById('userDepartment').value,
            manager: document.getElementById('userManager').value,
            title: document.getElementById('userTitle').value
        };

        try {
            const url = userId ? `${this.apiBase}/users/${userId}` : `${this.apiBase}/users`;
            const method = userId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('userModal')).hide();
                await this.loadUsers();
                this.showToast(userId ? 'User updated successfully' : 'User created successfully', 'success');
            } else {
                const data = await response.json();
                this.showToast(data.error || 'Failed to save user', 'error');
            }
        } catch (error) {
            console.error('Save user error:', error);
            this.showToast('Failed to save user', 'error');
        }
    }

    viewUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user) {
            this.showUserDetails(user);
        }
    }

    editUser(userId) {
        const user = this.users.find(u => u.id === userId);
        if (user) {
            this.showUserModal(user);
        }
    }

    async deleteUser(userId) {
        if (confirm('Are you sure you want to delete this user? This will also revoke all their licenses.')) {
            try {
                const response = await fetch(`${this.apiBase}/users/${userId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });

                if (response.ok) {
                    await this.loadUsers();
                    this.showToast('User deleted successfully', 'success');
                } else {
                    const data = await response.json();
                    this.showToast(data.error || 'Failed to delete user', 'error');
                }
            } catch (error) {
                console.error('Delete user error:', error);
                this.showToast('Failed to delete user', 'error');
            }
        }
    }

    // License Management
    showAssignLicenseModal() {
        const modal = new bootstrap.Modal(document.getElementById('assignLicenseModal'));
        
        // Populate user select
        const userSelect = document.getElementById('licenseUserSelect');
        userSelect.innerHTML = '<option value="">Select user...</option>';
        this.users.forEach(user => {
            userSelect.innerHTML += `<option value="${user.id}">${user.name} (${user.email})</option>`;
        });

        // Populate license type select
        const licenseTypeSelect = document.getElementById('licenseTypeSelect');
        licenseTypeSelect.innerHTML = '<option value="">Select license type...</option>';
        this.licenseTypes.forEach(type => {
            licenseTypeSelect.innerHTML += `<option value="${type.id}">${type.name}</option>`;
        });

        modal.show();
    }

    async assignLicense() {
        const userData = {
            user_id: parseInt(document.getElementById('licenseUserSelect').value),
            software_name: this.licenseTypes.find(lt => lt.id === parseInt(document.getElementById('licenseTypeSelect').value))?.name || '',
            license_type_id: parseInt(document.getElementById('licenseTypeSelect').value),
            license_key: document.getElementById('licenseKey').value,
            notes: document.getElementById('licenseNotes').value
        };

        try {
            const response = await fetch(`${this.apiBase}/licenses`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('assignLicenseModal')).hide();
                await this.loadLicenses();
                await this.loadUsers();
                this.showToast('License assigned successfully', 'success');
            } else {
                const data = await response.json();
                this.showToast(data.error || 'Failed to assign license', 'error');
            }
        } catch (error) {
            console.error('Assign license error:', error);
            this.showToast('Failed to assign license', 'error');
        }
    }

    async revokeLicense(licenseId) {
        if (confirm('Are you sure you want to revoke this license?')) {
            try {
                const response = await fetch(`${this.apiBase}/licenses/${licenseId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });

                if (response.ok) {
                    await this.loadLicenses();
                    await this.loadUsers();
                    this.showToast('License revoked successfully', 'success');
                } else {
                    const data = await response.json();
                    this.showToast(data.error || 'Failed to revoke license', 'error');
                }
            } catch (error) {
                console.error('Revoke license error:', error);
                this.showToast('Failed to revoke license', 'error');
            }
        }
    }

    // License Type Management
    showLicenseTypeModal() {
        const modal = new bootstrap.Modal(document.getElementById('licenseTypeModal'));
        document.getElementById('licenseTypeForm').reset();
        document.getElementById('iconPreview').style.display = 'none';
        modal.show();
    }

    previewIcon(file) {
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('iconPreviewImg').src = e.target.result;
                document.getElementById('iconPreview').style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }

    async saveLicenseType() {
        const formData = new FormData();
        formData.append('name', document.getElementById('licenseTypeName').value);
        
        const iconFile = document.getElementById('licenseTypeIcon').files[0];
        if (iconFile) {
            formData.append('icon', iconFile);
        }

        try {
            const response = await fetch(`${this.apiBase}/license-types`, {
                method: 'POST',
                credentials: 'include',
                body: formData
            });

            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('licenseTypeModal')).hide();
                await this.loadLicenseTypes();
                this.showToast('License type created successfully', 'success');
            } else {
                const data = await response.json();
                this.showToast(data.error || 'Failed to create license type', 'error');
            }
        } catch (error) {
            console.error('Save license type error:', error);
            this.showToast('Failed to create license type', 'error');
        }
    }

    async deleteLicenseType(licenseTypeId) {
        if (confirm('Are you sure you want to delete this license type?')) {
            try {
                const response = await fetch(`${this.apiBase}/license-types/${licenseTypeId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });

                if (response.ok) {
                    await this.loadLicenseTypes();
                    this.showToast('License type deleted successfully', 'success');
                } else {
                    const data = await response.json();
                    this.showToast(data.error || 'Failed to delete license type', 'error');
                }
            } catch (error) {
                console.error('Delete license type error:', error);
                this.showToast('Failed to delete license type', 'error');
            }
        }
    }

    // Admin Management
    showCreateAdminModal() {
        const modal = new bootstrap.Modal(document.getElementById('createAdminModal'));
        document.getElementById('createAdminForm').reset();
        modal.show();
    }

    async createAdmin() {
        const adminData = {
            username: document.getElementById('adminUsername').value,
            password: document.getElementById('adminPassword').value,
            role: document.getElementById('adminRole').value
        };

        try {
            const response = await fetch(`${this.apiBase}/auth/admins`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(adminData)
            });

            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('createAdminModal')).hide();
                await this.loadAdmins();
                this.showToast(`${adminData.role} user created successfully`, 'success');
            } else {
                const data = await response.json();
                this.showToast(data.error || 'Failed to create user', 'error');
            }
        } catch (error) {
            console.error('Create admin error:', error);
            this.showToast('Failed to create user', 'error');
        }
    }

    async deleteAdmin(adminId) {
        if (confirm('Are you sure you want to delete this user?')) {
            try {
                const response = await fetch(`${this.apiBase}/auth/admins/${adminId}`, {
                    method: 'DELETE',
                    credentials: 'include'
                });

                if (response.ok) {
                    await this.loadAdmins();
                    this.showToast('User deleted successfully', 'success');
                } else {
                    const data = await response.json();
                    this.showToast(data.error || 'Failed to delete user', 'error');
                }
            } catch (error) {
                console.error('Delete admin error:', error);
                this.showToast('Failed to delete user', 'error');
            }
        }
    }

    async transferOwnership() {
        const newOwner = document.getElementById('newOwnerSelect').value;
        if (!newOwner) {
            this.showToast('Please select a user to transfer ownership to', 'error');
            return;
        }

        if (confirm(`Are you sure you want to transfer ownership to ${newOwner}? This action cannot be undone.`)) {
            try {
                const response = await fetch(`${this.apiBase}/auth/transfer-ownership`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({ new_owner_username: newOwner })
                });

                if (response.ok) {
                    const data = await response.json();
                    this.showToast('Ownership transferred successfully', 'success');
                    
                    if (data.logout_required) {
                        setTimeout(() => {
                            this.logout();
                        }, 2000);
                    }
                } else {
                    const data = await response.json();
                    this.showToast(data.error || 'Failed to transfer ownership', 'error');
                }
            } catch (error) {
                console.error('Transfer ownership error:', error);
                this.showToast('Failed to transfer ownership', 'error');
            }
        }
    }

    // Password Management
    showChangePasswordModal() {
        const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
        document.getElementById('changePasswordForm').reset();
        modal.show();
    }

    async changePassword() {
        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (newPassword !== confirmPassword) {
            this.showToast('New passwords do not match', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/auth/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            if (response.ok) {
                bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
                this.showToast('Password changed successfully', 'success');
            } else {
                const data = await response.json();
                this.showToast(data.error || 'Failed to change password', 'error');
            }
        } catch (error) {
            console.error('Change password error:', error);
            this.showToast('Failed to change password', 'error');
        }
    }

    // Utility Functions
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to page
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        container.appendChild(toast);
        document.body.appendChild(container);

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove after hidden
        toast.addEventListener('hidden.bs.toast', () => {
            document.body.removeChild(container);
        });
    }

    setupAutoLogout() {
        let inactivityTimer;
        const timeout = 30 * 60 * 1000; // 30 minutes

        const resetTimer = () => {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(() => {
                this.showToast('Session expired due to inactivity', 'warning');
                this.logout();
            }, timeout);
        };

        // Reset timer on user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetTimer, true);
        });

        resetTimer();
    }

    showUserDetails(user) {
        // This could be expanded to show a detailed user modal
        alert(`User Details:\nName: ${user.name}\nEmail: ${user.email}\nTitle: ${user.title || 'N/A'}\nDepartment: ${user.department || 'N/A'}\nManager: ${user.manager || 'N/A'}\nLicenses: ${user.licenses.length}`);
    }
}

// Initialize the application
const app = new LicenseManager(); 