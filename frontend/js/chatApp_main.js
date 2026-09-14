const $ = document.querySelector.bind(document)
const $$ = document.querySelectorAll.bind(document)

const LOGIN_STORAGE_KEY = 'CHAT_WATCH_LOGIN'

const userName = $('#user_name')
const userAvt = $('#user_avt')
const profileName = $('#profile_name')

const logoutBtn = $('#logout')
const profileBtn = $('#profile')
const userPassword = $('#userPassword')

const logoutModal = $('#logoutModal')
const profileModal = $('#profileModal')
const passwordModal = $('#passwordModal')

const closeLogout = $('#close')
const cancelLogout = $('#cancelLogout')
const agreeLogout = $('#agree')

const closeProfile = $('#closeProfile')
const cancelProfile = $('#cancelProfile')
const saveProfile = $('#saveProfile')

const closePassword = $('#closePassword')
const cancelPassword = $('#cancelPassword')
const savePassword = $('#savePassword')

const avatarInput = $('#avatar_input')
const profileAvt = $('#profile_avt')

const currentPassword = $('#currentPassword')
const newPassword = $('#newPassword')
const confirmPassword = $('#confirmPassword')
const passwordErrors = $$('#passwordModal .error')

const chatApp = {
    config: JSON.parse(localStorage.getItem(LOGIN_STORAGE_KEY)) || {},

    setConfig: function (key, value) {
        this.config[key] = value

        localStorage.setItem(
            LOGIN_STORAGE_KEY,
            JSON.stringify(this.config)
        )
    },

    checkLogin: function () {
        if (!this.config.isLoggedIn || !this.config.user) {
            window.location.href = './login.html'
            return false
        }

        return true
    },

    loadUser: function () {
        if (this.config.isLoggedIn && this.config.user) {
            userName.textContent = this.config.user.username

            if (
                !this.config.user.avatar ||
                this.config.user.avatar === 'default_avt.png'
            ) {
                userAvt.src = './assests/img/default_avt.png'
            } else {
                userAvt.src =
                    `http://127.0.0.1:5000${this.config.user.avatar}`
            }
        }
    },

    openProfile: function () {
        profileName.value = this.config.user.username

        if (
            !this.config.user.avatar ||
            this.config.user.avatar === 'default_avt.png'
        ) {
            profileAvt.src = './assests/img/default_avt.png'
        } else {
            profileAvt.src =
                `http://127.0.0.1:5000${this.config.user.avatar}`
        }

        profileModal.classList.add('active')
    },

    closeProfile: function () {
        profileModal.classList.remove('active')
    },

    openLogout: function () {
        logoutModal.classList.add('active')
    },

    closeLogout: function () {
        logoutModal.classList.remove('active')
    },

    logout: function () {
        localStorage.removeItem(LOGIN_STORAGE_KEY)
        window.location.href = './login.html'
    },

    handleEvent: function () {

        // ==================== PROFILE ====================

        profileBtn.onclick = () => {
            this.openProfile()
        }

        closeProfile.onclick = () => {
            this.closeProfile()
        }

        cancelProfile.onclick = () => {
            this.closeProfile()
        }

        profileModal.onclick = (e) => {
            if (e.target === profileModal) {
                this.closeProfile()
            }
        }

        // ==================== PASSWORD ====================

        userPassword.onclick = () => {
            passwordModal.classList.add('active')
        }

        closePassword.onclick = () => {
            passwordModal.classList.remove('active')
        }

        cancelPassword.onclick = () => {
            passwordModal.classList.remove('active')
        }

        passwordModal.onclick = (e) => {
            if (e.target === passwordModal) {
                passwordModal.classList.remove('active')
            }
        }

        // ==================== LOGOUT ====================

        logoutBtn.onclick = () => {
            this.openLogout()
        }

        closeLogout.onclick = () => {
            this.closeLogout()
        }

        cancelLogout.onclick = () => {
            this.closeLogout()
        }

        agreeLogout.onclick = () => {
            this.logout()
        }

        logoutModal.onclick = (e) => {
            if (e.target === logoutModal) {
                this.closeLogout()
            }
        }

        // ==================== AVATAR ====================

        avatarInput.onchange = (e) => {
            const file = e.target.files[0]

            if (file) {
                profileAvt.src = URL.createObjectURL(file)
            }
        }

        // ==================== SAVE PROFILE ====================

        saveProfile.onclick = async () => {
            const newUsername = profileName.value.trim()
            const oldUsername = this.config.user.username
            const avatarFile = avatarInput.files[0]

            if (newUsername === '') {
                alert('Tên người dùng không được để trống')
                return
            }

            const usernameChanged = newUsername !== oldUsername
            const avatarChanged = !!avatarFile

            if (!usernameChanged && !avatarChanged) {
                profileModal.classList.remove('active')
                return
            }

            try {
                // Cập nhật username
                if (usernameChanged) {
                    const response = await fetch(
                        'http://127.0.0.1:5000/api/update-profile',
                        {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                userid: this.config.user.userid,
                                username: newUsername
                            })
                        }
                    )

                    const result = await response.json()

                    if (!result.success) {
                        alert(result.message)
                        return
                    }

                    this.config.user.username = result.username
                    userName.textContent = result.username
                }

                // Cập nhật avatar
                if (avatarChanged) {
                    const formData = new FormData()

                    formData.append(
                        'userid',
                        this.config.user.userid
                    )

                    formData.append(
                        'avatar',
                        avatarFile
                    )

                    const response = await fetch(
                        'http://127.0.0.1:5000/api/update-avatar',
                        {
                            method: 'POST',
                            body: formData
                        }
                    )

                    const result = await response.json()

                    if (!result.success) {
                        alert(result.message)
                        return
                    }

                    this.config.user.avatar = result.avatar

                    userAvt.src =
                        `http://127.0.0.1:5000${result.avatar}`

                    profileAvt.src =
                        `http://127.0.0.1:5000${result.avatar}`
                }

                this.setConfig(
                    'user',
                    this.config.user
                )

                profileModal.classList.remove('active')

                alert('Cập nhật thông tin thành công')

            } catch (error) {
                console.error(error)
                alert('Không thể kết nối đến máy chủ')
            }
        }
    },

    start: function () {
        if (!this.checkLogin()) {
            return
        }

        this.loadUser()
        this.handleEvent()
    }
}

chatApp.start()