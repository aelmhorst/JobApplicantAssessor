document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('application-form');
    const essays = ['essay1', 'essay2', 'essay3'];

    essays.forEach(essayId => {
        const textarea = document.getElementById(essayId);
        const counter = document.getElementById(`${essayId}-counter`);

        if (textarea && counter) {
            textarea.addEventListener('input', function() {
                const remainingChars = 10000 - this.value.length;
                counter.textContent = `${this.value.length}/10000 characters`;
                
                if (remainingChars < 0) {
                    counter.classList.add('text-danger');
                } else {
                    counter.classList.remove('text-danger');
                }
            });

            // Trigger the input event to initialize the counter
            textarea.dispatchEvent(new Event('input'));
        }
    });

    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;

            essays.forEach(essayId => {
                const textarea = document.getElementById(essayId);
                if (textarea.value.length < 100 || textarea.value.length > 10000) {
                    isValid = false;
                    const errorSpan = document.createElement('span');
                    errorSpan.className = 'text-danger';
                    errorSpan.textContent = 'Essay must be between 100 and 10000 characters.';
                    textarea.parentNode.appendChild(errorSpan);
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    }
});
