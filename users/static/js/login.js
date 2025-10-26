// Masking functions
function maskEmail(email) {
    if (!email || !email.includes('@')) return email;
    const [name, domain] = email.split('@');
    const maskLength = Math.floor(name.length * 0.7);
    const masked = '*'.repeat(maskLength) + name.slice(maskLength);
    return masked + '@' + domain;
}

function maskPhone(phone) {
    if (!phone || phone.length < 4) return phone;
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 4) return phone;
    return '*'.repeat(digits.length - 3) + digits.slice(-3);
}

// Modal handling
document.addEventListener('DOMContentLoaded', function() {
    const deliveryMethodModal = document.getElementById('deliveryMethodModal');
    const otpModal = document.getElementById('otpModal');
    
    // Apply masking to displayed values
    const emailDisplay = document.getElementById('emailDisplay');
    const phoneDisplay = document.getElementById('phoneDisplay');
    
    if (emailDisplay && emailDisplay.dataset.email) {
        emailDisplay.textContent = maskEmail(emailDisplay.dataset.email);
    }
    if (phoneDisplay && phoneDisplay.dataset.phone) {
        phoneDisplay.textContent = maskPhone(phoneDisplay.dataset.phone);
    }

    // Handle successful login response
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(loginForm);
            
            fetch(loginForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update email and phone displays with masked values
                    const emailDisplay = document.getElementById('emailDisplay');
                    const phoneDisplay = document.getElementById('phoneDisplay');
                    
                    if (emailDisplay) {
                        emailDisplay.dataset.email = data.email;
                        emailDisplay.textContent = maskEmail(data.email);
                    }
                    if (phoneDisplay) {
                        phoneDisplay.dataset.phone = data.phone;
                        phoneDisplay.textContent = maskPhone(data.phone);
                    }
                    
                    // Show delivery method modal
                    deliveryMethodModal.classList.remove('hidden');
                    deliveryMethodModal.classList.add('flex');
                } else {
                    // Show error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'rounded-md bg-red-500 p-4 mt-4';
                    errorDiv.innerHTML = `
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <i class="fas fa-exclamation-circle text-white"></i>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm text-white">${data.error}</p>
                            </div>
                        </div>
                    `;
                    loginForm.appendChild(errorDiv);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
});

// OTP Timer
let otpTimer;
let timeLeft = 120; // 2 minutes in seconds

function startOTPTimer() {
    const timerDisplay = document.getElementById('otpTimer');
    timeLeft = 120;
    
    clearInterval(otpTimer);
    otpTimer = setInterval(() => {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `Time remaining: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(otpTimer);
            timerDisplay.textContent = 'OTP expired';
            timerDisplay.classList.remove('text-blue-400');
            timerDisplay.classList.add('text-red-400');
        }
        timeLeft--;
    }, 1000);
}

// Delivery method selection
function selectDeliveryMethod(method) {
    // Hide delivery method modal immediately
    const deliveryMethodModal = document.getElementById('deliveryMethodModal');
    deliveryMethodModal.classList.add('hidden');
    deliveryMethodModal.classList.remove('flex');
    
    // Show OTP modal immediately
    const otpModal = document.getElementById('otpModal');
    otpModal.classList.remove('hidden');
    otpModal.classList.add('flex');
    
    // Start the OTP timer
    startOTPTimer();

    // Send OTP request
    fetch('/accounts/send-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            delivery_method: method
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            // Show error in OTP modal
            const errorDiv = document.createElement('div');
            errorDiv.className = 'rounded-md bg-red-500 p-4 mt-4';
            errorDiv.innerHTML = `
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-circle text-white"></i>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-white">${data.error}</p>
                    </div>
                </div>
            `;
            otpModal.querySelector('.modal-content').appendChild(errorDiv);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Show error in OTP modal
        const errorDiv = document.createElement('div');
        errorDiv.className = 'rounded-md bg-red-500 p-4 mt-4';
        errorDiv.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <i class="fas fa-exclamation-circle text-white"></i>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-white">An error occurred while sending OTP. Please try again.</p>
                </div>
            </div>
        `;
        otpModal.querySelector('.modal-content').appendChild(errorDiv);
    });
}

// OTP verification
function verifyOTP() {
    const otp = document.getElementById('otpInput').value;
    
    if (!otp || otp.length !== 6) {
        alert('Please enter a valid 6-digit OTP');
        return;
    }
    
    fetch('/accounts/verify-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            otp: otp
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Server response:', data); // Debug log
        if (data.success) {
            console.log('Redirecting to:', data.redirect_url || '/site/topics/'); // Debug log
            window.location.href = data.redirect_url || '/dashboard/';
        } else {
            alert(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while verifying OTP');
    });
}

// Resend OTP
function resendOTP() {
    // Hide OTP modal
    const otpModal = document.getElementById('otpModal');
    otpModal.classList.add('hidden');
    otpModal.classList.remove('flex');
    
    // Show delivery method modal
    const deliveryMethodModal = document.getElementById('deliveryMethodModal');
    deliveryMethodModal.classList.remove('hidden');
    deliveryMethodModal.classList.add('flex');
    
    // Reset delivery method buttons
    const buttons = deliveryMethodModal.querySelectorAll('button');
    buttons.forEach(button => {
        button.disabled = false;
        // Reset email button
        if (button.querySelector('.fa-envelope')) {
            button.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-envelope text-blue-400 mr-3"></i>
                    <div class="text-left">
                        <span class="text-white block">Email</span>
                        <span id="emailDisplay" class="text-gray-400 text-sm"></span>
                    </div>
                </div>
                <i class="fas fa-chevron-right text-gray-400"></i>
            `;
        }
        // Reset phone button
        if (button.querySelector('.fa-phone')) {
            button.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-phone text-blue-400 mr-3"></i>
                    <div class="text-left">
                        <span class="text-white block">Phone</span>
                        <span id="phoneDisplay" class="text-gray-400 text-sm"></span>
                    </div>
                </div>
                <i class="fas fa-chevron-right text-gray-400"></i>
            `;
        }
    });
    
    // Remove any error messages
    const errorMessages = deliveryMethodModal.querySelectorAll('.rounded-md.bg-red-500');
    errorMessages.forEach(error => error.remove());
    
    // Re-apply masking to the email and phone displays
    const emailDisplay = document.getElementById('emailDisplay');
    const phoneDisplay = document.getElementById('phoneDisplay');
    
    if (emailDisplay && emailDisplay.dataset.email) {
        emailDisplay.textContent = maskEmail(emailDisplay.dataset.email);
    }
    if (phoneDisplay && phoneDisplay.dataset.phone) {
        phoneDisplay.textContent = maskPhone(phoneDisplay.dataset.phone);
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
} 