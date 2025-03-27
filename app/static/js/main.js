document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const ratioSlider = document.getElementById('summary-ratio');
    const ratioValue = document.getElementById('ratio-value');
    const loadingSection = document.getElementById('loading');
    const resultsSection = document.getElementById('results');
    const errorSection = document.getElementById('error');
    
    // Update ratio value display
    ratioSlider.addEventListener('input', function() {
        ratioValue.textContent = this.value + '%';
    });
    
    // Handle form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Hide previous results and errors
        resultsSection.classList.add('hidden');
        errorSection.classList.add('hidden');
        
        // Show loading spinner
        loadingSection.classList.remove('hidden');
        
        // Create form data
        const formData = new FormData(form);
        
        // Convert slider value from percentage to decimal
        const ratioPercent = formData.get('ratio');
        formData.set('ratio', ratioPercent / 100);
        
        // Send request
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading spinner
            loadingSection.classList.add('hidden');
            
            if (data.error) {
                // Show error
                document.getElementById('error-message').textContent = data.error;
                errorSection.classList.remove('hidden');
            } else {
                // Show results
                document.getElementById('summary-text').textContent = data.summary;
                document.getElementById('original-count').textContent = data.original_word_count;
                document.getElementById('summary-count').textContent = data.word_count;
                document.getElementById('reduction').textContent = data.reduction_percentage;
                resultsSection.classList.remove('hidden');
            }
        })
        .catch(error => {
            // Hide loading spinner
            loadingSection.classList.add('hidden');
            
            // Show error
            document.getElementById('error-message').textContent = 'An error occurred. Please try again.';
            errorSection.classList.remove('hidden');
            console.error('Error:', error);
        });
    });
});
