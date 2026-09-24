const $ = document.querySelector.bind(document)

const API_URL =
    window.CHAT_WATCH_API_URL ||
    (
        window.location.port === '5000'
            ? window.location.origin
            : `${window.location.protocol}//${window.location.hostname}:5000`
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