document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('upload-form');
    const resultSection = document.getElementById('result-section');
    const errorSection = document.getElementById('error-section');
    const analysisText = document.getElementById('analysis-text');
    const errorMessage = document.querySelector('.error-message');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Reset previous results and errors
        resultSection.style.display = 'none';
        errorSection.style.display = 'none';

        const fileInput = document.getElementById('excel-file');
        const file = fileInput.files[0];

        if (!file) {
            showError('Please select a file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/excel-processor/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                analysisText.textContent = data.analysis;
                resultSection.style.display = 'block';
            } else {
                showError(data.error || 'An error occurred while processing the file');
            }
        } catch (error) {
            showError('An error occurred while uploading the file');
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
    }
}); 