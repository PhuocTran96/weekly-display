/**
 * Filter Manager Module
 * Manages alert filter configuration and preview
 */

export class FilterManager {
    constructor() {
        this.currentFilters = {};
        this.availableModels = [];
        this.availableChannels = [];
        this.availableStores = [];
        this.modelSearchTimeout = null;
        this.channelSearchTimeout = null;
        this.storeSearchTimeout = null;
    }

    /**
     * Initialize the filter manager
     */
    async init() {
        console.log('Initializing Filter Manager...');
        await this.loadFilters();
        await this.loadAvailableData();
        this.setupEventListeners();
        this.renderFilters();
        await this.previewFilters();
    }

    /**
     * Load current filters from API
     */
    async loadFilters() {
        try {
            const response = await fetch('/api/filters/');
            const data = await response.json();

            if (data.success) {
                this.currentFilters = data.filters;
                console.log('Filters loaded:', this.currentFilters);
            } else {
                this.showMessage('Error loading filters: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error loading filters:', error);
            this.showMessage('Error loading filters: ' + error.message, 'error');
        }
    }

    /**
     * Load available models, channels, and stores from current data
     */
    async loadAvailableData() {
        try {
            const [modelsRes, channelsRes, storesRes] = await Promise.all([
                fetch('/api/filters/models/search'),
                fetch('/api/filters/channels/list'),
                fetch('/api/filters/stores/list')
            ]);

            const modelsData = await modelsRes.json();
            const channelsData = await channelsRes.json();
            const storesData = await storesRes.json();

            if (modelsData.success) {
                this.availableModels = modelsData.models;
            }

            if (channelsData.success) {
                this.availableChannels = channelsData.channels;
            }

            if (storesData.success) {
                this.availableStores = storesData.stores;
            }

            console.log('Available data loaded:', {
                models: this.availableModels.length,
                channels: this.availableChannels.length,
                stores: this.availableStores.length
            });

        } catch (error) {
            console.error('Error loading available data:', error);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Filter enabled toggle
        const enabledToggle = document.getElementById('filterEnabled');
        enabledToggle.addEventListener('change', () => {
            this.currentFilters.enabled = enabledToggle.checked;
            this.previewFilters();
        });

        // Threshold inputs
        const minThreshold = document.getElementById('minThreshold');
        const maxThreshold = document.getElementById('maxThreshold');

        minThreshold.addEventListener('input', () => {
            this.currentFilters.min_threshold = parseInt(minThreshold.value) || 0;
            this.previewFilters();
        });

        maxThreshold.addEventListener('input', () => {
            this.currentFilters.max_threshold = parseInt(maxThreshold.value) || null;
            this.previewFilters();
        });

        // Model search inputs
        const whitelistInput = document.getElementById('whitelistModelInput');
        const blacklistInput = document.getElementById('blacklistModelInput');

        whitelistInput.addEventListener('input', (e) => {
            this.debounceModelSearch(e.target.value, 'whitelist');
        });

        blacklistInput.addEventListener('input', (e) => {
            this.debounceModelSearch(e.target.value, 'blacklist');
        });

        // Hide search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-box')) {
                document.querySelectorAll('.search-results').forEach(results => {
                    results.classList.remove('active');
                });
            }
        });

        // Add model buttons
        document.getElementById('whitelistModelInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addWhitelistModel();
            }
        });

        document.getElementById('blacklistModelInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addBlacklistModel();
            }
        });

        // Channel search input
        const channelInput = document.getElementById('channelInput');
        if (channelInput) {
            channelInput.addEventListener('input', (e) => {
                this.debounceChannelSearch(e.target.value);
            });

            channelInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addChannel();
                }
            });
        }

        // Store search input
        const storeInput = document.getElementById('storeInput');
        if (storeInput) {
            storeInput.addEventListener('input', (e) => {
                this.debounceStoreSearch(e.target.value);
            });

            storeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.addStore();
                }
            });
        }
    }

    /**
     * Debounce model search
     */
    debounceModelSearch(query, type) {
        clearTimeout(this.modelSearchTimeout);
        this.modelSearchTimeout = setTimeout(() => {
            this.searchModels(query, type);
        }, 300);
    }

    /**
     * Debounce channel search
     */
    debounceChannelSearch(query) {
        clearTimeout(this.channelSearchTimeout);
        this.channelSearchTimeout = setTimeout(() => {
            this.searchChannels(query);
        }, 300);
    }

    /**
     * Debounce store search
     */
    debounceStoreSearch(query) {
        clearTimeout(this.storeSearchTimeout);
        this.storeSearchTimeout = setTimeout(() => {
            this.searchStores(query);
        }, 300);
    }

    /**
     * Search models
     */
    async searchModels(query, type) {
        const resultsId = type === 'whitelist' ? 'whitelistSearchResults' : 'blacklistSearchResults';
        const resultsDiv = document.getElementById(resultsId);

        if (!query.trim()) {
            resultsDiv.classList.remove('active');
            return;
        }

        try {
            const response = await fetch(`/api/filters/models/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.success && data.models.length > 0) {
                // Filter out already added models
                const existingModels = type === 'whitelist' ?
                    this.currentFilters.whitelisted_models || [] :
                    this.currentFilters.blacklisted_models || [];

                const availableModels = data.models.filter(model => !existingModels.includes(model));

                if (availableModels.length > 0) {
                    resultsDiv.innerHTML = availableModels.map(model => `
                        <div class="search-result-item" onclick="window.filterManager.selectModel('${model}', '${type}')">
                            ${model}
                        </div>
                    `).join('');
                    resultsDiv.classList.add('active');
                } else {
                    resultsDiv.innerHTML = '<div class="search-result-item">No models found</div>';
                    resultsDiv.classList.add('active');
                }
            } else {
                resultsDiv.innerHTML = '<div class="search-result-item">No models found</div>';
                resultsDiv.classList.add('active');
            }
        } catch (error) {
            console.error('Error searching models:', error);
        }
    }

    /**
     * Search channels
     */
    async searchChannels(query) {
        const resultsDiv = document.getElementById('channelSearchResults');

        if (!query.trim()) {
            resultsDiv.classList.remove('active');
            return;
        }

        try {
            // If we have available channels loaded, filter them locally
            if (this.availableChannels.length > 0) {
                const filteredChannels = this.availableChannels.filter(channel =>
                    channel.toLowerCase().includes(query.toLowerCase()) &&
                    !this.currentFilters.channels?.includes(channel)
                );

                if (filteredChannels.length > 0) {
                    resultsDiv.innerHTML = filteredChannels.map(channel => `
                        <div class="search-result-item" onclick="window.filterManager.selectChannel('${channel}')">
                            ${channel}
                        </div>
                    `).join('');
                    resultsDiv.classList.add('active');
                } else {
                    resultsDiv.innerHTML = '<div class="search-result-item">No channels found</div>';
                    resultsDiv.classList.add('active');
                }
            } else {
                // Fallback to API call
                const response = await fetch('/api/filters/channels/list');
                const data = await response.json();

                if (data.success && data.channels.length > 0) {
                    this.availableChannels = data.channels;
                    const filteredChannels = data.channels.filter(channel =>
                        channel.toLowerCase().includes(query.toLowerCase()) &&
                        !this.currentFilters.channels?.includes(channel)
                    );

                    if (filteredChannels.length > 0) {
                        resultsDiv.innerHTML = filteredChannels.map(channel => `
                            <div class="search-result-item" onclick="window.filterManager.selectChannel('${channel}')">
                                ${channel}
                            </div>
                        `).join('');
                        resultsDiv.classList.add('active');
                    } else {
                        resultsDiv.innerHTML = '<div class="search-result-item">No channels found</div>';
                        resultsDiv.classList.add('active');
                    }
                } else {
                    resultsDiv.innerHTML = '<div class="search-result-item">No channels found</div>';
                    resultsDiv.classList.add('active');
                }
            }
        } catch (error) {
            console.error('Error searching channels:', error);
        }
    }

    /**
     * Search stores
     */
    async searchStores(query) {
        const resultsDiv = document.getElementById('storeSearchResults');

        if (!query.trim()) {
            resultsDiv.classList.remove('active');
            return;
        }

        try {
            // If we have available stores loaded, filter them locally
            if (this.availableStores.length > 0) {
                const filteredStores = this.availableStores.filter(store =>
                    store.toLowerCase().includes(query.toLowerCase()) &&
                    !this.currentFilters.stores?.includes(store)
                );

                if (filteredStores.length > 0) {
                    resultsDiv.innerHTML = filteredStores.map(store => `
                        <div class="search-result-item" onclick="window.filterManager.selectStore('${store}')">
                            ${store}
                        </div>
                    `).join('');
                    resultsDiv.classList.add('active');
                } else {
                    resultsDiv.innerHTML = '<div class="search-result-item">No stores found</div>';
                    resultsDiv.classList.add('active');
                }
            } else {
                // Fallback to API call
                const response = await fetch('/api/filters/stores/list');
                const data = await response.json();

                if (data.success && data.stores.length > 0) {
                    this.availableStores = data.stores;
                    const filteredStores = data.stores.filter(store =>
                        store.toLowerCase().includes(query.toLowerCase()) &&
                        !this.currentFilters.stores?.includes(store)
                    );

                    if (filteredStores.length > 0) {
                        resultsDiv.innerHTML = filteredStores.map(store => `
                            <div class="search-result-item" onclick="window.filterManager.selectStore('${store}')">
                                ${store}
                            </div>
                        `).join('');
                        resultsDiv.classList.add('active');
                    } else {
                        resultsDiv.innerHTML = '<div class="search-result-item">No stores found</div>';
                        resultsDiv.classList.add('active');
                    }
                } else {
                    resultsDiv.innerHTML = '<div class="search-result-item">No stores found</div>';
                    resultsDiv.classList.add('active');
                }
            }
        } catch (error) {
            console.error('Error searching stores:', error);
        }
    }

    /**
     * Select model from search results
     */
    selectModel(model, type) {
        const inputId = type === 'whitelist' ? 'whitelistModelInput' : 'blacklistModelInput';
        document.getElementById(inputId).value = model;

        // Hide search results
        const resultsId = type === 'whitelist' ? 'whitelistSearchResults' : 'blacklistSearchResults';
        document.getElementById(resultsId).classList.remove('active');

        // Add the model
        if (type === 'whitelist') {
            this.addWhitelistModel();
        } else {
            this.addBlacklistModel();
        }
    }

    /**
     * Add model to whitelist
     */
    addWhitelistModel() {
        const input = document.getElementById('whitelistModelInput');
        const model = input.value.trim();

        if (!model) return;

        if (!this.currentFilters.whitelisted_models) {
            this.currentFilters.whitelisted_models = [];
        }

        if (!this.currentFilters.whitelisted_models.includes(model)) {
            this.currentFilters.whitelisted_models.push(model);
            this.renderModelLists();
            this.previewFilters();
        }

        input.value = '';
        document.getElementById('whitelistSearchResults').classList.remove('active');
    }

    /**
     * Add model to blacklist
     */
    addBlacklistModel() {
        const input = document.getElementById('blacklistModelInput');
        const model = input.value.trim();

        if (!model) return;

        if (!this.currentFilters.blacklisted_models) {
            this.currentFilters.blacklisted_models = [];
        }

        if (!this.currentFilters.blacklisted_models.includes(model)) {
            this.currentFilters.blacklisted_models.push(model);
            this.renderModelLists();
            this.previewFilters();
        }

        input.value = '';
        document.getElementById('blacklistSearchResults').classList.remove('active');
    }

    /**
     * Select channel from search results
     */
    selectChannel(channel) {
        document.getElementById('channelInput').value = channel;
        document.getElementById('channelSearchResults').classList.remove('active');
        this.addChannel();
    }

    /**
     * Select store from search results
     */
    selectStore(store) {
        document.getElementById('storeInput').value = store;
        document.getElementById('storeSearchResults').classList.remove('active');
        this.addStore();
    }

    /**
     * Add channel
     */
    addChannel() {
        const input = document.getElementById('channelInput');
        const channel = input.value.trim();

        if (!channel) return;

        if (!this.currentFilters.channels) {
            this.currentFilters.channels = [];
        }

        if (!this.currentFilters.channels.includes(channel)) {
            this.currentFilters.channels.push(channel);
            this.renderMultiSelects();
            this.previewFilters();
        }

        input.value = '';
        document.getElementById('channelSearchResults').classList.remove('active');
    }

    /**
     * Add store
     */
    addStore() {
        const input = document.getElementById('storeInput');
        const store = input.value.trim();

        if (!store) return;

        if (!this.currentFilters.stores) {
            this.currentFilters.stores = [];
        }

        if (!this.currentFilters.stores.includes(store)) {
            this.currentFilters.stores.push(store);
            this.renderMultiSelects();
            this.previewFilters();
        }

        input.value = '';
        document.getElementById('storeSearchResults').classList.remove('active');
    }

    /**
     * Remove model from whitelist
     */
    removeWhitelistModel(model) {
        if (this.currentFilters.whitelisted_models) {
            this.currentFilters.whitelisted_models = this.currentFilters.whitelisted_models.filter(m => m !== model);
            this.renderModelLists();
            this.previewFilters();
        }
    }

    /**
     * Remove model from blacklist
     */
    removeBlacklistModel(model) {
        if (this.currentFilters.blacklisted_models) {
            this.currentFilters.blacklisted_models = this.currentFilters.blacklisted_models.filter(m => m !== model);
            this.renderModelLists();
            this.previewFilters();
        }
    }

    /**
     * Render model lists
     */
    renderModelLists() {
        const whitelistDiv = document.getElementById('whitelistModels');
        const blacklistDiv = document.getElementById('blacklistModels');

        const whitelistModels = this.currentFilters.whitelisted_models || [];
        const blacklistModels = this.currentFilters.blacklisted_models || [];

        whitelistDiv.innerHTML = whitelistModels.length > 0 ?
            whitelistModels.map(model => `
                <div class="model-item">
                    <span>${model}</span>
                    <button onclick="window.filterManager.removeWhitelistModel('${model}')">×</button>
                </div>
            `).join('') :
            '<p style="color: #999; text-align: center;">No models added</p>';

        blacklistDiv.innerHTML = blacklistModels.length > 0 ?
            blacklistModels.map(model => `
                <div class="model-item">
                    <span>${model}</span>
                    <button onclick="window.filterManager.removeBlacklistModel('${model}')">×</button>
                </div>
            `).join('') :
            '<p style="color: #999; text-align: center;">No models added</p>';
    }

    /**
     * Render multi-select elements for channels and stores
     */
    renderMultiSelects() {
        const channelDiv = document.getElementById('channelSelect');
        const storeDiv = document.getElementById('storeSelect');

        const selectedChannels = this.currentFilters.channels || [];
        const selectedStores = this.currentFilters.stores || [];

        channelDiv.innerHTML = selectedChannels.length > 0 ?
            selectedChannels.map(channel => `
                <div class="multi-select-item">
                    ${channel}
                    <button onclick="window.filterManager.removeChannel('${channel}')">×</button>
                </div>
            `).join('') :
            '<p style="color: #999; padding: 10px;">No channels selected</p>';

        storeDiv.innerHTML = selectedStores.length > 0 ?
            selectedStores.map(store => `
                <div class="multi-select-item">
                    ${store}
                    <button onclick="window.filterManager.removeStore('${store}')">×</button>
                </div>
            `).join('') :
            '<p style="color: #999; padding: 10px;">No stores selected</p>';
    }

    /**
     * Render all filters in the UI
     */
    renderFilters() {
        // Enabled toggle
        document.getElementById('filterEnabled').checked = this.currentFilters.enabled || false;

        // Thresholds
        document.getElementById('minThreshold').value = this.currentFilters.min_threshold || '';
        document.getElementById('maxThreshold').value = this.currentFilters.max_threshold || '';

        // Model lists
        this.renderModelLists();

        // Multi-selects
        this.renderMultiSelects();
    }

    /**
     * Remove channel from selection
     */
    removeChannel(channel) {
        if (this.currentFilters.channels) {
            this.currentFilters.channels = this.currentFilters.channels.filter(c => c !== channel);
            this.renderMultiSelects();
            this.previewFilters();
        }
    }

    /**
     * Remove store from selection
     */
    removeStore(store) {
        if (this.currentFilters.stores) {
            this.currentFilters.stores = this.currentFilters.stores.filter(s => s !== store);
            this.renderMultiSelects();
            this.previewFilters();
        }
    }

    /**
     * Preview filters
     */
    async previewFilters() {
        try {
            const response = await fetch('/api/filters/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filters: this.currentFilters
                })
            });

            const data = await response.json();

            if (data.success) {
                this.renderPreviewStats(data.preview.summary);
            } else {
                this.showMessage('Preview error: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error previewing filters:', error);
            this.showMessage('Preview error: ' + error.message, 'error');
        }
    }

    /**
     * Render preview statistics
     */
    renderPreviewStats(stats) {
        document.getElementById('originalCount').textContent = stats.original_count;
        document.getElementById('filteredCount').textContent = stats.filtered_count;
        document.getElementById('hiddenCount').textContent = stats.hidden_count;
        document.getElementById('reductionPercentage').textContent = stats.reduction_percentage.toFixed(1) + '%';
    }

    /**
     * Save filters
     */
    async saveFilters() {
        try {
            const response = await fetch('/api/filters/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.currentFilters)
            });

            const data = await response.json();

            if (data.success) {
                this.currentFilters = data.filters;
                this.renderFilters();
                this.showMessage('Filters saved successfully!', 'success');
            } else {
                this.showMessage('Error saving filters: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error saving filters:', error);
            this.showMessage('Error saving filters: ' + error.message, 'error');
        }
    }

    /**
     * Reset filters to defaults
     */
    async resetFilters() {
        if (!confirm('Are you sure you want to reset all filters to default values?')) {
            return;
        }

        try {
            const response = await fetch('/api/filters/reset', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.currentFilters = data.filters;
                this.renderFilters();
                await this.previewFilters();
                this.showMessage('Filters reset to defaults', 'success');
            } else {
                this.showMessage('Error resetting filters: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error resetting filters:', error);
            this.showMessage('Error resetting filters: ' + error.message, 'error');
        }
    }

    /**
     * Show message to user
     */
    showMessage(message, type = 'info') {
        const container = document.getElementById('messageContainer');
        const messageDiv = document.createElement('div');
        messageDiv.className = type;
        messageDiv.textContent = message;

        container.innerHTML = '';
        container.appendChild(messageDiv);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}