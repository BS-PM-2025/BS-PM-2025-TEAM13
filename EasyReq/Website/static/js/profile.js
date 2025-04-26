document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('updateProfileForm').addEventListener('submit', function(event) {
        event.preventDefault();

        const newEmail = document.getElementById('new_email').value;
        const newPassword = document.getElementById('new_password').value;

        const formData = new FormData();
        formData.append('new_email', newEmail);
        formData.append('new_password', newPassword);

        fetch("{% url 'profile' %}", {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Profile updated successfully!');
                document.querySelector('input[name="email"]').value = newEmail;
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error with the request.');
        });
    });
});
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
        });