document.addEventListener('DOMContentLoaded', function() {
    const fetchDigestButton = document.getElementById('fetchDigest');
    const emailCountInput = document.getElementById('emailCount');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const progressMessage = document.getElementById('progressMessage');
    const errorMessage = document.getElementById('errorMessage');
    const emailResults = document.getElementById('emailResults');

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }

    function updateProgress(message) {
        progressMessage.textContent = message;
    }

    function formatNewsletterDigest(digest) {
        // Configure marked options
        marked.setOptions({
            breaks: true,
            gfm: true,
            sanitize: true
        });
        
        // Convert markdown to HTML
        const htmlContent = marked.parse(digest);
        
        return `
            <div class="digest-content">
                ${htmlContent}
            </div>
        `;
    }

    fetchDigestButton.addEventListener('click', async function() {
        const emailCount = parseInt(emailCountInput.value);
        
        if (emailCount < 1 || emailCount > 100) {
            showError('Please enter a number between 1 and 100');
            return;
        }

        // Show loading indicator and disable button
        loadingIndicator.style.display = 'block';
        emailResults.style.display = 'none';
        errorMessage.style.display = 'none';
        fetchDigestButton.disabled = true;

        try {
            updateProgress('Starting newsletter digest generation...');
            console.log('Sending request to generate newsletter digest...');
            
            const response = await fetch('http://localhost:5000/generate-digest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    emailCount: emailCount
                })
            });

            console.log('Response received:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Raw data received:', JSON.stringify(data, null, 2));
            console.log('Digest content:', data.digest);

            if (data.status === 'success') {
                // Display newsletter digest
                emailResults.innerHTML = formatNewsletterDigest(data.digest);
                emailResults.style.display = 'block';
            } else {
                showError(data.message || 'Failed to generate newsletter digest');
            }
        } catch (error) {
            console.error('Error:', error);
            showError('Error generating newsletter digest: ' + error.message);
        } finally {
            loadingIndicator.style.display = 'none';
            fetchDigestButton.disabled = false;
        }
    });
}); 