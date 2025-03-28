document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('upload-form');
    const resultSection = document.getElementById('result-section');
    const errorSection = document.getElementById('error-section');
    const summaryText = document.getElementById('summary-text');
    const errorMessage = document.querySelector('.error-message');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        // Reset previous results
        resultSection.style.display = 'none';
        errorSection.style.display = 'none';

        const fileInput = document.getElementById('pdf-file');
        const file = fileInput.files[0];

        if (!file) {
            showError('Please select a PDF file');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/pdf-processor/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showResult(data.summary);
            } else {
                showError(data.error || 'An error occurred while processing the PDF');
            }
        } catch (error) {
            showError('An error occurred while uploading the file');
        }
    });

    function showResult(summary) {
        summaryText.textContent = summary;
        resultSection.style.display = 'block';
        errorSection.style.display = 'none';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        resultSection.style.display = 'none';
    }
}); 