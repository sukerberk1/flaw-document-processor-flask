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
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            if (fileName) {
                const submitBtn = this.closest('form').querySelector('button[type="submit"]');
                submitBtn.textContent = `Upload ${fileName}`;
            }
        });
    }
    
    // Add a subtle animation to file list items
    const fileItems = document.querySelectorAll('.files-list li');
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