/**
 * Results Page Script
 * Handles email preview and sending functionality on the results page
 */

import { EmailManager } from './modules/email.module.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Email Manager
    const emailManager = new EmailManager();

    console.log('Results page initialized');
});
