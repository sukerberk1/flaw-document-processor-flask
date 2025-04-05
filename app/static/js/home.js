// Function to highlight JSON syntax with colors
function syntaxHighlight(json) {
    if (!json) return '';
    
    // Replace any potentially harmful characters
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        let cls = 'json-number';
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'json-key';
            } else {
                cls = 'json-string';
            }
        } else if (/true|false/.test(match)) {
            cls = 'json-boolean';
        } else if (/null/.test(match)) {
            cls = 'json-null';
        }
        return '<span class="' + cls + '">' + match + '</span>';
    });
}

// Handle file upload UI and flash messages
document.addEventListener('DOMContentLoaded', function () {
    // Handle collapsible file section
    const toggleButton = document.getElementById('toggle-files');
    const filesContainer = document.getElementById('files-container');
    
    if (toggleButton && filesContainer) {
        // Set initial height for smooth animation
        filesContainer.style.maxHeight = filesContainer.scrollHeight + 'px';
        
        toggleButton.addEventListener('click', function() {
            if (filesContainer.classList.contains('collapsed')) {
                // Expand
                filesContainer.classList.remove('collapsed');
                filesContainer.style.maxHeight = filesContainer.scrollHeight + 'px';
                toggleButton.textContent = 'Collapse';
                
                // Store preference in localStorage
                localStorage.setItem('filesContainerCollapsed', 'false');
            } else {
                // Collapse
                filesContainer.classList.add('collapsed');
                filesContainer.style.maxHeight = '0';
                toggleButton.textContent = 'Expand';
                
                // Store preference in localStorage
                localStorage.setItem('filesContainerCollapsed', 'true');
            }
        });
        
        // Check for saved preference
        const savedPreference = localStorage.getItem('filesContainerCollapsed');
        if (savedPreference === 'true') {
            filesContainer.classList.add('collapsed');
            filesContainer.style.maxHeight = '0';
            toggleButton.textContent = 'Expand';
        }
    }
    
    // Flash messages fade out
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        // Add fade-in effect
        message.style.opacity = '0';
        message.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            message.style.opacity = '1';
        }, 100);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
    
    // File input enhancement
    const fileInput = document.querySelector('#file-upload');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const numFiles = this.files.length;
            
            // Update the label text
            const fileInputLabel = this.nextElementSibling;
            if (fileInputLabel) {
                if (numFiles === 0) {
                    fileInputLabel.textContent = 'Choose files or folders';
                } else if (numFiles === 1) {
                    fileInputLabel.textContent = `Selected: ${this.files[0].name}`;
                } else {
                    fileInputLabel.textContent = `Selected: ${numFiles} files`;
                }
            }
            
            // Update the upload button
            const submitBtn = this.closest('form').querySelector('button[type="submit"]');
            if (submitBtn) {
                if (numFiles === 0) {
                    submitBtn.textContent = 'Upload';
                } else if (numFiles === 1) {
                    submitBtn.textContent = `Upload 1 file`;
                } else {
                    submitBtn.textContent = `Upload ${numFiles} files`;
                }
            }
        });
    }
    
    // Wait a bit to ensure the files container has its proper height
    setTimeout(() => {
        // Update max-height after adding content
        const filesContainer = document.getElementById('files-container');
        if (filesContainer && !filesContainer.classList.contains('collapsed')) {
            filesContainer.style.maxHeight = filesContainer.scrollHeight + 'px';
        }
        
        // Add a subtle animation to file list items and visual cues for directories
        const fileItems = document.querySelectorAll('.files-list li');
        
        // First apply visual grouping for directories and their children
        fileItems.forEach(item => {
            if (item.classList.contains('directory-item')) {
                const dirPath = item.dataset.dir;
                // Highlight child items when hovering over a directory
                item.addEventListener('mouseenter', () => {
                    // Find all files that are children of this directory
                    const childItems = document.querySelectorAll(`.file-item`);
                    childItems.forEach(child => {
                        const filePath = child.querySelector('input[name="filepath"]').value;
                        if (filePath.startsWith(dirPath + '/')) {
                            child.classList.add('directory-child-hover');
                        }
                    });
                    item.classList.add('directory-hover');
                });
                
                item.addEventListener('mouseleave', () => {
                    document.querySelectorAll('.directory-child-hover').forEach(el => {
                        el.classList.remove('directory-child-hover');
                    });
                    item.classList.remove('directory-hover');
                });
            }
        });
        
        // Then apply the animations
        fileItems.forEach((item, index) => {
            const depth = parseInt(item.style.paddingLeft) / 20 - 0.5;
            
            item.style.opacity = '0';
            item.style.transform = 'translateX(-10px)';
            item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            
            // Stagger the animations based on depth to create a cascade effect
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, (depth * 50) + (index * 30));
        });
    }, 100);
    
    // Add confirmation for delete buttons
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const filepath = this.querySelector('input[name="filepath"]').value;
            const isDirectory = this.closest('li').classList.contains('directory-item');
            
            let message = `Are you sure you want to delete "${filepath}"?`;
            if (isDirectory) {
                message = `Are you sure you want to delete the directory "${filepath}" and ALL its contents?`;
            }
            
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
    
    // Set up document scanning functionality
    const scannedSection = document.querySelector('.scanned-pdfs-section');
    const scannedResults = document.getElementById('scanned-results');
    const clearScansButton = document.getElementById('clear-scans');
    const scanAllButton = document.getElementById('scan-all-docs');
    
    // Function to show the scanned PDFs section if it's hidden
    function showScannedSection() {
        if (scannedSection.style.display === 'none') {
            scannedSection.style.display = 'block';
            
            // Smooth scroll to the scanned section
            scannedSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
    
    // Function to add a new scan result card
    function addScanResult(fileName, filePath, content, isError = false) {
        // Create a unique ID for this scan result
        const resultId = 'scan-' + Date.now();
        
        // Get current time for timestamp
        const timestamp = new Date().toLocaleString();
        
        // Create a new result card
        const resultCard = document.createElement('div');
        resultCard.className = 'scan-result-card';
        resultCard.id = resultId;
        
        // Set card content
        let cardContent = '';
        if (isError) {
            cardContent = `
                <div class="scan-result-header">
                    <h3 class="scan-result-title">Error scanning ${fileName}</h3>
                    <button class="remove-scan-btn" data-id="${resultId}">×</button>
                </div>
                <div class="scan-result-content error-message">${content}</div>
                <div class="timestamp">${timestamp}</div>
            `;
        } else {
            cardContent = `
                <div class="scan-result-header">
                    <h3 class="scan-result-title">
                        <a href="#" class="pdf-link" data-path="${filePath}">${fileName}</a>
                    </h3>
                    <button class="remove-scan-btn" data-id="${resultId}">×</button>
                </div>
                <div class="scan-result-content">${content}</div>
                <div class="timestamp">${timestamp}</div>
            `;
        }
        
        resultCard.innerHTML = cardContent;
        
        // Add to the results container
        scannedResults.prepend(resultCard);
        
        // Add event listener to remove button
        const removeButton = resultCard.querySelector('.remove-scan-btn');
        removeButton.addEventListener('click', function() {
            const cardId = this.getAttribute('data-id');
            const card = document.getElementById(cardId);
            if (card) {
                card.remove();
                
                // Hide section if no results left
                if (scannedResults.children.length === 0) {
                    scannedSection.style.display = 'none';
                }
            }
        });
        
        // Add event listener to the PDF link to scroll to the file in the list
        const pdfLink = resultCard.querySelector('.pdf-link');
        if (pdfLink) {
            pdfLink.addEventListener('click', function(e) {
                e.preventDefault();
                const path = this.getAttribute('data-path');
                const fileElement = document.querySelector(`li[data-pdf="${path}"]`);
                
                if (fileElement) {
                    // Expand the file list if it's collapsed
                    const filesContainer = document.getElementById('files-container');
                    if (filesContainer.classList.contains('collapsed')) {
                        const toggleButton = document.getElementById('toggle-files');
                        toggleButton.click();
                    }
                    
                    // Highlight the file item
                    fileElement.classList.add('highlight-file');
                    setTimeout(() => {
                        fileElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 300);
                    
                    // Remove highlight after a few seconds
                    setTimeout(() => {
                        fileElement.classList.remove('highlight-file');
                    }, 3000);
                }
            });
        }
        
        // Show the section if it was hidden
        showScannedSection();
    }
    
    // Add event listener to clear all button
    if (clearScansButton) {
        clearScansButton.addEventListener('click', function() {
            scannedResults.innerHTML = '';
            scannedSection.style.display = 'none';
        });
    }
    
    // Function to scan a document (PDF or Word)
    function scanDocument(filePath, documentType) {
        return new Promise((resolve, reject) => {
            const fileName = filePath.split('/').pop();
            const endpoint = documentType === 'pdf' ? '/agents/pdf/scan' : '/agents/word/scan';
            
            // Make API call to scan the document
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ file_path: filePath })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    addScanResult(fileName, filePath, data.error, true);
                    resolve({ success: false, file: fileName });
                } else {
                    // Display summary and JSON data in tabs
                    const resultId = 'result-' + Date.now();
                    const jsonString = JSON.stringify(data.json_data, null, 2);
                    const docIcon = documentType === 'pdf' ? '📕' : '📄';
                    const docType = documentType === 'pdf' ? 'PDF' : 'Word';
                    
                    const formattedContent = `
                        <div class="pdf-result-tabs" id="${resultId}">
                            <div class="doc-type-indicator">${docIcon} ${docType}</div>
                            <div class="tab-buttons">
                                <button class="tab-btn active" data-tab="summary-${resultId}">Summary</button>
                                <button class="tab-btn" data-tab="json-${resultId}">JSON Data</button>
                            </div>
                            <div class="tab-content">
                                <div class="tab-pane active" id="summary-${resultId}">
                                    <div class="pdf-text">${data.summary}</div>
                                </div>
                                <div class="tab-pane" id="json-${resultId}">
                                    <div class="json-data-container">
                                        <pre class="json-data">${syntaxHighlight(jsonString)}</pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    addScanResult(fileName, filePath, formattedContent);
                    
                    // Add event listeners for tabs
                    setTimeout(() => {
                        const tabsContainer = document.getElementById(resultId);
                        if (tabsContainer) {
                            const tabButtons = tabsContainer.querySelectorAll('.tab-btn');
                            tabButtons.forEach(button => {
                                button.addEventListener('click', function() {
                                    // Remove active class from all buttons and panes
                                    const parent = this.closest('.pdf-result-tabs');
                                    parent.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                                    parent.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
                                    
                                    // Add active class to clicked button and corresponding pane
                                    this.classList.add('active');
                                    const tabName = this.getAttribute('data-tab');
                                    parent.querySelector(`#${tabName}`).classList.add('active');
                                });
                            });
                        }
                    }, 100);
                    
                    resolve({ success: true, file: fileName });
                }
            })
            .catch(error => {
                addScanResult(fileName, filePath, `Error: ${error.message}`, true);
                resolve({ success: false, file: fileName });
            });
        });
    }
    
    // Function to scan a PDF document
    function scanPdf(filePath) {
        return scanDocument(filePath, 'pdf');
    }
    
    // Function to scan a Word document
    function scanWord(filePath) {
        return scanDocument(filePath, 'word');
    }
    
    // Add click handler to scan all documents button
    if (scanAllButton) {
        scanAllButton.addEventListener('click', async function() {
            // Find all scannable documents in the list
            const scannableItems = document.querySelectorAll('li[data-scannable]');
            
            if (scannableItems.length === 0) {
                alert('No PDF or Word documents found to scan.');
                return;
            }
            
            // Disable the button during processing
            scanAllButton.disabled = true;
            scanAllButton.textContent = `Scanning ${scannableItems.length} documents...`;
            
            // Show progress in the scanned section
            const progressId = 'scan-progress-' + Date.now();
            const progressCard = document.createElement('div');
            progressCard.className = 'scan-result-card progress-card';
            progressCard.id = progressId;
            progressCard.innerHTML = `
                <div class="scan-result-header">
                    <h3 class="scan-result-title">Scanning ${scannableItems.length} document(s)...</h3>
                </div>
                <div class="scan-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 0%"></div>
                    </div>
                    <div class="progress-text">0/${scannableItems.length} complete</div>
                </div>
            `;
            
            scannedResults.prepend(progressCard);
            showScannedSection();
            
            // Process documents one by one to avoid overwhelming the server
            let completedCount = 0;
            
            for (const item of scannableItems) {
                const filePath = item.getAttribute('data-scannable');
                const isPdf = item.hasAttribute('data-pdf');
                const isWord = item.hasAttribute('data-word');
                
                if (isPdf) {
                    await scanPdf(filePath);
                } else if (isWord) {
                    await scanWord(filePath);
                }
                
                completedCount++;
                
                // Update progress
                const progressFill = progressCard.querySelector('.progress-fill');
                const progressText = progressCard.querySelector('.progress-text');
                const percentage = Math.round((completedCount / scannableItems.length) * 100);
                
                progressFill.style.width = `${percentage}%`;
                progressText.textContent = `${completedCount}/${scannableItems.length} complete`;
                
                // If this is the last one, remove the progress card after a delay
                if (completedCount === scannableItems.length) {
                    setTimeout(() => {
                        progressCard.remove();
                    }, 1500);
                }
            }
            
            // Re-enable the button
            scanAllButton.disabled = false;
            scanAllButton.textContent = 'Scan All Documents';
        });
    }
}); 