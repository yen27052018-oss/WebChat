// Đã đăng nhập rồi thì vào thẳng trang chat
try {
    const savedLogin = JSON.parse(localStorage.getItem('CHAT_WATCH_LOGIN')) || {}

    if (savedLogin.isLoggedIn && savedLogin.user) {
        window.location.replace('./chatApp.html')
    }
} catch (error) {

    showServerError(signupError, error)
}

const $ = document.querySelector.bind(document)

const API_URL =
    window.CHAT_WATCH_API_URL ||
    (
        // Live Server (5500/5501) thì backend ở cổng 5000, còn lại dùng chính địa chỉ đang mở
        ['5500', '5501'].includes(window.location.port)
            ? `${window.location.protocol}//${window.location.hostname}:5000`
            : window.location.origin
    )

const form = $('.form')

const username = $('#username')
const password = $('#password')
const confirmPassword = $('#confirm-password')

const signupError = $('#signupError')

const app = {

    handleEvents: function () {

        clearErrorOnInput(
            [
                username,
                password,
                confirmPassword
            ],
            signupError
        )

        form.onsubmit = async function (e) {

            e.preventDefault()

            const usernameValue =
                username.value.trim()

            const passwordValue =
                password.value.trim()

            if (
                !validateSignup(
                    username,
                    password,
                    confirmPassword,
                    signupError
                )
            ) {
                return
            }

            try {

                const response = await fetch(
                    `${API_URL}/api/register`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type':
                                'application/json'
                        },
                        body: JSON.stringify({
                            username: usernameValue,
                            password: passwordValue
                        })
                    }
                )

                const result =
                    await response.json()

                if (!result.success) {

                    showError(
                        signupError,
                        result.message
                    )

                    return
                }

                alert(
                    `Đăng ký thành công!\nMã người dùng: ${result.user_code}`
                )

                window.location.href =
                    './login.html'

            } catch (error) {

                console.error(error)

                alert(
                    'Không thể kết nối đến máy chủ'
                )
            }
        }
    },

    start: function () {
        this.handleEvents()
    }
}

app.start()