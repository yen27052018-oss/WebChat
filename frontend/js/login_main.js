const $ = document.querySelector.bind(document)

const LOGIN_STORAGE_KEY = 'CHAT_WATCH_LOGIN'
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
const checkbox = $('#checkbox')

const loginError = $('#loginError')

const btnSignin = $('.signin_act')
const forgotPassword = $('.form-option__link')
const signupOption = $('.signup-option')

const eyeSlash = $('.input_icon.unhide_password')
const eye = $('.input_icon.hide_password')


const login = {

    isLoggedIn: false,

    config:
        JSON.parse(
            localStorage.getItem(LOGIN_STORAGE_KEY)
        ) || {},


    setConfig: function (key, value) {

        this.config[key] = value

        localStorage.setItem(
            LOGIN_STORAGE_KEY,
            JSON.stringify(this.config)
        )
    },


    handleEvents: function () {

        const _this = this


        // =========================
        // XÓA LỖI KHI NHẬP
        // =========================

        clearErrorOnInput(
            [username, password],
            loginError
        )


        // =========================
        // ĐĂNG NHẬP
        // =========================

        form.onsubmit = async function (e) {

            e.preventDefault()


            const usernameValue =
                username.value.trim()

            const passwordValue =
                password.value.trim()


            // =========================
            // KIỂM TRA DỮ LIỆU
            // =========================

            if (
                !validateLogin(
                    username,
                    password,
                    loginError
                )
            ) {
                return
            }


            // =========================
            // GỌI API LOGIN
            // =========================

            try {

                const response = await fetch(
                    `${API_URL}/api/login`,
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


                // =========================
                // LOGIN THẤT BẠI
                // =========================

                if (!result.success) {

                    showError(
                        loginError,
                        result.message
                    )

                    return
                }


                // =========================
                // LOGIN THÀNH CÔNG
                // =========================

                _this.isLoggedIn = true


                _this.setConfig(
                    'isLoggedIn',
                    true
                )


                _this.setConfig(
                    'user',
                    result.user
                )


                // =========================
                // NHỚ TÊN ĐĂNG NHẬP
                // =========================

                if (checkbox.checked) {

                    _this.setConfig(
                        'username',
                        usernameValue
                    )

                } else {

                    delete _this.config.username

                    localStorage.setItem(
                        LOGIN_STORAGE_KEY,
                        JSON.stringify(
                            _this.config
                        )
                    )
                }


                // =========================
                // THÔNG BÁO
                // =========================

                // alert(
                //     `Đăng nhập thành công!\nXin chào ${result.user.username}`
                // )


                // =========================
                // CHUYỂN TRANG
                // =========================

                window.location.href =
                    './chatApp.html'

            } catch (error) {

                console.error(error)

                // alert(
                //     'Không thể kết nối đến máy chủ'
                // )
            }
        }
    },


    // =========================
    // LOAD CONFIG
    // =========================

    loadConfig: function () {

        if (this.config.username) {

            username.value =
                this.config.username
        }


        if (this.config.isLoggedIn) {

            this.isLoggedIn =
                this.config.isLoggedIn
        }
    },


    start: function () {

        this.handleEvents()

        this.loadConfig()
    }
}


login.start()