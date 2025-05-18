document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    var form = document.getElementById('content-generation-form');
    var overlay = document.getElementById('loading-overlay');
    var progressBar = document.getElementById('progress-bar');
    var progressLog = document.getElementById('progress-log');
    
    // Get campaign ID from data attribute - NO TEMPLATE VARIABLE!
    var campaignId = form.getAttribute('data-campaign-id');
    
    // Form submit handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        startGeneration();
    });
    
    // Start the generation process
    function startGeneration() {
        // Show overlay
        overlay.style.display = 'flex';
        progressLog.textContent = 'Starting content generation...';
        
        // Prepare form data
        var formData = new FormData(form);
        
        // Send AJAX request
        var xhr = new XMLHttpRequest();
        xhr.open('POST', form.action);
        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.status === 'success') {
                    // Start polling for progress
                    startPolling();
                } else {
                    // Show error
                    progressLog.textContent += '\nError: ' + response.message;
                }
            } else {
                progressLog.textContent += '\nError: Request failed';
            }
        };
        
        xhr.onerror = function() {
            progressLog.textContent += '\nError: Network error occurred';
        };
        
        xhr.send(formData);
    }
    
    // Poll for progress updates
    function startPolling() {
        pollProgress();
    }
    
    function pollProgress() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/campaign/' + campaignId + '/generate_content/progress');
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                var data = JSON.parse(xhr.responseText);
                
                // Update progress UI
                updateProgressBar(data.completed, data.total);
                updateProgressLog(data.messages);
                
                // Check status
                if (data.status === 'success' || data.status === 'completed') {
                    // Process complete, redirect
                    progressLog.textContent += '\nComplete! Redirecting to content page...';
                    setTimeout(function() {
                        window.location.href = '/campaign/' + campaignId + '/content';
                    }, 1500);
                } else if (data.status === 'in_progress') {
                    // Still in progress, continue polling
                    setTimeout(pollProgress, 1000);
                } else if (data.status === 'error') {
                    // Error occurred
                    progressLog.textContent += '\nError: ' + data.message;
                } else {
                    // Unknown status, poll again
                    setTimeout(pollProgress, 2000);
                }
            } else {
                // Error with request
                setTimeout(pollProgress, 2000);
            }
        };
        
        xhr.onerror = function() {
            // Network error, try again
            setTimeout(pollProgress, 2000);
        };
        
        xhr.send();
    }
    
    // Update progress bar
    function updateProgressBar(completed, total) {
        var percent = 0;
        if (total > 0) {
            percent = Math.round((completed / total) * 100);
        }
        
        progressBar.style.width = percent + '%';
        progressBar.textContent = percent + '% (' + completed + '/' + total + ')';
    }
    
    // Update progress log
    function updateProgressLog(messages) {
        if (!messages || messages.length === 0) {
            return;
        }
        
        // Get current messages
        var currentText = progressLog.textContent;
        var currentLines = currentText.split('\n').filter(function(line) {
            return line.trim() !== '';
        });
        
        // Add only new messages
        var newMessages = [];
        for (var i = 0; i < messages.length; i++) {
            var message = messages[i];
            if (currentLines.indexOf(message) === -1) {
                newMessages.push(message);
            }
        }
        
        if (newMessages.length > 0) {
            progressLog.textContent += '\n' + newMessages.join('\n');
            // Scroll to bottom
            progressLog.scrollTop = progressLog.scrollHeight;
        }
    }
});