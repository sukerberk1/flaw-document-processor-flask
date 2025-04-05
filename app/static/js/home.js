// Handle file upload UI and flash messages
document.addEventListener('DOMContentLoaded', function () {
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
}); 