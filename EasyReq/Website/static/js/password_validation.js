document.addEventListener('DOMContentLoaded', function() {
    // Track the visibility state of the password
    let password1Visible = false;
    let password2Visible = false;

    const togglePassword1 = document.getElementById('toggle-password1');
    const password1 = document.getElementById('password1');
    const togglePassword2 = document.getElementById('toggle-password2');
    const password2 = document.getElementById('password2');

    // Toggle password visibility for first password field
    if (togglePassword1 && password1) {
        togglePassword1.addEventListener('click', function() {
            // Toggle the password visibility state
            password1Visible = !password1Visible;

            // Update the input type based on the visibility state
            if (password1Visible) {
                password1.type = 'text';
                this.classList.remove('bx-lock-alt');
                this.classList.add('bx-lock-open-alt');
            } else {
                password1.type = 'password';
                this.classList.remove('bx-lock-open-alt');
                this.classList.add('bx-lock-alt');
            }
        });
    }

    // Toggle password visibility for second password field
    if (togglePassword2 && password2) {
        togglePassword2.addEventListener('click', function() {
            // Toggle the password visibility state
            password2Visible = !password2Visible;

            // Update the input type based on the visibility state
            if (password2Visible) {
                password2.type = 'text';
                this.classList.remove('bx-lock-alt');
                this.classList.add('bx-lock-open-alt');
            } else {
                password2.type = 'password';
                this.classList.remove('bx-lock-open-alt');
                this.classList.add('bx-lock-alt');
            }
        });
    }

    // Password validation
    const passwordField = document.getElementById('password1');
    const confirmPasswordField = document.getElementById('password2');
    const passwordMatchError = document.getElementById('password-match-error');

    if (passwordField) {
        passwordField.addEventListener('input', function() {
            validatePassword(this.value);

            // Check match only if confirmation field has content
            if (confirmPasswordField && confirmPasswordField.value) {
                checkPasswordMatch(passwordField.value, confirmPasswordField.value, passwordMatchError);
            }
        });
    }

    if (confirmPasswordField && passwordMatchError) {
        confirmPasswordField.addEventListener('input', function() {
            checkPasswordMatch(passwordField.value, this.value, passwordMatchError);
        });
    }

    function validatePassword(password) {
        // Password validation checks
        const isLongEnough = password.length >= 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);

        // Update UI indicators
        updateRequirement('length', isLongEnough);
        updateRequirement('uppercase', hasUpperCase);
        updateRequirement('lowercase', hasLowerCase);
        updateRequirement('number', hasNumber);
        updateRequirement('special', hasSpecial);
    }

    function checkPasswordMatch(password, confirmPassword, errorElement) {
        if (password === confirmPassword) {
            errorElement.style.display = 'none';
            return true;
        } else {
            errorElement.style.display = 'block';
            return false;
        }
    }

    function updateRequirement(id, isValid) {
        const requirement = document.getElementById(id);
        if (requirement) {
            if (isValid) {
                requirement.classList.add('valid');
            } else {
                requirement.classList.remove('valid');
            }
        }
    }

    // Prevent form submission if passwords don't match
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const password = document.getElementById('password1').value;
            const confirmPassword = document.getElementById('password2').value;

            if (password !== confirmPassword) {
                event.preventDefault(); // Prevent form submission
                document.getElementById('password-match-error').style.display = 'block';
            }
        });
    }

    // Add similar validation for reset password form if present
    const resetPasswordForm = document.querySelector('form input[name="new_password1"]');
    if (resetPasswordForm) {
        const newPassword1 = document.getElementById('new_password1');
        const newPassword2 = document.querySelector('input[name="new_password2"]');
        const resetPasswordMatchError = document.getElementById('reset-password-match-error');

        if (newPassword1 && newPassword2 && resetPasswordMatchError) {
            newPassword1.addEventListener('input', function() {
                validatePassword(this.value);
                if (newPassword2.value) {
                    checkPasswordMatch(newPassword1.value, newPassword2.value, resetPasswordMatchError);
                }
            });

            newPassword2.addEventListener('input', function() {
                checkPasswordMatch(newPassword1.value, this.value, resetPasswordMatchError);
            });
        }
    }
});