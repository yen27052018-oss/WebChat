// ERROR
const showError = (error, message) => {
    error.textContent = message
    error.style.display = 'block'
}

const hideError = (error) => {
    error.textContent = ''
    error.style.display = 'none'
}

// LOGIN
const validateLogin = (
    username,
    password,
    error
) => {
    const usernameValue = username.value.trim()
    const passwordValue = password.value.trim()

    hideError(error)

    // Kiểm tra bỏ trống trước
    if (usernameValue === '' || passwordValue === '') {
        showError(
            error,
            'Vui lòng nhập đầy đủ'
        )
        return false
    }

    // Kiểm tra độ dài mật khẩu
    if (passwordValue.length < 6) {
        showError(
            error,
            'Mật khẩu phải có ít nhất 6 ký tự'
        )
        return false
    }

    return true
}

// SIGNUP
const validateSignup = (
    username,
    password,
    confirmPassword,
    error
) => {
    const usernameValue = username.value.trim()
    const passwordValue = password.value.trim()
    const confirmPasswordValue =
        confirmPassword.value.trim()

    hideError(error)

    // Kiểm tra bỏ trống
    if (
        usernameValue === '' ||
        passwordValue === '' ||
        confirmPasswordValue === ''
    ) {
        showError(
            error,
            'Vui lòng nhập đầy đủ'
        )
        return false
    }

    // Kiểm tra độ dài mật khẩu
    if (passwordValue.length < 6) {
        showError(
            error,
            'Mật khẩu phải có ít nhất 6 ký tự'
        )
        return false
    }

    // Kiểm tra xác nhận mật khẩu
    if (passwordValue !== confirmPasswordValue) {
        showError(
            error,
            'Mật khẩu xác nhận không khớp'
        )
        return false
    }

    return true
}

// CHANGE PASSWORD
const validateChangePassword = (
    currentPassword,
    newPassword,
    confirmPassword,
    error
) => {
    const currentValue =currentPassword.value.trim()

    const newValue =newPassword.value.trim()

    const confirmValue =confirmPassword.value.trim()

    hideError(error)

    if (
        currentValue === '' &&
        newValue === '' &&
        confirmValue === ''
    ) {
        showError(
            error,
            'Vui lòng nhập đầy đủ để đổi'
        )
        return false
    }

    if (currentValue === '') {
        showError(
            error,
            'Vui lòng nhập mật khẩu hiện tại'
        )
        return false
    }

    if (newValue === '' && confirmValue === '') {
        showError(
            error,
            'Vui lòng nhập mật khẩu mới và xác nhận'
        )
        return false
    }

    if (newValue === '') {
        showError(
            error,
            'Vui lòng nhập mật khẩu mới'
        )
        return false
    }

    if (confirmValue === '') {
        showError(
            error,
            'Vui lòng nhập xác nhận mật khẩu mới'
        )
        return false
    }

    if (newValue.length < 6) {
        showError(
            error,
            'Mật khẩu phải có ít nhất 6 ký tự'
        )
        return false
    }

    if (newValue !== confirmValue) {
        showError(
            error,
            'Mật khẩu xác nhận không khớp'
        )
        return false
    }

    return true
}

// CLEAR ERROR
const clearErrorOnInput = (
    inputs,
    error
) => {
    inputs.forEach((input) => {
        input.oninput = () => {
            hideError(error)
        }
    })
}