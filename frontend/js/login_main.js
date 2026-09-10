const $ = document.querySelector.bind(document)
const $$ = document.querySelectorAll.bind(document)

const LOGIN_STORAGE_KEY = 'CHAT_WATCH_LOGIN'

const form = $('.form')
const username = $('#username')
const password = $('#password')
const checkbox = $('#checkbox')

const errors = $$('.error')

const usernameGroup = username.closest('.form_group')
const passwordGroup = password.closest('.form_group')

const errorUsername = errors[0]
const errorPassword = errors[1]
const btnSignin = $('.signin_act')
const forgotPassword = $('.form-option__link')
const signupOption = $('.signup-option')

const eyeSlash = $('.input_icon.unhide_password')
const eye = $('.input_icon.hide_password')

const login ={
    isLoggedIn: false,
    config:JSON.parse(localStorage.getItem(LOGIN_STORAGE_KEY)) || {},

    setConfig: function(key, value){
        this.config[key] = value

        localStorage.setItem(
            LOGIN_STORAGE_KEY,
            JSON.stringify(this.config)
        )
    },

    handleEvents: function(){
        // Hiện pass 
        const _this = this
        eyeSlash.onclick = function(){
            password.type = 'text'
            eyeSlash.classList.add('hide')
            eye.classList.remove('hide')
        }
        // Ẩn pass 
        eye.onclick = function(){
            password.type = 'password'
            eye.classList.add('hide')
            eyeSlash.classList.remove('hide')
        }

        username.oninput = function(){

            if(username.value.trim() !== ''){

                usernameGroup.classList.remove('error')

                errorUsername.textContent = ''
            }
        }


        // nhập pass 

        password.oninput = function(){

            if(password.value.trim() !== ''){

                passwordGroup.classList.remove('error')

                errorPassword.textContent = ''
            }
        }


        // đăng nhập

        form.onsubmit = function(e){

            e.preventDefault()

            const usernameValue = username.value.trim()
            const passwordValue = password.value.trim()


            // kiểm tra để trống thông tin 

            if(usernameValue === '' || passwordValue === ''){

                if(usernameValue === ''){

                    usernameGroup.classList.add('error')

                    errorUsername.textContent =
                        'Vui lòng nhập đầy đủ'

                }

                if(passwordValue === ''){

                    passwordGroup.classList.add('error')

                    errorPassword.textContent =
                        'Vui lòng nhập đầy đủ'

                }

                return
            }


            // xóa lỗi để trống

            usernameGroup.classList.remove('error')
            passwordGroup.classList.remove('error')

            errorUsername.textContent = ''
            errorPassword.textContent = ''


            // chạy thử

            const testUsername = 'yen'
            const testPassword = '123456'


            if(
                usernameValue === testUsername &&
                passwordValue === testPassword
            ){

                _this.isLoggedIn = true

                _this.setConfig(
                    'isLoggedIn',
                    true
                )


                if(checkbox.checked){

                    _this.setConfig(
                        'username',
                        usernameValue
                    )

                }else{

                    delete _this.config.username

                    localStorage.setItem(
                        LOGIN_STORAGE_KEY,
                        JSON.stringify(_this.config)
                    )
                }


                alert('Đăng nhập thành công!')

                window.location.href = './chat.html' /*nếu đăng nhập thành công sẽ đưa vào trang để chat*/

            }else{

                usernameGroup.classList.add('error')
                passwordGroup.classList.add('error')

                errorUsername.textContent =
                    'Tên người dùng hoặc mật khẩu không tồn tại'

                errorPassword.textContent =
                    'Tên người dùng hoặc mật khẩu không tồn tại'
            }
        }
    },


    // =========================
    // LOAD CONFIG
    // =========================

    loadConfig: function(){

        if(this.config.username){

            username.value = this.config.username
        }

        if(this.config.isLoggedIn){

            this.isLoggedIn = this.config.isLoggedIn
        }
    },

    start: function(){
        this.handleEvents();
        this.loadConfig();
    }
}

login.start()