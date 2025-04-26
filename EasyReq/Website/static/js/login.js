
document.addEventListener('DOMContentLoaded', function() {
            const toggleIcon = document.querySelector('.password-toggle-icon');
            const passwordField = document.getElementById('password');

            toggleIcon.addEventListener('click', function() {
                if (passwordField.type === 'password') {
                    passwordField.type = 'text';
                    toggleIcon.classList.remove('bxs-lock-alt');
                    toggleIcon.classList.add('bxs-lock-open-alt');
                } else {
                    passwordField.type = 'password';
                    toggleIcon.classList.remove('bxs-lock-open-alt');
                    toggleIcon.classList.add('bxs-lock-alt');
                }
            });