const $ = document.querySelector.bind(document)
const $$ = document.querySelectorAll.bind(document)

const REGISTER_STORAGE_KEY = 'CHAT_WATCH_REGISTER'

const form = $('.form')

const username = $('#username')
const password = $('#password')
const confirmPassword = $('#confirm-password')

const checkbox = $('#checkbox')

const usernameGroup = username.closest('.form_group')
const passwordGroup = password.closest('.form_group')
const confirmPasswordGroup = confirmPassword.closest('.form_group')

const errorUsername = usernameGroup.querySelector('.error')
const errorPassword = passwordGroup.querySelector('.error')
const errorConfirmPassword = confirmPasswordGroup.querySelector('.error')

const eyeSlash = $$('.fa-eye-slash')
const eye = $$('.fa-eye')


// APP
const app = {

    config: JSON.parse(
        localStorage.getItem(REGISTER_STORAGE_KEY)
    ) || {},

    setConfig: function(key, value){

        this.config[key] = value

        localStorage.setItem(
            REGISTER_STORAGE_KEY,
            JSON.stringify(this.config)
        )
    },

    handleEvents: function(){

        const _this = this
        // ẩn
        eyeSlash[0].onclick = function(){

            password.type = 'text'

            eyeSlash[0].parentElement.classList.add('hide')
            eye[0].parentElement.classList.remove('hide')
        }

        // hiện
        eye[0].onclick = function(){

            password.type = 'password'

            eye[0].parentElement.classList.add('hide')
            eyeSlash[0].parentElement.classList.remove('hide')
        }


        // ẩn confirm pass

        eyeSlash[1].onclick = function(){

            confirmPassword.type = 'text'

            eyeSlash[1].parentElement.classList.add('hide')
            eye[1].parentElement.classList.remove('hide')
        }

        // hiện confirm pass
        eye[1].onclick = function(){

            confirmPassword.type = 'password'

            eye[1].parentElement.classList.add('hide')
            eyeSlash[1].parentElement.classList.remove('hide')
        }

        username.oninput = function(){

            if(username.value.trim() !== ''){

                usernameGroup.classList.remove('error')
                errorUsername.textContent = ''
            }
        }

        password.oninput = function(){

            if(password.value.trim() !== ''){

                passwordGroup.classList.remove('error')
                errorPassword.textContent = ''
            }


            // Nếu password thay đổi
            // thì kiểm tra lại confirm password

            if(
                confirmPassword.value.trim() !== '' &&
                confirmPassword.value !== password.value
            ){

                confirmPasswordGroup.classList.add('error')

                errorConfirmPassword.textContent =
                    'Mật khẩu xác nhận không khớp'

            }else if(
                confirmPassword.value.trim() !== ''
            ){

                confirmPasswordGroup.classList.remove('error')

                errorConfirmPassword.textContent = ''
            }
        }        

        confirmPassword.oninput = function(){

            if(confirmPassword.value.trim() === ''){

                return
            }


            if(confirmPassword.value !== password.value){

                confirmPasswordGroup.classList.add('error')

                errorConfirmPassword.textContent =
                    'Mật khẩu xác nhận không khớp'

            }else{

                confirmPasswordGroup.classList.remove('error')

                errorConfirmPassword.textContent = ''
            }
        }
        //  thực hiện đăng ký

        form.onsubmit = function(e){

            e.preventDefault()


            const usernameValue = username.value.trim()
            const passwordValue = password.value.trim()
            const confirmPasswordValue =
                confirmPassword.value.trim()


            let isValid = true

            usernameGroup.classList.remove('error')
            passwordGroup.classList.remove('error')
            confirmPasswordGroup.classList.remove('error')

            errorUsername.textContent = ''
            errorPassword.textContent = ''
            errorConfirmPassword.textContent = ''

            if(usernameValue === ''){

                usernameGroup.classList.add('error')

                errorUsername.textContent =
                    'Vui lòng nhập đầy đủ'

                isValid = false
            }

            if(passwordValue === ''){

                passwordGroup.classList.add('error')

                errorPassword.textContent =
                    'Vui lòng nhập đầy đủ'

                isValid = false

            }else if(passwordValue.length < 6){

                passwordGroup.classList.add('error')

                errorPassword.textContent =
                    'Mật khẩu phải có ít nhất 6 ký tự'

                isValid = false
            }

            if(confirmPasswordValue === ''){

                confirmPasswordGroup.classList.add('error')

                errorConfirmPassword.textContent =
                    'Vui lòng nhập đầy đủ'

                isValid = false

            }else if(
                confirmPasswordValue !== passwordValue
            ){

                confirmPasswordGroup.classList.add('error')

                errorConfirmPassword.textContent =
                    'Mật khẩu xác nhận không khớp'

                isValid = false
            }

            if(!isValid){
                return
            }


            _this.setConfig(
                'username',
                usernameValue
            )


            alert('Đăng ký thành công!')


            // Chuyển về trang Login

            window.location.href = '../login.html'
        }
    },

    loadConfig: function(){

    },


    start: function(){

        this.loadConfig()

        this.handleEvents()
    }
}


app.start()