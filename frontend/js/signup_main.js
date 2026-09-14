const $ = document.querySelector.bind(document)
const $$ = document.querySelectorAll.bind(document)

const form = $('.form')

const username = $('#username')
const password = $('#password')
const confirmPassword = $('#confirm-password')

const usernameGroup = username.closest('.form_group')
const passwordGroup = password.closest('.form_group')
const confirmPasswordGroup = confirmPassword.closest('.form_group')

const errorUsername = usernameGroup.querySelector('.error')
const errorPassword = passwordGroup.querySelector('.error')
const errorConfirmPassword = confirmPasswordGroup.querySelector('.error')

const eyeSlash = $$('.input_icon.unhide_password')
const eye = $$('.input_icon.hide_password')


// APP
const app = {

    handleEvents: function(){
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

        form.onsubmit = async function(e){

            e.preventDefault()

            const usernameValue = username.value.trim()
            const passwordValue = password.value.trim()
            const confirmPasswordValue = confirmPassword.value.trim()
            console.log(usernameValue, passwordValue, confirmPasswordValue)

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

            }else if(confirmPasswordValue !== passwordValue){

                confirmPasswordGroup.classList.add('error')

                errorConfirmPassword.textContent =
                    'Mật khẩu xác nhận không khớp'

                isValid = false
            }

            if(!isValid){
                return
            }

            try{

                const response = await fetch(
                    'http://127.0.0.1:5000/api/register',
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            username: usernameValue,
                            password: passwordValue
                        })
                    }
                )

                const result = await response.json()

                if(!result.success){

                    usernameGroup.classList.add('error')

                    errorUsername.textContent =
                        result.message

                    return
                }

                alert(
                    `Đăng ký thành công!\nMã người dùng: ${result.user_code}`
                )

                window.location.href = './login.html'

            }catch(error){

                console.error(error)

                alert('Không thể kết nối đến máy chủ')
            }
        }
    },

    start: function(){


        this.handleEvents()
    }
}


app.start()