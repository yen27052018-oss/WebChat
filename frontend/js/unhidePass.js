

const inputForm = $$('.form_input')
const passwords = $$('.password')
const eyeSlashes = $$('.input_icon.unhide_password')
const eyes = $$('.input_icon.hide_password')

passwords.forEach((password, i) => {
    const eyeSlash = eyeSlashes[i];
    const eye = eyes[i];
    eyeSlash.onclick = function () {
        password.type = 'text'
        eyeSlash.classList.add('hide')
        eye.classList.remove('hide')
    };
    eye.onclick = function () {
        password.type = 'password'
        eye.classList.add('hide')
        eyeSlash.classList.remove('hide')
    };
});